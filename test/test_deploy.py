import pytest

from pyepm import deploy

from helpers import config, has_solc, is_hex, mock_json_response, solc

def test_load_yaml():
    deployment = deploy.Deploy('test/fixtures/example.yaml.fixture', config)
    result = deployment.load_yaml()
    assert result == [
        {
            "set": {
                "NameReg": "0x72ba7d8e73fe8eb666ea66babc8116a41bfb10e2"
            }
        },
        {
            "deploy": {
                "NameCoin": {
                    "contract": "namecoin.se",
                    "wait": False
                },
                "Subcurrency": {
                    "contract": "subcurrency.se",
                    "endowment": 1000000000000000000,
                    "gas": 100000
                }
            }
        },
        {
            "transact": {
                "NameReg": {
                    "fun_name": "register",
                    "sig": "i",
                    "gas": 10000,
                    "gas_price": 10000000000000,
                    "to": "$NameReg",
                    "value": 0,
                    "data": [
                        "$Subcurrency"
                    ],
                    "wait": False
                }
            }
        },
        {
            'transact': {
                'TestEncoding': {
                    'fun_name': 'some_method',
                    'sig': 'iii',
                    'gas': 10000,
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
            "call": {
                "GetMarket": {
                    "fun_name": "get_market",
                    "sig": "i",
                    "to": "0x77045e71a7a2c50903d88e564cd72fab11e82051",
                    "data": [
                        1
                    ]
                }
            }
        },
        {
            "deploy": {
                "extra": {
                    "contract": "short_namecoin.se"
                }
            }
        },
        {
            "deploy": {
                "Config": {
                    "contract": "config.sol",
                    "solidity": [
                        "Config",
                        "mortal",
                        "owned"
                    ]
                }
            }
        }
    ]

def test_deploy(mocker):
    deployment = deploy.Deploy('test/fixtures/example.yaml.fixture', config)
    mocker.patch('requests.post', return_value=mock_json_response(status_code=200, result=None))
    mocker.patch('time.sleep')
    if not has_solc:
        with pytest.raises(Exception) as excinfo:
            deployment.deploy()
        assert excinfo.value.message == 'solc compiler not found'
    else:
        deployment.deploy()

@solc
def test_compile_solidity(mocker):
    contract = 'test/fixtures/config.sol'
    deployment = deploy.Deploy('test/fixtures/example.yaml.fixture', config)
    contract_names = ['Config', 'mortal', 'owned']
    contracts = deployment.compile_solidity(contract, contract_names)

    assert len(contracts) == 3
    for idx, (contract_name, code) in enumerate(contracts):
        assert contract_name == contract_names[idx]
        assert is_hex(code)
