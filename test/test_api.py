import mock
import pytest
import requests

from pyepm import deploy, config
config = config.get_default_config()

from pyepm import api  # NOQA

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
    instance = api.Api(config)
    mocker.patch('requests.post', return_value=mock_json_response(error={'code': 31337, 'message': 'Too Elite'}))
    with pytest.raises(api.ApiException) as excinfo:
        instance.coinbase()
    assert excinfo.value.code == 31337
    assert excinfo.value.message == 'Too Elite'

def test_api_exception_status_code(mocker):
    instance = api.Api(config)
    mocker.patch('requests.post', return_value=mock_json_response(status_code=404))
    with pytest.raises(api.ApiException) as excinfo:
        instance.coinbase()
    assert excinfo.value.code == 404
    assert excinfo.value.message == 'Error Reason'

def mock_rpc(mocker, rpc_fun, rpc_args, json_result, rpc_method, rpc_params):
    instance = api.Api(config)

    mocker.patch('requests.post', return_value=mock_json_response(result=json_result))
    mock_rpc_post = mocker.patch.object(instance, '_rpc_post', side_effect=instance._rpc_post)

    result = getattr(instance, rpc_fun)(*rpc_args)
    mock_rpc_post.assert_called_with(rpc_method, rpc_params)
    return result

def test_accounts(mocker):
    accounts = ['0x7adf3b3bce3a5c8c17e8b243f4c331dd97c60579']
    assert mock_rpc(mocker, 'accounts', [], json_result=accounts,
                    rpc_method='eth_accounts', rpc_params=None) == accounts

def test_balance_at_zero(mocker):
    address = '0x7adf3b3bce3a5c8c17e8b243f4c331dd97c60579'
    balance = '0x'
    assert mock_rpc(mocker, 'balance_at', [address], json_result=balance,
                    rpc_method='eth_balanceAt', rpc_params=[address]) == 0

def test_balance_at_non_zero(mocker):
    address = '0x7adf3b3bce3a5c8c17e8b243f4c331dd97c60579'
    balance = '0x01495010e21ff5d000'
    assert mock_rpc(mocker, 'balance_at', [address], json_result=balance,
                    rpc_method='eth_balanceAt', rpc_params=[address]) == 23729485000000000000

def test_block(mocker):
    nr = 1711
    block = {
        'nonce': '0x0bacf24ff9c36870be684a1e8b8f875864c6ea69248373db87266199e6a2ca16',
        'transactionsRoot': '0x56e81f171bcc55a6ff8345e692c0f86e5b48e01b996cadc001622fb5e363b421',
        'hash': '806eee83f9aaa349031bd0dccd50241cc898c65cd36b8fa53aaaee3638d27488',
        'sha3Uncles': '0x1dcc4de8dec75d7aab85b567b6ccd41ad312451b948a7413f0a142fd40d49347',
        'miner': '0xba5a55dec63ca9b4f8108dec82b9d734320c7057',
        'parentHash': '0xc4781fe71e48632aba0dc95b24a23eef638e961ecb54e8a236c4c561b75298b6',
        'extraData': '0x0000000000000000000000000000000000000000000000000000000000000000',
        'gasLimit': 187806,
        'number': 1711,
        'stateRoot': '0xfdc5440b69a0361051d319d5c463ce45bcd03bc8622fbe2a5739b6a469f5da50',
        'difficulty': '0x022eec',
        'timestamp': 1423664646}
    assert mock_rpc(mocker, 'block', [nr], json_result=block,
                    rpc_method='eth_blockByNumber', rpc_params=[nr]) == block

def test_coinbase(mocker):
    coinbase = '0x7adf3b3bce3a5c8c17e8b243f4c331dd97c60579'
    assert mock_rpc(mocker, 'coinbase', [], json_result=coinbase,
                    rpc_method='eth_coinbase', rpc_params=None) == coinbase

def test_create(mocker):
    code = '0xdeadbeef'
    address = '0x6489ecbe173ac43dadb9f4f098c3e663e8438dd7'
    rpc_params = [{'gas': '10000',
                   'code': '0xdeadbeef',
                   'from': 'cd2a3d9f938e13cd947ec05abc7fe734df8dd826',
                   'value': '0',
                   'gasPrice': '10000000000000'}]
    assert mock_rpc(mocker, 'create', [code], json_result=address,
                    rpc_method='eth_transact', rpc_params=rpc_params) == address

def test_is_contract_at_contract_exists(mocker):
    address = '0x6489ecbe173ac43dadb9f4f098c3e663e8438dd7'
    code = '0xdeadbeef'
    assert mock_rpc(mocker, 'is_contract_at', [address], json_result=code,
                    rpc_method='eth_codeAt', rpc_params=[address])

def test_is_contract_at_contract_doesnt_exists(mocker):
    address = '0x6489ecbe173ac43dadb9f4f098c3e663e8438dd7'
    code = '0x0000000000000000000000000000000000000000000000000000000000000000'
    assert not mock_rpc(mocker, 'is_contract_at', [address], json_result=code,
                        rpc_method='eth_codeAt', rpc_params=[address])

