"""The model graph: an in-memory Relate database, driven from one thread because it is thread-affine."""

from concurrent.futures import ThreadPoolExecutor

import relate


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
            except BaseException:
                self._db.rollback_transaction()
                raise
            self._db.commit_transaction()

        self._run(work)

    def read_only(
        self, cypher: str, params: dict | None, limit: int, timeout_s: float
    ) -> dict:
        raise NotImplementedError("read-only Cypher is not implemented yet")

    def close(self) -> None:
        self._run(self._db.close)
        self._pool.shutdown()
