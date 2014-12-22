#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: caktux
# @Date:   2014-12-21 12:44:20
# @Last Modified by:   caktux
# @Last Modified time: 2014-12-22 04:36:43

import logging

import api
import json
import yaml
import config as c
config = c.read_config()

logger = logging.getLogger(__name__)

from serpent import compile

default_from = config.get('api', 'address')
default_gas = int(config.get('deploy', 'gas'))
default_gas_price = int(config.get('deploy', 'gas_price'))

def deploy(filename, wait=False):
    # Load YAML definitions
    definitions = load_yaml(filename)

    # Dynamic variables
    variables = {}

    logger.info("Parsing %s..." % filename)

    for definition in definitions:
        for key in definition:
            logger.info("%s: " % key)

            if key == 'set':
                for name in definition[key]:
                    # Replace variables
                    for repdef in definitions:
                        for repkey in repdef:
                            for repname in repdef[repkey]:
                                if repkey != 'set':
                                    for repoption in repdef[repkey][repname]:
                                        if repdef[repkey][repname][repoption] == "$%s" % name:
                                            logger.debug("Replacing $%s with %s" % (name, definition[key][name]))
                                            repdef[repkey][repname][repoption] = definition[key][name]
                    logger.info("  %s: %s" % (name, definition[key][name]))
                logger.debug(definitions)

            if key == 'deploy':
                for name in definition[key]:
                    # Reset default values at each definition
                    from_ = default_from
                    gas = default_gas
                    gas_price = default_gas_price
                    wait = False
                    for option in definition[key][name]:
                        if option == 'contract':
                            contract = definition[key][name][option]
                        if option == 'gas':
                            gas = definition[key][name][option]
                        if option == 'gas_price':
                            gas_price = definition[key][name][option]
                        if option == 'endowment':
                            value = definition[key][name][option]
                        if option == 'wait':
                            wait = definition[key][name][option]
                    logger.info("    Deploying %s..." % contract)
                    create(contract, gas, gas_price, value, wait)

            if key in ['transact', 'call']:
                for name in definition[key]:
                    # Reset default values at each definition
                    from_ = default_from
                    to = None
                    funid = None
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
                        if option == 'funid':
                            funid = definition[key][name][option]
                        if option == 'data':
                            data = definition[key][name][option]
                        if option == 'gas':
                            gas = definition[key][name][option]
                        if option == 'gas_price':
                            gas_price = definition[key][name][option]
                        if option == 'value':
                            value = definition[key][name][option]
                        if option == 'wait':
                            wait = definition[key][name][option]
                    logger.info("    Transaction to %s..." % to)
                    if key == 'transact':
                        transact(to, from_, funid, data, gas, gas_price, value, wait)
                    elif key == 'call':
                        call(to, from_, funid, data, gas, gas_price, value, wait)


def create(contract, gas, gas_price, value, wait):
    instance = api.Api()
    contract = compile(open(contract).read()).encode('hex')
    contract_address = instance.create(contract, gas=gas, gas_price=gas_price, endowment=value)
    logger.info("      Contract is available at %s" % contract_address)
    if wait:
        instance.wait_for_next_block(verbose=(True if config.get('misc', 'verbosity') > 1 else False))

def transact(to, from_, funid, data, gas, gas_price, value, wait):
    instance = api.Api()
    result = instance.transact(to, funid=funid, data=data, gas=gas, gas_price=gas_price, value=value)
    logger.info("      Result: %s" % (result if result else "OK"))
    if wait:
        instance.wait_for_next_block(verbose=(True if config.get('misc', 'verbosity') > 1 else False))

def call(to, from_, funid, data, gas, gas_price, value, wait):
    instance = api.Api()
    result = instance.call(to, funid=funid, data=data, gas=gas, gas_price=gas_price, value=value)
    logger.info("      Result: %s" % result)
    if wait:
        instance.wait_for_next_block(verbose=(True if config.get('misc', 'verbosity') > 1 else False))

def load_yaml(filename):
    logger.info("Loading %s..." % filename)
    f = open(filename)
    data = yaml.load(f)
    f.close()
    logger.debug(json.dumps(data, indent=4))

    return data

