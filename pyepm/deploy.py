#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: caktux
# @Date:   2014-12-21 12:44:20
# @Last Modified by:   caktux
# @Last Modified time: 2014-12-22 00:48:24

import logging

import api
import json
import yaml
import config as c
config = c.read_config()

logger = logging.getLogger(__name__)

from serpent import compile

def deploy(filename, gas=config.get('deploy', 'gas'), gas_price=config.get('deploy', 'gas_price'), endowment=0, wait=False):
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
                    variables[name] = definition[key][name]
                    logger.info("  %s: %s" % (name, definition[key][name]))

            if key == 'deploy':
                for name in definition[key]:
                    for option in definition[key][name]:
                        if option == 'contract':
                            contract = definition[key][name][option]
                        if option == 'gas':
                            gas = definition[key][name][option]
                        if option == 'gas_price':
                            gas_price = definition[key][name][option]
                        if option == 'endowment':
                            endowment = definition[key][name][option]
                        if option == 'wait':
                            wait = definition[key][name][option]
                    logger.info("    Deploying %s..." % contract)
                    create(contract, gas, gas_price, endowment, wait)


def create(contract, gas, gas_price, endowment, wait):
    instance = api.Api()
    contract = compile(open(contract).read()).encode('hex')
    contract_address = instance.create(contract)
    logger.info("      Contract is available at %s" % contract_address)
    if wait:
        instance.wait_for_next_block(verbose=True)


def load_yaml(filename):
    logger.info("Loading %s..." % filename)
    f = open(filename)
    data = yaml.load(f)
    f.close()
    logger.debug(json.dumps(data, indent=4))

    return data

