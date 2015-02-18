from pyepm import deploy, config
config = config.get_default_config()

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
                "wait": True
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
                "wait": True
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
