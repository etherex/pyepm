#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: caktux
# @Date:   2014-12-21 12:44:20
# @Last Modified by:   caktux
# @Last Modified time: 2015-04-05 01:25:39

import logging

import os
import api
import json
import yaml
import subprocess
from colors import colors
from distutils import spawn
from serpent import compile

logger = logging.getLogger(__name__)

class Deploy(object):
    def __init__(self, filename, config):
        self.filename = filename
        self.config = config

    def deploy(self, wait=False):
        default_from = self.config.get('api', 'address')
        default_gas = int(self.config.getint('deploy', 'gas'))
        default_gas_price = int(self.config.getint('deploy', 'gas_price'))

        # Load YAML definitions
        definitions = self.load_yaml()

        logger.debug("\nParsing %s..." % self.filename)
        path = os.path.dirname(self.filename)

        for definition in definitions:
            for key in definition:
                logger.info(colors.HEADER + "\n%s: " % key + colors.ENDC)

                if key == 'set':
                    for variable in definition[key]:
                        replacement = definition[key][variable]
                        definitions = self.replace(variable, definitions, replacement)
                    logger.debug(definitions)

                if key == 'deploy':
                    for name in definition[key]:
                        # Reset default values at each definition
                        contract_names = []
                        from_ = default_from
                        gas = default_gas
                        gas_price = default_gas_price
                        value = 0
                        retry = False
                        skip = False
                        wait = False
                        for option in definition[key][name]:
                            if option == 'contract':
                                contract = definition[key][name][option]
                            if option == 'solidity':
                                contract_names = definition[key][name][option]
                            if option == 'from':
                                from_ = definition[key][name][option]
                            if option == 'gas':
                                gas = int(definition[key][name][option])
                            if option == 'gas_price':
                                gas_price = int(definition[key][name][option])
                            if option == 'value':
                                value = int(definition[key][name][option])
                            if option == 'endowment':
                                value = int(definition[key][name][option])
                            if option == 'wait':
                                wait = definition[key][name][option]
                            if option == 'skip':
                                skip = int(definition[key][name][option])
                            if option == 'retry':
                                retry = int(definition[key][name][option])
                        logger.info("  Deploying " + colors.BOLD + "%s" % os.path.join(path, contract) + colors.ENDC + "...")
                        addresses = self.create("%s" % os.path.join(path, contract),
                                                from_, gas, gas_price, value,
                                                retry, skip, wait,
                                                contract_names=contract_names if contract_names else name)
                        if isinstance(addresses, list):
                            for address in addresses:
                                definitions = self.replace(name, definitions, address, True)
                        else:
                            definitions = self.replace(name, definitions, addresses, True)
                    logger.debug(definitions)

                if key in ['transact', 'call']:
                    for name in definition[key]:
                        # Reset default values at each definition
                        from_ = default_from
                        to = None
                        sig = None
                        data = ''
                        gas = default_gas
                        gas_price = default_gas_price
                        value = 0
                        retry = False
                        skip = False
                        wait = False
                        for option in definition[key][name]:
                            if option == 'from':
                                from_ = definition[key][name][option]
                            if option == 'to':
                                to = definition[key][name][option]
                            if option == 'fun_name':
                                raise DeprecationWarning("The `fun_name` definition is deprecated, use `serpent mk_signature <file>`"
                                                         " output for your method in `sig` instead.")
                            if option == 'sig':
                                sig = definition[key][name][option]
                            if option == 'data':
                                dat = definition[key][name][option]
                                if isinstance(dat, list):
                                    for i, d in enumerate(dat):
                                        if isinstance(d, (basestring)) and not d.startswith("0x") and not d.startswith("$"):
                                            if d != d.decode('string_escape'):
                                                definition[key][name][option][i] = d.decode('string_escape')
                                            else:
                                                padded = "0x" + d.encode('hex')
                                                definition[key][name][option][i] = u"%s" % padded
                                                logger.info("  Converting " + colors.BOLD + "'%s'" % d.encode('unicode-escape') + colors.ENDC +
                                                            " string to " + colors.BOLD + "%s" % padded + colors.ENDC)
                                data = definition[key][name][option]
                            if option == 'gas':
                                gas = int(definition[key][name][option])
                            if option == 'gas_price':
                                gas_price = int(definition[key][name][option])
                            if option == 'value':
                                value = int(definition[key][name][option])
                            if option == 'retry':
                                retry = int(definition[key][name][option])
                            if option == 'skip':
                                skip = int(definition[key][name][option])
                            if option == 'wait':
                                wait = definition[key][name][option]
                        logger.info("  %s " % ("Transaction" if key == 'transact' else "Call") +
                                    colors.BOLD + "%s" % name + colors.ENDC + " to " +
                                    colors.BOLD + "%s " % to + colors.ENDC + "...")
                        if data:
                            bluedata = []
                            for dat in data:
                                bluedata.append(colors.OKBLUE + "%s" % dat + colors.ENDC)
                            logger.info("      with data: [" + ", ".join(bluedata) + "]")
                        if key == 'transact':
                            self.transact(to, from_, sig, data, gas, gas_price, value, retry, skip, wait)
                        elif key == 'call':
                            self.call(to, from_, sig, data, gas, gas_price, value)

        logger.info("\n" + colors.OKGREEN + "Done!" + colors.ENDC + "\n")

    def compile_solidity(self, contract, contract_names=[]):
        if not spawn.find_executable("solc"):
            raise Exception("solc compiler not found")

        subprocess.call(["solc", "--input-file", contract, "--binary", "file"])
        contracts = []

        if not isinstance(contract_names, list):
            raise Exception("Contract names must be list")
        if not contract_names:
            contract_names = [contract[:-4]]
        for contract_name in contract_names:
            filename = "%s.binary" % contract_name
            evm = "0x" + open(filename).read()
            contracts.append((contract_name, evm))

        return contracts

    def create(self, contract, from_, gas, gas_price, value, retry, skip, wait, contract_names=None):
        instance = api.Api(self.config)
        verbose = (True if self.config.get('misc', 'verbosity') > 1 else False)

        addresses = self.try_create_deploy(contract, from_, gas, gas_price, value, retry, skip, verbose, contract_names)

        # Wait for single contract in pending state
        if not isinstance(addresses, list):
            if not retry:
                instance.wait_for_contract(addresses, defaultBlock='pending', retry=retry, skip=skip, verbose=verbose)
            else:
                successful = False
                while not successful:
                    successful = instance.wait_for_contract(addresses, defaultBlock='pending', retry=retry, skip=skip, verbose=verbose)
                    if not successful:
                        addresses = self.try_create_deploy(contract, from_, gas, gas_price, value, retry, skip, verbose, contract_names)

        # Wait for contract(s) being mined
        if wait:
            if not retry:
                if isinstance(addresses, list):
                    for address in addresses:
                        instance.wait_for_contract(address, retry=retry, skip=skip, verbose=verbose)
                else:
                    instance.wait_for_contract(addresses, retry=retry, skip=skip, verbose=verbose)
            else:
                successful = False
                while not successful:
                    if isinstance(addresses, list):
                        for i, address in enumerate(addresses):
                            success = False
                            while not success:
                                success = instance.wait_for_contract(address, retry=retry, skip=skip, verbose=verbose)
                                if not success:
                                    break
                            if success and i == len(addresses) - 1:
                                successful = True
                            elif not success:
                                break
                    else:
                        successful = instance.wait_for_contract(addresses, retry=retry, skip=skip, verbose=verbose)
                    if not successful:
                        addresses = self.try_create_deploy(contract, from_, gas, gas_price, value, retry, skip, verbose, contract_names)

        return addresses

    def try_create_deploy(self, contract, from_, gas, gas_price, value, retry, skip, verbose, contract_names):
        instance = api.Api(self.config)
        addresses = []
        if contract[-3:] == 'sol' or isinstance(contract_names, list):
            contracts = self.compile_solidity(contract, contract_names)

            for contract_name, contract in contracts:
                logger.debug("%s: %s" % (contract_name, contract))

                address = self.try_create(contract, contract_name=contract_name, from_=from_, gas=gas, gas_price=gas_price, value=value)

                if not retry:
                    instance.wait_for_contract(address, defaultBlock='pending', retry=retry, skip=skip, verbose=verbose)
                else:
                    successful = False
                    while not successful:
                        successful = instance.wait_for_contract(address, defaultBlock='pending', retry=retry, skip=skip, verbose=verbose)
                        if not successful:
                            address = self.try_create(contract, contract_name=contract_name, from_=from_, gas=gas, gas_price=gas_price, value=value)

                addresses.append(address)
        else:
            contract = compile(open(contract).read()).encode('hex')
            address = self.try_create(contract, contract_name=contract_names, from_=from_, gas=gas, gas_price=gas_price, value=value)

        if addresses:
            return addresses
        return address

    def try_create(self, contract, from_, gas, gas_price, value, contract_name=None):
        instance = api.Api(self.config)
        address = instance.create(contract, from_=from_, gas=gas, gas_price=gas_price, endowment=value)
        if contract_name:
            logger.info("      Contract " + colors.BOLD + "'%s'" % contract_name + colors.ENDC +
                        " will be available at " + colors.WARNING + "%s" % address + colors.ENDC)
        else:
            logger.info("      Contract will be available at " + colors.WARNING + "%s" % address + colors.ENDC)
        return address

    def transact(self, to, from_, sig, data, gas, gas_price, value, retry, skip, wait):
        instance = api.Api(self.config)
        # from_count = instance.transaction_count(defaultBlock='pending')
        verbose = (True if self.config.get('misc', 'verbosity') > 1 else False)

        result = self.try_transact(to, from_, sig, data, gas, gas_price, value)

        # Wait for transaction in Tx pool
        if not retry:
            instance.wait_for_transaction(transactionHash=result, defaultBlock='pending', retry=retry, skip=skip, verbose=verbose)
        else:
            successful = False
            while not successful:
                successful = instance.wait_for_transaction(transactionHash=result, defaultBlock='pending', retry=retry, skip=skip, verbose=verbose)
                if not successful:
                    result = self.try_transact(to, from_, sig, data, gas, gas_price, value)

        # Wait for transaction being mined
        if wait:
            if result.startswith("0x"):
                if not retry:
                    instance.wait_for_transaction(transactionHash=result, retry=retry, skip=skip, verbose=verbose)
                else:
                    successful = False
                    while not successful:
                        successful = instance.wait_for_transaction(transactionHash=result, retry=retry, skip=skip, verbose=verbose)
                        if not successful:
                            result = self.try_transact(to, from_, sig, data, gas, gas_price, value)
            else:
                from_block = instance.last_block()
                if not retry:
                    instance.wait_for_next_block(from_block=from_block, retry=retry, skip=skip, verbose=verbose)
                else:
                    successful = False
                    while not successful:
                        successful = instance.wait_for_next_block(from_block=from_block, retry=retry, skip=skip, verbose=verbose)
                        if not successful:
                            result = self.try_transact(to, from_, sig, data, gas, gas_price, value)

    def try_transact(self, to, from_, sig, data, gas, gas_price, value):
        instance = api.Api(self.config)
        result = instance.transact(to, from_=from_, sig=sig, data=data, gas=gas, gas_price=gas_price, value=value)
        logger.info("      Result: " + colors.BOLD + "%s" % (result if result else "OK") + colors.ENDC)
        return result

    def call(self, to, from_, sig, data, gas, gas_price, value):
        instance = api.Api(self.config)

        result = instance.call(to, sig=sig, data=data, gas=gas, gas_price=gas_price, value=value)
        logger.info("      Result: " + colors.BOLD + "%s" % result + colors.ENDC)

        return result

    def replace(self, variable, definitions, replacement, isContract=False):
        # Replace variables
        count = 0
        for repdef in definitions:
            for repkey in repdef:
                for repname in repdef[repkey]:
                    if repkey != 'set':
                        for repoption in repdef[repkey][repname]:
                            to_replace = repdef[repkey][repname][repoption]
                            if to_replace == "$%s" % variable:
                                logger.debug("- Replacing $%s with %s" % (variable, replacement))
                                repdef[repkey][repname][repoption] = replacement
                                count = count + 1
                            if repoption == 'data':
                                for i, repdata in enumerate(to_replace):
                                    if repdata == "$%s" % variable:
                                        logger.debug("- Replacing $%s with %s" % (variable, replacement))
                                        repdef[repkey][repname][repoption][i] = replacement
                                        count = count + 1
        if count:
            logger.info("  %sReplacing $%s with " % (("      " if isContract else ""), variable) +
                        colors.BOLD + "%s" % replacement + colors.ENDC + " (%s)" % count)

        return definitions

    def load_yaml(self):
        logger.debug("\nLoading %s..." % self.filename)
        f = open(self.filename)
        data = yaml.load(f)
        f.close()
        logger.debug(json.dumps(data, indent=4))

        return data