def test_create_solidity(mocker):
    contract = 'test/fixtures/config.sol'
    deployment = deploy.Deploy(contract, config)
    contracts = deployment.compile_solidity(contract, ['Config', 'mortal', 'owned'])

    address = '0x6489ecbe173ac43dadb9f4f098c3e663e8438dd7'
    for contract_name, code in contracts:
        rpc_params = [{'gas': '10000',
                       'code': code,
                       'from': 'cd2a3d9f938e13cd947ec05abc7fe734df8dd826',
                       'value': '0',
                       'gasPrice': '10000000000000'}]
        assert mock_rpc(mocker, 'create', [code], json_result=address,
                        rpc_method='eth_transact', rpc_params=rpc_params) == address

def test_is_solidity_contract_at_contract_exists(mocker):
    address = '0x6489ecbe173ac43dadb9f4f098c3e663e8438dd7'
    code = '0xdeadbeef'
    assert mock_rpc(mocker, 'is_contract_at', [address], json_result=code,
                    rpc_method='eth_codeAt', rpc_params=[address])

def test_is_solidity_contract_at_contract_doesnt_exists(mocker):
    address = '0x6489ecbe173ac43dadb9f4f098c3e663e8438dd7'
    code = '0x0000000000000000000000000000000000000000000000000000000000000000'
    assert not mock_rpc(mocker, 'is_contract_at', [address], json_result=code,
                        rpc_method='eth_codeAt', rpc_params=[address])

def test_is_listening(mocker):
    assert mock_rpc(mocker, 'is_listening', [], json_result=True,
                    rpc_method='eth_listening', rpc_params=None)

def test_is_mining(mocker):
    assert mock_rpc(mocker, 'is_mining', [], json_result=True,
                    rpc_method='eth_mining', rpc_params=None)

def test_number(mocker):
    assert mock_rpc(mocker, 'number', [], json_result=42,
                    rpc_method='eth_number', rpc_params=None) == 42

def test_peer_count(mocker):
    assert mock_rpc(mocker, 'peer_count', [], json_result=8,
                    rpc_method='eth_peerCount', rpc_params=None) == 8

def test_state_at(mocker):
    address = "0x407d73d8a49eeb85d32cf465507dd71d507100c1"
    idx = 1
    assert mock_rpc(mocker, 'state_at', [address, idx], json_result='0x03',
                    rpc_method='eth_stateAt', rpc_params=[address, idx]) == '0x03'

def test_storage_at(mocker):
    address = "0x407d73d8a49eeb85d32cf465507dd71d507100c1"
    assert mock_rpc(mocker, 'storage_at', [address], json_result={'0x': '0x03'},
                    rpc_method='eth_storageAt', rpc_params=[address]) == {'0x': '0x03'}

def test_transact(mocker):
    address = '0x6489ecbe173ac43dadb9f4f098c3e663e8438dd7'
    rpc_params = [{'gas': '10000',
                   'to': address,
                   'data': None,
                   'value': '0',
                   'gasPrice': '10000000000000'}]
    assert mock_rpc(mocker, 'transact', [address], json_result=None,
                    rpc_method='eth_transact', rpc_params=rpc_params) is None

def test_call_multiply(mocker):
    address = '0x6489ecbe173ac43dadb9f4f098c3e663e8438dd7'
    fun_name = 'multiply'
    sig = 'i'
    data = [3]
    data_abi = '0x1df4f1440000000000000000000000000000000000000000000000000000000000000003'
    json_result = '0x0000000000000000000000000000000000000000000000000000000000000015'
    rpc_params = [{'gas': '10000',
                   'to': address,
                   'data': data_abi,
                   'gasPrice': '10000000000000'}]
    assert mock_rpc(mocker, 'call', [address, fun_name, sig, data], json_result=json_result,
                    rpc_method='eth_call', rpc_params=rpc_params) == [21]

def test_call_returning_array(mocker):
    address = '0x7b089cfe50c1a5fe5b0da352348a43bba81addd4'
    fun_name = 'get_stats'
    sig = ''
    data = []
    data_abi = '0x61837e41'
    json_result = '0x0000000000000000000000000000000000000000000000000000000000000003' +\
                  '0000000000000000000000000000000000000000000000000000000000000002' +\
                  '0000000000000000000000000000000000000000000000000000000000000001' +\
                  '0000000000000000000000000000000000000000000000000000000000000000'
    rpc_params = [{'gas': '10000',
                   'to': address,
                   'data': data_abi,
                   'gasPrice': '10000000000000'}]
    assert mock_rpc(mocker, 'call', [address, fun_name, sig, data], json_result=json_result,
                    rpc_method='eth_call', rpc_params=rpc_params) == [3, 2, 1, 0]  # with length prefix of 3
