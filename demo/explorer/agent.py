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

from explorer import cypher as cypher_mod
from explorer import search

PROMPT = Path(__file__).with_name("prompt.md")
SYSML_TOOLS = ("outline", "find", "relations", "check")
# intended: allowed_tools auto-approves the read-only tools, can_use_tool denies everything else
warnings.filterwarnings("ignore", category=CanUseToolShadowedWarning)


def dumps(value) -> str:
    return json.dumps(value, default=str)


def semantic_search(driver, embedder, q, k=8) -> str:
    try:
        return dumps(search.search(driver, embedder, q, k))
    except Exception as e:  # noqa: BLE001 - tool errors go back to the agent as text
        return dumps({"error": str(e)})


def cypher(driver, query) -> str:
    try:
        return dumps(cypher_mod.run_read(driver, query, limit=100))
    except Exception as e:  # noqa: BLE001
        return dumps({"error": str(e)})


def element(driver, key) -> str:
    try:
        return dumps(
            search.neighbourhood(driver, key) or {"error": f"no element {key}"}
        )
    except Exception as e:  # noqa: BLE001
        return dumps({"error": str(e)})


def model_root(project: Path) -> Path:
    """Where `sysml mcp` sees the project's model and, through `platform`, the platform's."""
    # the platform's model sits behind the `platform` symlink, which `sysml mcp --project` does
    # not follow; their common directory holds both (its two `Trace` packages merge, no collision)
    # shortcut: the common directory can hold other models too, fine for the examples layout
    model = project.resolve() / "model"
    platform = (project / "platform" / "model").resolve()
    return Path(os.path.commonpath([model, platform])) if platform.is_dir() else model


async def can_use_tool(name, input, context):
    if name.startswith(("mcp__kit__", "mcp__sysml__")):
        return PermissionResultAllow()
    return PermissionResultDeny(
        message=f"{name} is not available: the agent is read-only"
    )


def options(project: Path, driver, embedder) -> ClaudeAgentOptions:
    def text(s):
        return {"content": [{"type": "text", "text": s}]}

    @tool(
        "semantic_search",
        "Hybrid semantic and full-text search over elements and needs",
        {"q": str},
    )
    async def semantic_search_tool(args):
        return text(
            await asyncio.to_thread(semantic_search, driver, embedder, args["q"])
        )

    @tool(
        "cypher",
        "Run one read-only Cypher query against the model graph (100 rows max)",
        {"query": str},
    )
    async def cypher_tool(args):
        return text(await asyncio.to_thread(cypher, driver, args["query"]))

    @tool(
        "element",
        "One element or need by key, with its properties and direct edges",
        {"key": str},
    )
    async def element_tool(args):
        return text(await asyncio.to_thread(element, driver, args["key"]))

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
        allowed_tools=[
            "mcp__kit__semantic_search",
            "mcp__kit__cypher",
            "mcp__kit__element",
            *(f"mcp__sysml__{t}" for t in SYSML_TOOLS),
        ],
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
    except Exception as e:  # noqa: BLE001 - the page gets the failure as an event
        yield {"type": "error", "message": str(e)}
