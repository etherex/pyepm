#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: jorisbontje
# @Date:   2014-08-03 13:53:04
# @Last Modified by:   caktux
# @Last Modified time: 2015-04-03 14:56:23

import json
import logging
import requests
import sys
import time
from uuid import uuid4

from pyethereum import abi
from serpent import get_prefix, decode_datalist
from utils import unhex

logger = logging.getLogger(__name__)

def abi_data(fun_name, sig, data):
    types = []
    prefix = get_prefix(fun_name, sig)
    data_abi = hex(prefix).rstrip('L')

    for i, s in enumerate(sig):
        if s == 's':
            types.append('string')
        elif s == 'a':
            types.append('int256[]')
        else:
            if isinstance(data[i], (str, unicode)) and data[i][:2] == "0x":
                data[i] = unhex(data[i])
            types.append('int256')
    data_abi += abi.encode_abi(types, data).encode('hex')

    logger.debug("ABI data: %s" % data_abi)
    return data_abi

class ApiException(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message

    def __str__(self):
        return "code=%d, message=\"%s\"" % (self.code, self.message)


class Api(object):

    def __init__(self, config):
        self.host = config.get('api', 'host')
        self.port = config.getint('api', 'port')
        self.jsonrpc_url = "http://%s:%s" % (self.host, self.port)
        logger.debug("Deploying to %s" % self.jsonrpc_url)

        address = config.get("api", "address")
        if not address.startswith('0x'):
            address = '0x' + address
        self.address = address

        self.gas = config.getint("deploy", "gas")
        self.gas_price = config.getint("deploy", "gas_price")

    def _rpc_post(self, method, params):
        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid4()),
            "method": method,
            "params": params}
        headers = {'content-type': 'application/json'}

        r = requests.post(self.jsonrpc_url, data=json.dumps(payload), headers=headers)
        if r.status_code >= 400:
            raise ApiException(r.status_code, r.reason)

        response = r.json()

        logger.debug(response)

        if 'error' in response:
            raise ApiException(response['error']['code'], response['error']['message'])

        return response.get('result')

    def accounts(self):
        return self._rpc_post('eth_accounts', None)

    def balance_at(self, address, defaultBlock='latest'):
        params = [address, defaultBlock]
        balance = self._rpc_post('eth_getBalance', params)
        if balance is not None:
            return unhex(balance)
        return 0

    def block(self, nr, includeTransactions=False):
        params = [hex(nr).rstrip('L'), includeTransactions]
        return self._rpc_post('eth_getBlockByNumber', params)

    def defaultBlock(self):
        raise DeprecationWarning('the function `defaultBlock` is deprecated, use `defaultBlock` as function argument in your request')

    def setDefaultBlock(self):
        raise DeprecationWarning('the method `setDefaultBlock` is deprecated, use `defaultBlock` as function argument in your request')

    def transaction_count(self, address=None, defaultBlock='latest'):
        if address is None:
            address = self.address
        params = [str(address), defaultBlock]
        try:
            count = int(self._rpc_post('eth_getTransactionCount', params), 16)
            logger.debug("Tx count: %s" % count)
        except Exception as e:
            logger.debug("Failed Tx count, returning 0: %s" % e)
            count = 0
        return count

    def check(self):
        raise DeprecationWarning('the method `check` is no longer available')

    def coinbase(self):
        return self._rpc_post('eth_coinbase', None)

    def create(self, code, from_=None, gas=None, gas_price=None, endowment=0):
        if not code.startswith('0x'):
            code = '0x' + code
        # params = [{'code': code}]

        if gas is None:
            gas = self.gas
        if gas_price is None:
            gas_price = self.gas_price
        if from_ is None:
            from_ = self.address

        params = [{
            'data': code,
            'from': from_,
            'gas': hex(gas).rstrip('L'),
            'gasPrice': hex(gas_price).rstrip('L'),
            'value': hex(endowment).rstrip('L')
        }]
        return self._rpc_post('eth_sendTransaction', params)

    def is_contract_at(self, address, defaultBlock='latest'):
        params = [address, defaultBlock]
        result = self._rpc_post('eth_getCode', params)
        if result is not None:
            return unhex(result) != 0
        return True

    def is_listening(self):
        return self._rpc_post('net_listening', None)

    def is_mining(self):
        return self._rpc_post('eth_mining', None)

    def key(self):
        raise DeprecationWarning('the function `key` is no longer available in the JSON RPC API')

    def keys(self):
        raise DeprecationWarning('the function `keys` is no longer available in the JSON RPC API')

    def last_block(self):
        return self.block(self.number())

    def lll(self, contract):
        params = {
            's': contract
        }
        return self._rpc_post('eth_compileLLL', params)

    def logs(self, filter):
        params = [filter]
        return self._rpc_post('eth_getLogs', params)

    def number(self):
        return unhex(self._rpc_post('eth_blockNumber', None))

    def peer_count(self):
        return unhex(self._rpc_post('net_peerCount', None))

    def state_at(self, address, index, defaultBlock='latest'):
        raise DeprecationWarning('the method `stateAt` is no longer available in the JSON RPC API, use `eth_getStorageAt` (`storage_at` in PyEPM) instead.')

    def storage_at(self, address, index, defaultBlock='latest'):
        params = [address, hex(index), defaultBlock]
        return self._rpc_post('eth_getStorageAt', params)

    def transact(self, dest, fun_name=None, sig='', data=None, gas=None, gas_price=None, value=0, from_=None):
        if not dest.startswith('0x'):
            dest = '0x' + dest

        if fun_name is not None:
            data = abi_data(fun_name, sig, data)

        if gas is None:
            gas = self.gas
        if gas_price is None:
            gas_price = self.gas_price
        if from_ is None:
            from_ = self.address

        params = [{
            'from': from_,
            'to': dest,
            'data': data,
            'gas': hex(gas).rstrip('L'),
            'gasPrice': hex(gas_price).rstrip('L'),
            'value': hex(value).rstrip('L')}]
        return self._rpc_post('eth_sendTransaction', params)

    def call(self, dest, fun_name, sig='', data=None, gas=None, gas_price=None, from_=None, defaultBlock='latest'):
        if not dest.startswith('0x'):
            dest = '0x' + dest

        if fun_name is not None:
            data = abi_data(fun_name, sig, data)

        if gas is None:
            gas = self.gas
        if gas_price is None:
            gas_price = self.gas_price
        if from_ is None:
            from_ = self.address

        params = [{
            'from': from_,
            'to': dest,
            'data': data,
            'gas': hex(gas).rstrip('L'),
            'gasPrice': hex(gas_price).rstrip('L')}, defaultBlock]
        r = self._rpc_post('eth_call', params)
        if r is not None:
            return decode_datalist(r[2:].decode('hex'))
        return []

    def wait_for_contract(self, address, verbose=False, defaultBlock='latest'):
        if verbose:
            sys.stdout.write('Waiting for contract at %s' % address)
            start_time = time.time()

        while True:
            if verbose:
                sys.stdout.write('.')
                sys.stdout.flush()
            time.sleep(1)
            codeat = self.is_contract_at(address, defaultBlock)
            if codeat:
                break

        if verbose:
            delta = time.time() - start_time
            logger.info(" took %ds" % delta)

    def wait_for_transaction(self, from_count=None, verbose=False):
        if from_count is None:
            time.sleep(1)
            return

        if verbose:
            sys.stdout.write('Waiting for transaction')
            start_time = time.time()

        while True:
            if verbose:
                sys.stdout.write('.')
                sys.stdout.flush()
            time.sleep(1)
            to_count = self.transaction_count(defaultBlock='pending')
            if to_count > from_count:
                break

        if verbose:
            delta = time.time() - start_time
            logger.info(" took %ds" % delta)

    def wait_for_next_block(self, from_block=None, verbose=False):
        if verbose:
            sys.stdout.write('Waiting for next block to be mined')
            start_time = time.time()

        if from_block is None:
            last_block = self.last_block()
        else:
            last_block = from_block

        while True:
            if verbose:
                sys.stdout.write('.')
                sys.stdout.flush()
            time.sleep(1)
            block = self.last_block()
            if block != last_block:
                break

        if verbose:
            delta = time.time() - start_time
            logger.info(" Ready! Mining took %ds" % delta)
