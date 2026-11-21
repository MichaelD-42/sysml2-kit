"""HTTP API over the loaded graph: `python -m explorer.server <project-dir>`."""

import json
import os
import subprocess
import sys
import threading
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from neo4j import GraphDatabase
from pydantic import BaseModel

from explorer import agent, cypher, load, search, views
from explorer.search import Embedder

STATIC = Path(__file__).resolve().parent.parent / "static"


class CypherBody(BaseModel):
    query: str
    params: dict | None = None


class AskBody(BaseModel):
    question: str


def error(status, message):
    return JSONResponse({"error": message}, status_code=status)


def create_app(driver, embedder, project: Path, agent_factory=None) -> FastAPI:
    app = FastAPI()
    app.state.reload_lock = threading.Lock()
    needs_path = project / "build" / "needs" / "needs.json"
    if agent_factory is None:
        agent_options = agent.options(project, driver, embedder)

        def agent_factory(question):
            return agent.ask(agent_options, question)

    @app.exception_handler(ValueError)
    def bad_value(request, e):
        return error(400, str(e))

    @app.exception_handler(KeyError)
    def not_found(request, e):
        return error(404, str(e.args[0]) if e.args else "not found")

    @app.exception_handler(cypher.CypherError)
    def bad_cypher(request, e):
        return error(400, str(e))

    @app.get("/api/tree")
    def tree():
        return views.tree(driver)

    @app.get("/api/keys")
    def keys():
        records, _, _ = driver.execute_query(
            "MATCH (n:Node) RETURN n.key AS key ORDER BY key", routing_="r"
        )
        return [r["key"] for r in records]

    @app.get("/api/element/{key}")
    def element(key: str):
        found = search.neighbourhood(driver, key)
        if not found:
            raise KeyError(key)
        return found

    @app.get("/api/view/{kind}")
    def view(kind: str, focus: str | None = None):
        return views.view(driver, kind, focus, needs_path)

    @app.get("/api/search")
    def find(q: str, k: int = 10):
        return search.search(driver, embedder, q, k)

    @app.get("/api/cypher/examples")
    def examples():
        return cypher.EXAMPLES

    @app.post("/api/cypher")
    def run(body: CypherBody):
        return cypher.run_read(driver, body.query, body.params)

    @app.post("/api/ask")
    async def ask(body: AskBody):
        async def events():
            async for event in agent_factory(body.question):
                yield f"data: {json.dumps(event)}\n\n"

        return StreamingResponse(events(), media_type="text/event-stream")

    @app.post("/api/reload")
    def reload():
        if not app.state.reload_lock.acquire(blocking=False):
            return error(409, "a reload is already running")
        try:
            made = subprocess.run(
                ["make", "-C", str(project), "docs", "STRICT="],
                check=False,
                capture_output=True,
                text=True,
            )
            if made.returncode:
                tail = (made.stdout + made.stderr).splitlines()[-40:]
                return error(422, "\n".join(tail))
            try:
                nodes, edges = load.load(project, driver, embedder)
            except Exception as e:  # noqa: BLE001 - any load failure is reported, not raised
                return error(500, str(e))
            return {"nodes": nodes, "edges": edges}
        finally:
            app.state.reload_lock.release()

    # last, so /api routes win
    app.mount("/", StaticFiles(directory=STATIC, html=True, check_dir=False))
    return app


def main(argv=None):
    import uvicorn

    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        sys.exit("usage: python -m explorer.server <project-dir>")
    driver = GraphDatabase.driver(
        os.environ.get("NEO4J_URI", "bolt://localhost:7687"),
        auth=None
        if os.environ.get("NEO4J_AUTH") == "none"
        else (os.environ.get("NEO4J_USER", "neo4j"), os.environ["NEO4J_PASSWORD"]),
    )
    app = create_app(driver, Embedder(), Path(argv[0]).resolve())
    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
