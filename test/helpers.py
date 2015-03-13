from distutils import spawn
import mock
import pytest
import requests

from pyepm import config as c

config = c.get_default_config()

has_solc = spawn.find_executable("solc")

solc = pytest.mark.skipif(not has_solc, reason="solc compiler not found")

COW_ADDRESS = '0xcd2a3d9f938e13cd947ec05abc7fe734df8dd826'

def is_hex(s):
    try:
        int(s, 16)
        return True
    except ValueError:
        return False

def mock_json_response(status_code=200, error=None, result=None):
    m = mock.MagicMock(spec=requests.Response)
    m.status_code = status_code
    base_json_response = {u'jsonrpc': u'2.0', u'id': u'c7c427a5-b6e9-4dbf-b218-a6f9d4f09246'}
    json_response = dict(base_json_response)
    if result:
        json_response[u'result'] = result
    elif error:
        json_response[u'error'] = error
    if status_code >= 400:
        m.reason = 'Error Reason'
    m.json.return_value = json_response
    return m
