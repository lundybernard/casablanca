"""Integration tests for the lib public API.

Pattern stub: ``lib`` holds only ``hello_world`` today; real value
arrives with ``lib.listen`` (see .todo/listen-command-plan.md).
"""

from unittest import TestCase

from casablanca.lib import hello_world


class LibTests(TestCase):
    def test_hello_world(t) -> None:
        t.assertEqual(hello_world(), 'Hello World!')
