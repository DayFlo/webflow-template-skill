"""Shared path helpers for the webflow-template script tests."""
import os
import sys

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.dirname(TESTS_DIR)
SKILL_DIR = os.path.dirname(SCRIPTS_DIR)
FIXTURES = os.path.join(TESTS_DIR, "fixtures")
ASSETS = os.path.join(SKILL_DIR, "assets")
REFERENCES = os.path.join(SKILL_DIR, "references")

if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)


def fixture(*parts: str) -> str:
    return os.path.join(FIXTURES, *parts)


def script(name: str) -> str:
    return os.path.join(SCRIPTS_DIR, name)
