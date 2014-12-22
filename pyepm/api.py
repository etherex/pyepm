#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: jorisbontje
# @Date:   2014-08-03 13:53:04
# @Last Modified by:   caktux
# @Last Modified time: 2014-12-22 04:24:00

import json
import logging
import requests
import sys
import time
from uuid import uuid4

from pyethereum import utils
import serpent

import config as c
config = c.read_config()

logger = logging.getLogger(__name__)

class ApiException(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message

    def __str__(self):
        return "code=%d, message=\"%s\"" % (self.code, self.message)


class Api(object):

    def __init__(self):
        self.host = config.get('api', 'host')
        self.port = config.getint('api', 'port')
        self.jsonrpc_url = "http://%s:%s" % (self.host, self.port)
        self.address = config.get("api", "address")

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

    def balance_at(self, address):
        params = [address]
        balance = self._rpc_post('eth_balanceAt', params)
        if balance == "0x":
            return 0
        else:
            return int(balance, 16)

    def block(self, nr):
        params = [nr]
        return self._rpc_post('eth_blockByNumber', params)

    def check(self, addresses):
        params = {
            'a': addresses
        }
        return self._rpc_post('check', params)

    def coinbase(self):
        return self._rpc_post('eth_coinbase', None)

    def create(self, code, from_=config.get("api", "address"), gas=config.get("deploy", "gas"), gas_price=config.get("deploy", "gas_price"), endowment=0):
        if not code.startswith('0x'):
            code = '0x' + code
        params = [{'code': code}]
        # FIXME
        # params = [{
        #    'code': code,
        #    'from': from_,
        #    'gas': hex(gas),
        #    'gasPrice': hex(gas_price),
        #    'value': hex(value)}]
        return self._rpc_post('eth_transact', params)

    def is_contract_at(self, address):
        params = [address]
        return int(self._rpc_post('eth_codeAt', params), 16) != 0

    def is_listening(self):
        return self._rpc_post('eth_listening', None)

    def is_mining(self):
        return self._rpc_post('eth_mining', None)

    def key(self):
        return self._rpc_post('key', None)

    def keys(self):
        return self._rpc_post('keys', None)

    def last_block(self):
        return self.block(-1)

    def lll(self, contract):
        params = {
            's': contract
        }
        return self._rpc_post('eth_lll', params)

    def number(self):
        return self._rpc_post('eth_number', None)

    def peer_count(self):
        return self._rpc_post('eth_peerCount', None)

    def state_at(self, address, index):
        params = [address, index]
        return self._rpc_post('eth_stateAt', params)

    def storage_at(self, address):
        params = [address]
        return self._rpc_post('eth_storageAt', params)

    def transact(self, dest, from_=config.get("api", "address"), funid=None, data="", gas=config.get("deploy", "gas"), gas_price=config.get("deploy", "gas_price"), value=0):
        if not dest.startswith('0x'):
            dest = '0x' + dest

        if funid is not None:
            data = "0x" + serpent.encode_abi(funid, data).encode('hex')

        params = [{
            'to': dest,
            'data': data,
            'gas': hex(gas),
            'gasPrice': hex(gas_price),
            'value': hex(value)}]
        return self._rpc_post('eth_transact', params)

    def call(self, dest, from_=config.get("api", "address"), funid=None, data="", gas=config.get("deploy", "gas"), gas_price=config.get("deploy", "gas_price"), value=0):
        if not dest.startswith('0x'):
            dest = '0x' + dest

        if funid is not None:
            data = "0x" + serpent.encode_abi(funid, data).encode('hex')

        params = [{
            'to': dest,
            'data': data,
            'from': from_,
            'gas': hex(gas),
            'gasPrice': hex(gas_price),
            'value': hex(value)}]
        r = self._rpc_post('eth_call', params)
        return serpent.decode_datalist(r[2:].decode('hex'))

    def wait_for_next_block(self, verbose=False):
        if verbose:
            sys.stdout.write('Waiting for next block to be mined')
            start_time = time.time()

        last_block = self.last_block()
        while True:
            if verbose:
                sys.stdout.write('.')
                sys.stdout.flush()
            time.sleep(5)
            block = self.last_block()
            if block != last_block:
                break

        if verbose:
            delta = time.time() - start_time
            logger.info("Ready! Mining took %ds" % delta)
