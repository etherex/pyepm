from pyepm import api

import pytest
import requests
import mock

base_json_response = {u'jsonrpc': u'2.0', u'id': u'c7c427a5-b6e9-4dbf-b218-a6f9d4f09246'}

def mock_json_response(status_code=200, error=None, result=None):
    m = mock.MagicMock(spec=requests.Response)
    m.status_code = status_code
    json_response = dict(base_json_response)
    if result:
        json_response[u'result'] = result
    elif error:
        json_response[u'error'] = error
    if status_code >= 400:
        m.reason = 'Error Reason'
    m.json.return_value = json_response
    return m

def test_api_exception_error_response(mocker):
    mocker.patch('requests.post', return_value=mock_json_response(error={'code': 31337, 'message': 'Too Elite'}))
    instance = api.Api()
    with pytest.raises(api.ApiException) as excinfo:
        instance.coinbase()
    assert excinfo.value.code == 31337
    assert excinfo.value.message == 'Too Elite'

def test_api_exception_status_code(mocker):
    mocker.patch('requests.post', return_value=mock_json_response(status_code=404))
    instance = api.Api()
    with pytest.raises(api.ApiException) as excinfo:
        instance.coinbase()
    assert excinfo.value.code == 404
    assert excinfo.value.message == 'Error Reason'

def test_coinbase(mocker):
    coinbase = '0x7adf3b3bce3a5c8c17e8b243f4c331dd97c60579'
    mocker.patch('requests.post', return_value=mock_json_response(result=coinbase))
    instance = api.Api()
    assert instance.coinbase() == coinbase
