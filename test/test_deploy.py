import pytest

from pyepm import deploy

from helpers import config, has_solc, is_hex, mock_json_response, solc

def test_load_yaml():
    deployment = deploy.Deploy('test/fixtures/example.yaml', config)
    result = deployment.load_yaml()
    assert result == [
        {
            'set': {
                'NameReg': '0x72ba7d8e73fe8eb666ea66babc8116a41bfb10e2'
            }
        },
        {
            'deploy': {
                'NameCoin': {
                    'contract': 'namecoin.se',
                    'retry': 15,
                    'wait': True
                }
            },
        },
        {
            'deploy': {
                'Subcurrency': {
                    'contract': 'subcurrency.se',
                    'endowment': 1000000000000000000,
                    'gas': 100000,
                    'retry': 30,
                    'wait': True
                }
            }
        },
        {
            'transact': {
                'RegisterSubToNameCoin': {
                    'to': '$NameCoin',
                    'sig': 'register:[int256,int256]:int256',
                    'gas': 100000,
                    'gas_price': 10000000000000,
                    'value': 0,
                    'data': [
                        '$Subcurrency',
                        'SubcurrencyName'
                    ],
                    'retry': 30,
                    'wait': True
                }
            }
        },
        {
            'transact': {
                'TestEncoding': {
                    'sig': 'some_method:[int256,int256,int256]:int256',
                    'gas': 100000,
                    'gas_price': 10000000000000,
                    'to': '$NameReg',
                    'value': 0,
                    'data': [
                        '$Subcurrency',
                        42,
                        '\x01\x00'],
                    'wait': False
                }
            }
        },
        {
            'call': {
                'GetNameFromNameCoin': {
                    'sig': 'get_name:[int256]:int256',
                    'to': '$NameCoin',
                    'data': [
                        '$Subcurrency'
                    ]
                }
            }
        },
        {
            'deploy': {
                'extra': {
                    'contract': 'short_namecoin.se',
                    'retry': 10,
                    'wait': True
                }
            }
        },
        {
            'deploy': {
                'Wallet': {
                    'contract': 'wallet.sol',
                    'solidity': [
                        'multiowned',
                        'daylimit',
                        'multisig',
                        'Wallet'
                    ],
                    'gas': 2500000,
                    'retry': 30,
                    'wait': True
                }
            }
        },
        {
            'transact': {
                'ToWallet': {
                    'to': '$Wallet',
                    'sig': 'kill:[$Subcurrency]:int256',
                    'retry': 15,
                    'wait': True
                }
            }
        }
    ]

def test_deploy(mocker):
    deployment = deploy.Deploy('test/fixtures/example.yaml', config)
    mocker.patch('requests.post', return_value=mock_json_response(status_code=200, result='0x01'))
    mocker.patch('time.sleep')
    if not has_solc:
        with pytest.raises(Exception) as excinfo:
            deployment.deploy()
        assert excinfo.value.message == 'solc compiler not found'
    else:
        deployment.deploy()

@solc
def test_compile_solidity(mocker):
    contract = 'test/fixtures/wallet.sol'
    deployment = deploy.Deploy('test/fixtures/example.yaml', config)
    contract_names = ['multiowned', 'daylimit', 'multisig', 'Wallet']
    contracts = deployment.compile_solidity(contract, contract_names)

    assert len(contracts) == 4
    for idx, (contract_name, code) in enumerate(contracts):
        assert contract_name == contract_names[idx]
        assert is_hex(code)
