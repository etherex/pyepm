from pyepm import deploy, config
config = config.get_default_config()

def test_load_yaml():
    deployment = deploy.Deploy('test/fixtures/example.yaml.fixture', config)
    result = deployment.load_yaml()
    assert result == [
        {'set': {'NameReg': '0x72ba7d8e73fe8eb666ea66babc8116a41bfb10e2'}},
        {'deploy': {'NameCoin': {'contract': 'namecoin.se', 'wait': True},
                    'Subcurrency': {'contract': 'subcurrency.se',
                                    'endowment': 1000000000000000000,
                                    'gas': 100000}}},
        {'transact': {'NameReg': {'data': '$Subcurrency',
                                  'funid': 0,
                                  'gas': 10000,
                                  'gas_price': 10000000000000,
                                  'to': '$NameReg',
                                  'value': 0,
                                  'wait': True}}},
        {'call': {'MySubcurrency': {'data': [1, 74565],
                                    'funid': 1,
                                    'to': '$Subcurrency',
                                    'value': 0}}},
        {'deploy': {'extra': {'contract': 'short_namecoin.se'}}}]
