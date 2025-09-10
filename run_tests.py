"""Runner to execute test scripts from project root.

Usage:
    python run_tests.py
"""
from scripts import test_api


if __name__ == '__main__':
    test_api.run()
