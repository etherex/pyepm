#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: caktux
# @Date:   2014-12-21 12:44:20
# @Last Modified by:   caktux
# @Last Modified time: 2015-02-17 23:29:14

import logging

import os
import api
import json
import yaml
import subprocess

logger = logging.getLogger(__name__)

from serpent import compile

class Deploy(object):
    def __init__(self, filename, config):
        self.filename = filename
        self.config = config

    def deploy(self, wait=False):
        default_from = self.config.get('api', 'address')
        default_gas = int(self.config.get('deploy', 'gas'))
        default_gas_price = int(self.config.get('deploy', 'gas_price'))

        # Load YAML definitions
        definitions = self.load_yaml()

        logger.info("Parsing %s..." % self.filename)
        path = os.path.dirname(self.filename)

        for definition in definitions:
            for key in definition:
                logger.info("%s: " % key)

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
                        wait = False
                        for option in definition[key][name]:
                            if option == 'contract':
                                contract = definition[key][name][option]
                            if option == 'solidity':
                                contract_names = definition[key][name][option]
                            if option == 'from':
                                from_ = definition[key][name][option]
                            if option == 'gas':
                                gas = definition[key][name][option]
                            if option == 'gas_price':
                                gas_price = definition[key][name][option]
                            if option == 'endowment':
                                value = definition[key][name][option]
                            if option == 'wait':
                                wait = definition[key][name][option]
                        logger.info("    Deploying %s..." % os.path.join(path, contract))
                        contract_address = self.create("%s" % os.path.join(path, contract), from_, gas, gas_price, value, wait, contract_names=contract_names)
                        definitions = self.replace(name, definitions, contract_address, True)
                    logger.debug(definitions)

                if key in ['transact', 'call']:
                    for name in definition[key]:
                        # Reset default values at each definition
                        from_ = default_from
                        to = None
                        fun_name = None
                        sig = None
                        data = ''
                        gas = default_gas
                        gas_price = default_gas_price
                        value = 0
                        wait = False
                        for option in definition[key][name]:
                            if option == 'from':
                                from_ = definition[key][name][option]
                            if option == 'to':
                                to = definition[key][name][option]
                            if option == 'fun_name':
                                fun_name = definition[key][name][option]
                            if option == 'sig':
                                sig = definition[key][name][option]
                            if option == 'data':
                                dat = definition[key][name][option]
                                if isinstance(dat, list):
                                    for i, d in enumerate(dat):
                                        if isinstance(d, (basestring)) and not d.startswith("0x") and not d.startswith("$"):
                                            padded = "0x" + d.encode('hex')
                                            definition[key][name][option][i] = u"%s" % padded
                                            logger.info("  Converting '%s' string to %s" % (d, padded))
                                data = definition[key][name][option]
                            if option == 'gas':
                                gas = definition[key][name][option]
                            if option == 'gas_price':
                                gas_price = definition[key][name][option]
                            if option == 'value':
                                value = definition[key][name][option]
                            if option == 'wait':
                                wait = definition[key][name][option]
                        logger.info("    %s to %s (%s)..." % ("Transaction" if key == 'transact' else "Call", name, to))
                        if data:
                            logger.info("      with data: %s" % data)
                        if key == 'transact':
                            self.transact(to, from_, fun_name, sig, data, gas, gas_price, value, wait)
                        elif key == 'call':
                            self.call(to, from_, fun_name, sig, data, gas, gas_price, value, wait)

    def compile_solidity(self, contract, contract_names=[]):
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

    def create(self, contract, from_, gas, gas_price, value, wait, contract_names=None):
        instance = api.Api(self.config)
        contract_addresses = []
        if contract[-3:] == 'sol' or contract_names:
            contracts = self.compile_solidity(contract, contract_names)
            if contract_names:
                for contract_name, contract in contracts:
                    logger.info("%s: %s" % (contract_name, contract))
                    contract_address = instance.create(contract, from_=from_, gas=gas, gas_price=gas_price, endowment=value)
                    contract_addresses.append(contract_address)
                    logger.info("      Contract '%s' is available at %s" % (contract_name, contract_address))
            else:
                contract_address = instance.create(contract, from_=from_, gas=gas, gas_price=gas_price, endowment=value)
                logger.info("      Contract is available at %s" % contract_address)
        else:
            contract = compile(open(contract).read()).encode('hex')
            contract_address = instance.create(contract, from_=from_, gas=gas, gas_price=gas_price, endowment=value)
            logger.info("      Contract is available at %s" % contract_address)
        if wait:
            instance.wait_for_next_block(verbose=(True if self.config.get('misc', 'verbosity') > 1 else False))

        if contract_addresses:
            return contract_addresses
        return contract_address

    def transact(self, to, from_, fun_name, sig, data, gas, gas_price, value, wait):
        instance = api.Api(self.config)
        result = instance.transact(to, fun_name=fun_name, sig=sig, data=data, gas=gas, gas_price=gas_price, value=value)
        logger.info("      Result: %s" % (result if result else "OK"))
        if wait:
            instance.wait_for_next_block(verbose=(True if self.config.get('misc', 'verbosity') > 1 else False))

    def call(self, to, from_, fun_name, sig, data, gas, gas_price, value, wait):
        instance = api.Api(self.config)
        result = instance.call(to, fun_name=fun_name, sig=sig, data=data, gas=gas, gas_price=gas_price, value=value)
        logger.info("      Result: %s" % result)
        if wait:
            instance.wait_for_next_block(verbose=(True if self.config.get('misc', 'verbosity') > 1 else False))

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
            logger.info("  %sReplacing $%s with %s (%s)" % (("      " if isContract else ""), variable, replacement, count))

        return definitions

    def load_yaml(self):
        logger.info("Loading %s..." % self.filename)
        f = open(self.filename)
        data = yaml.load(f)
        f.close()
        logger.debug(json.dumps(data, indent=4))

        return data

