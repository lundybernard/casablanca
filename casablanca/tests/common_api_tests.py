import requests

PT_SVC_ADDR = 'http://0.0.0.0:5000/'


class CommonAPITest(object):
    '''Define the API tests in their own inheritable class
    so they may be reused in multiple test cases.
    This was done to allow testing of the api in a container
    and as local service.
    '''

    def test_api_hello_world(self):
        print('test_api_hello_world')
        url = f'{self.service_address}hello_world'
        print(f'connect to service at {url}')
        out = requests.get(url, verify=False)
        self.assertEqual(out.text, '"Hello World!"\n')
