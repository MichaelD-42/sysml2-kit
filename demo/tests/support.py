"""Shared test helpers: a Neo4j driver or a skip, and loading a kit project into it."""

import os
from pathlib import Path

from neo4j import GraphDatabase
from neo4j.exceptions import AuthError, ServiceUnavailable

from explorer import load


def driver_or_skip(testcase):
    uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    password = os.environ.get("NEO4J_PASSWORD")
    if not password:
        testcase.skipTest(f"Neo4j not reachable at {uri}")
    driver = GraphDatabase.driver(
        uri, auth=(os.environ.get("NEO4J_USER", "neo4j"), password)
    )
    try:
        driver.verify_connectivity()
    except (AuthError, ServiceUnavailable, OSError):
        driver.close()
        testcase.skipTest(f"Neo4j not reachable at {uri}")
    testcase.addCleanup(driver.close)
    return driver


def load_project(driver, project: Path):
    graph = load.read_project(project)
    load.write(graph, driver)
    return graph
