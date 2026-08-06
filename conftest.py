"""Pytest bootstrap for test environment isolation."""

import os

# Must be set before app imports so tests always use testing config.
os.environ["FLASK_CONFIG"] = "testing"
os.environ["FLASK_ENV"] = "testing"