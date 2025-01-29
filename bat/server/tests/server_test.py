from unittest import TestCase
from unittest.mock import patch

from ..server import (
    app,
    start_server,
    start_api_server,
)


SRC = 'bat.server.server'


class TestFlaskApp(TestCase):

    def test_get_root(t):
        client = app.test_client()

        res = client.get('/')
        t.assertEqual(res.status_code, 200)
        t.assertEqual(
            res.get_data(as_text=True),
            'Hello World!'
        )


class TestServer(TestCase):

    @patch(f'{SRC}.app', autospec=True)
    def test_start_server(t, app):
        start_server()
        app.run.assert_called_with(host='0.0.0.0', port='5000', debug=True)

    @patch(f'{SRC}.connexion')
    def test_start_api_server(t, connexion):
        start_api_server()
        connexion.FlaskApp.assert_called_with(
            'bat.server.server', specification_dir='../api/'
        )
        app = connexion.FlaskApp.return_value
        app.run.assert_called_with(host='0.0.0.0', port='5000', debug=True)
