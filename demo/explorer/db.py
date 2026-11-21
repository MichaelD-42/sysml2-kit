"""The model graph: an in-memory Relate database, driven from one thread because it is thread-affine."""

import contextlib
from concurrent.futures import ThreadPoolExecutor

import relate


class ReadOnlyError(Exception):
    pass


class Graph:
    def __init__(self):
        self._pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="relate")
        self._db = self._run(relate.Database)

    def _run(self, fn, *args):
        return self._pool.submit(fn, *args).result()

    def query(self, cypher: str, **params) -> list[dict]:
        return self._run(lambda: self._db.execute(cypher, params).data)

    def write(self, statements) -> None:
        """Run `statements(run)` in one transaction; `run(cypher, params)` issues one statement."""

        def work():
            self._db.begin_transaction()
            try:
                statements(
                    lambda cypher, params=None: self._db.execute(cypher, params or {})
                )
                self._db.commit_transaction()
            except BaseException:
                # a failing rollback must not mask the original error
                with contextlib.suppress(Exception):
                    self._db.rollback_transaction()
                raise

        self._run(work)

    def read_only(
        self, cypher: str, params: dict | None, limit: int, timeout_s: float
    ) -> dict:
        """One query that cannot change the graph: `{columns, rows, truncated}`, rows as JSON values."""
        # shortcut: Relate 1.2.0 has no query timeout, so timeout_s is not enforced and a runaway
        # read blocks the worker; enforce it when Relate gains one
        params = params or {}

        def work():
            # the planner's query_type is "r" only for reads; "w", "rw" and "s" (schema) are refused
            kind = self._db.execute("EXPLAIN " + cypher, params).query_type
            if kind != "r":
                raise ReadOnlyError(
                    f"only read queries are allowed (query type {kind!r})"
                )
            # backstop: run in a transaction that is never committed
            self._db.begin_transaction()
            try:
                result = self._db.execute(cypher, params)
                keys = {}

                def key(node_id):
                    if node_id not in keys:
                        found = self._db.execute(
                            "MATCH (n) WHERE id(n) = $id RETURN n.key AS k",
                            {"id": node_id},
                        ).data
                        keys[node_id] = found[0]["k"] if found else node_id
                    return keys[node_id]

                def plain(v):
                    if isinstance(v, relate.Node):
                        # the 384-float search vector would swamp every row
                        props = v.properties.items()
                        return {k: plain(x) for k, x in props if k != "embedding"}
                    if isinstance(v, relate.Relationship):
                        return {"type": v.type, "src": key(v.start), "dst": key(v.end)}
                    if isinstance(v, relate.Path):
                        return {
                            "nodes": [plain(n) for n in v.nodes],
                            "relationships": [plain(r) for r in v.relationships],
                        }
                    if isinstance(v, (list, tuple)):
                        return [plain(x) for x in v]
                    if isinstance(v, dict):
                        return {k: plain(x) for k, x in v.items()}
                    return v

                rows = [
                    [plain(r[c]) for c in result.columns] for r in result.data[:limit]
                ]
                return {
                    "columns": result.columns,
                    "rows": rows,
                    "truncated": len(result.data) > limit,
                }
            finally:
                self._db.rollback_transaction()

        return self._run(work)

    def close(self) -> None:
        if self._pool is None:
            return
        self._run(self._db.close)
        self._pool.shutdown()
        self._pool = None
