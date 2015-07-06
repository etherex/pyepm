#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: jorisbontje
# @Date:   2014-08-03 13:53:04
# @Last Modified by:   caktux
# @Last Modified time: 2015-04-05 01:37:30

import json
import logging
import requests
import sys
import time
from colors import colors
from uuid import uuid4

from ethereum import abi
from serpent import get_prefix, decode_datalist
from utils import unhex

logger = logging.getLogger(__name__)
logging.getLogger("requests").setLevel(logging.WARNING)

def abi_data(sig, data):
    prefix = get_prefix(sig)
    data_abi = hex(prefix).rstrip('L')
    logger.debug("ABI prefix: %s" % data_abi)

    types = sig.split(':')[1][1:-1].split(',')
    logger.debug("ABI types: %s" % types)

    for i, s in enumerate(data):
        if isinstance(data[i], (str, unicode)) and data[i][:2] == "0x":
            data[i] = unhex(data[i])
    logger.debug("ABI data: %s" % data)

    data_abi += abi.encode_abi(types, data).encode('hex')
    logger.debug("ABI encoded: %s" % data_abi)

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
        self.fixed_price = config.getboolean("deploy", "fixed_price")
        self.gas_price_modifier = config.getfloat("deploy", "gas_price_modifier")

    def _rpc_post(self, method, params):
        if params is None:
            params = []

        payload = {
            "jsonrpc": "2.0",
            "id": str(uuid4()),
            "method": method,
            "params": params}
        headers = {'content-type': 'application/json'}

        logger.debug(json.dumps(payload))

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
            hexcount = self._rpc_post('eth_getTransactionCount', params)
            if hexcount is not None:
                count = unhex(hexcount)
            else:
                return None
            logger.debug("Tx count: %s" % count)
        except Exception as e:
            logger.info("Failed Tx count, returning None: %s" % e)
            count = None
        return count

    def transaction(self, transactionHash):
        params = [transactionHash]
        return self._rpc_post('eth_getTransactionByHash', params)

    def check(self):
        raise DeprecationWarning('the method `check` is no longer available')

    def coinbase(self):
        return self._rpc_post('eth_coinbase', None)

    def gasprice(self):
        result = self._rpc_post('eth_gasPrice', None)
        logger.debug("Got gas price: %s" % result)
        if result is not None:
            return unhex(result)
        return None

    def is_contract_at(self, address, defaultBlock='latest'):
        params = [address, defaultBlock]
        result = self._rpc_post('eth_getCode', params)
        if result is not None:
            return unhex(result) != 0
        return False

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
        if not self.fixed_price:
            net_price = self.gasprice()
            if net_price is None:
                gas_price = self.gas_price
            else:
                logger.info("    Gas price: {:.4f} szabo * {:.4f}".format(float(net_price) / 1000000000000, self.gas_price_modifier))
                gas_price = int(net_price * self.gas_price_modifier)
                logger.info("    Our price: %s" % "{:,}".format(gas_price))

        params = [{
            'data': code,
            'from': from_,
            'gas': hex(gas).rstrip('L'),
            'gasPrice': hex(gas_price).rstrip('L'),
            'value': hex(endowment).rstrip('L')
        }]
        return self._rpc_post('eth_sendTransaction', params)

    def get_contract_address(self, tx_hash):
        receipt = self._rpc_post('eth_getTransactionReceipt', [tx_hash])
        if receipt and 'contractAddress' in receipt:
            return receipt['contractAddress']
        return "0x0"

    def transact(self, dest, sig=None, data=None, gas=None, gas_price=None, value=0, from_=None, fun_name=None):
        if not dest.startswith('0x'):
            dest = '0x' + dest

        if fun_name is not None:
            raise DeprecationWarning("The `fun_name` definition is deprecated, use `serpent mk_signature <file>`"
                                     " output for your method in `sig` instead.")
        if sig is not None:
            data = abi_data(sig, data)

        if from_ is None:
            from_ = self.address

        if gas is None:
            gas = self.gas
        if gas_price is None:
            gas_price = self.gas_price
        if not self.fixed_price:
            net_price = self.gasprice()
            if net_price is None:
                gas_price = self.gas_price
            else:
                logger.info("    Gas price: {:.4f} szabo * {:.4f}".format(float(net_price) / 1000000000000, self.gas_price_modifier))
                gas_price = int(net_price * self.gas_price_modifier)
                logger.info("    Our price: %s" % "{:,}".format(gas_price))

        params = [{
            'from': from_,
            'to': dest,
            'data': data,
            'gas': hex(gas).rstrip('L'),
            'gasPrice': hex(gas_price).rstrip('L'),
            'value': hex(value).rstrip('L')}]
        return self._rpc_post('eth_sendTransaction', params)

    def call(self, dest, sig=None, data=None, gas=None, gas_price=None, value=0, from_=None, defaultBlock='latest', fun_name=None):
        if not dest.startswith('0x'):
            dest = '0x' + dest

        if fun_name is not None:
            raise DeprecationWarning("The `fun_name` definition is deprecated, use `serpent mk_signature <file>`"
                                     " output for your method in `sig` instead.")
        if sig is not None:
            data = abi_data(sig, data)

        if from_ is None:
            from_ = self.address

        if gas is None:
            gas = self.gas
        if gas_price is None:
            gas_price = self.gas_price
        if not self.fixed_price:
            net_price = self.gasprice()
            if net_price is None:
                gas_price = self.gas_price
            else:
                logger.info("    Gas price: {:.4f} szabo * {:.4f}".format(float(net_price) / 1000000000000, self.gas_price_modifier))
                gas_price = int(net_price * self.gas_price_modifier)
                logger.info("    Our price: %s" % "{:,}".format(gas_price))

        params = [{
            'from': from_,
            'to': dest,
            'data': data,
            'gas': hex(gas).rstrip('L'),
            'gasPrice': hex(gas_price).rstrip('L'),
            'value': hex(value).rstrip('L')}, defaultBlock]
        r = self._rpc_post('eth_call', params)
        if r is not None:
            return decode_datalist(r[2:].decode('hex'))
        return []

    def wait_for_contract(self, address, defaultBlock='latest', retry=False, skip=False, verbose=False):
        if verbose:
            if defaultBlock == 'pending':
                sys.stdout.write('    Waiting for contract at %s' % address)
            else:
                sys.stdout.write('    Waiting for contract to be mined')
        start_time = time.time()

        delta = 0
        while True:
            if verbose:
                sys.stdout.write('.')
                sys.stdout.flush()
            time.sleep(1)
            codeat = self.is_contract_at(address, defaultBlock)
            if codeat:
                break

            delta = time.time() - start_time

            if skip and delta > skip:
                logger.info(" Took too long, " + colors.WARNING + "skipping" + colors.ENDC + "...")
                break
            if retry and delta > retry:
                logger.info(" Took too long, " + colors.WARNING + "retrying" + colors.ENDC + "...")
                return False

        if verbose:
            if defaultBlock == 'pending':
                logger.info(" Took %ds" % delta)
            elif not ((skip and delta > skip) or (retry and delta > retry)):
                logger.info(" " + colors.OKGREEN + "Ready!" + colors.ENDC + " Mining took %ds" % delta)
        return True

    def wait_for_transaction(self, transactionHash, defaultBlock='latest', retry=False, skip=False, verbose=False):
        if verbose:
            if defaultBlock == 'pending':
                sys.stdout.write('    Waiting for transaction')
            else:
                sys.stdout.write('    Waiting for transaction to be mined')
        start_time = time.time()

        delta = 0
        while True:
            if verbose:
                sys.stdout.write('.')
                sys.stdout.flush()
            time.sleep(1)
            result = self.transaction(transactionHash)  # no defaultBlock, check result instead
            logger.debug("Transaction result: %s" % result)
            if isinstance(result, dict):
                if result['blockNumber'] is not None:
                    break
                if defaultBlock == 'pending' and result['blockNumber'] is None:
                    break
            elif result == "0x01":  # For test_deploy's mocked RPC.. TODO make sure there's no side effects
                return result

            delta = time.time() - start_time

            if skip and delta > skip:
                logger.info(" Took too long, " + colors.FAIL + "skipping" + colors.ENDC + "...")
                break
            if retry and delta > retry:
                logger.info(" Took too long, " + colors.WARNING + "retrying" + colors.ENDC + "...")
                return False

        if verbose:
            if defaultBlock == 'pending':
                logger.info(" Took %ds" % delta)
            elif not ((skip and delta > skip) or (retry and delta > retry)):
                logger.info(" " + colors.OKGREEN + "Ready!" + colors.ENDC + " Mining took %ds" % delta)
        return True

    def wait_for_next_block(self, from_block=None, retry=False, skip=False, verbose=False):
        if verbose:
            sys.stdout.write('Waiting for next block to be mined')
            start_time = time.time()

        if from_block is None:
            last_block = self.last_block()
        else:
            last_block = from_block

        delta = 0
        while True:
            if verbose:
                sys.stdout.write('.')
                sys.stdout.flush()
            time.sleep(1)
            block = self.last_block()
            if block != last_block:
                break

            delta = time.time() - start_time

            if skip and delta > skip:
                logger.info(" Took too long, " + colors.FAIL + "skipping" + colors.ENDC + "...")
                break
            if retry and delta > retry:
                logger.info(" Took too long, " + colors.WARNING + "retrying" + colors.ENDC + "...")
                return False

        if verbose and not ((skip and delta > skip) or (retry and delta > retry)):
            logger.info(" " + colors.OKGREEN + "Ready!" + colors.ENDC + " Mining took %ds" % delta)
        return True
