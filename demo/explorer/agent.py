"""The read-only Claude agent: graph tools in process, the `sysml` MCP server over stdio."""

import asyncio
import json
import os
import shutil
import warnings
from pathlib import Path

from claude_agent_sdk import (
    AssistantMessage,
    CanUseToolShadowedWarning,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    PermissionResultAllow,
    PermissionResultDeny,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    create_sdk_mcp_server,
    tool,
)

from explorer import search

PROMPT = Path(__file__).with_name("prompt.md")
ALLOWED = (
    "mcp__kit__semantic_search",
    "mcp__kit__cypher",
    "mcp__kit__element",
    "mcp__sysml__outline",
    "mcp__sysml__find",
    "mcp__sysml__relations",
    "mcp__sysml__check",
)
# intended: allowed_tools auto-approves the read-only tools, can_use_tool denies everything else
warnings.filterwarnings("ignore", category=CanUseToolShadowedWarning)


def dumps(value) -> str:
    return json.dumps(value, default=str)


def semantic_search(graph, embedder, q, k=8) -> str:
    try:
        return dumps(search.search(graph, embedder, q, k))
    except Exception as e:  # noqa: BLE001 - tool errors go back to the agent as text
        return dumps({"error": str(e)})


def cypher(graph, query) -> str:
    try:
        return dumps(graph.read_only(query, None, 100, 10))
    except Exception as e:  # noqa: BLE001
        return dumps({"error": str(e)})


def element(graph, key) -> str:
    try:
        return dumps(search.neighbourhood(graph, key) or {"error": f"no element {key}"})
    except Exception as e:  # noqa: BLE001
        return dumps({"error": str(e)})


def model_root(project: Path) -> Path:
    """Where `sysml mcp` sees the project's model and, through `platform`, the platform's."""
    # the platform's model sits behind the `platform` symlink, which `sysml mcp --project` does
    # not follow; their common directory holds both (its two `Trace` packages merge, no collision)
    # shortcut: the common directory can hold other models too, so it is used only when it is the
    # project or its parent (the examples layout); otherwise the platform stays unresolved
    project = project.resolve()
    model = project / "model"
    platform = (project / "platform" / "model").resolve()
    if not platform.is_dir():
        return model
    common = Path(os.path.commonpath([model, platform]))
    return common if common in (project, project.parent) else model


async def can_use_tool(name, input, context):
    if name in ALLOWED:
        return PermissionResultAllow()
    return PermissionResultDeny(
        message=f"{name} is not available: the agent is read-only"
    )


def options(project: Path, graph, embedder) -> ClaudeAgentOptions:
    def text(s):
        return {"content": [{"type": "text", "text": s}]}

    @tool(
        "semantic_search",
        "Hybrid semantic and full-text search over elements and needs",
        {"q": str},
    )
    async def semantic_search_tool(args):
        return text(
            await asyncio.to_thread(semantic_search, graph, embedder, args["q"])
        )

    @tool(
        "cypher",
        "Run one read-only Cypher query against the model graph (100 rows max)",
        {"query": str},
    )
    async def cypher_tool(args):
        return text(await asyncio.to_thread(cypher, graph, args["query"]))

    @tool(
        "element",
        "One element or need by key, with its properties and direct edges",
        {"key": str},
    )
    async def element_tool(args):
        return text(await asyncio.to_thread(element, graph, args["key"]))

    kit = create_sdk_mcp_server(
        "kit", tools=[semantic_search_tool, cypher_tool, element_tool]
    )
    sysml = {
        "type": "stdio",
        "command": shutil.which("sysml") or "sysml",
        "args": ["mcp", "--project", str(model_root(project)), "--color", "never"],
    }
    return ClaudeAgentOptions(
        system_prompt=PROMPT.read_text(),
        mcp_servers={"kit": kit, "sysml": sysml},
        strict_mcp_config=True,
        tools=[],  # no built-in tools at all: no file, shell or web access
        setting_sources=[],  # no user or project settings whose allow rules could widen this
        allowed_tools=list(ALLOWED),
        can_use_tool=can_use_tool,
        max_turns=12,
    )


async def ask(options, question: str, client=ClaudeSDKClient):
    try:
        async with client(options) as session:
            await session.query(question)
            async for message in session.receive_response():
                if isinstance(message, AssistantMessage):
                    for block in message.content:
                        if isinstance(block, TextBlock):
                            yield {"type": "text", "text": block.text}
                        elif isinstance(block, ToolUseBlock):
                            yield {
                                "type": "tool",
                                "name": block.name,
                                "summary": dumps(block.input)[:120],
                            }
                elif isinstance(message, ResultMessage):
                    if message.is_error:
                        yield {
                            "type": "error",
                            "message": message.result or message.subtype,
                        }
                    else:
                        yield {"type": "done"}
                    return
        yield {"type": "error", "message": "the agent stopped without a result"}
    except Exception as e:  # noqa: BLE001 - the page gets the failure as an event
        yield {"type": "error", "message": str(e)}
