from unittest import TestCase

from casablanca.lib import hello_world


class LibTests(TestCase):
    def test_hello_world(t):
        ret = hello_world()
        t.assertEqual(ret, 'Hello World!')
