"""Shared test helpers: a Neo4j driver or a skip, and loading a kit project into it."""

import os
from pathlib import Path

from neo4j import GraphDatabase
from neo4j.exceptions import AuthError, ServiceUnavailable

from explorer import load
from explorer.search import Embedder


def driver_or_skip(testcase):
    uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    password = os.environ.get("NEO4J_PASSWORD")
    no_auth = os.environ.get("NEO4J_AUTH") == "none"
    if not (password or no_auth):
        testcase.skipTest(f"Neo4j not reachable at {uri}")
    driver = GraphDatabase.driver(
        uri, auth=None if no_auth else (os.environ.get("NEO4J_USER", "neo4j"), password)
    )
    try:
        driver.verify_connectivity()
    except (AuthError, ServiceUnavailable, OSError):
        driver.close()
        testcase.skipTest(f"Neo4j not reachable at {uri}")
    testcase.addCleanup(driver.close)
    return driver


_embedder = None


def load_project(driver, project: Path):
    global _embedder
    _embedder = _embedder or Embedder()  # loading the model is slow: once per run
    return load.load(project, driver, _embedder)
