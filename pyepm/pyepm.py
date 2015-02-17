#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: caktux
# @Date:   2014-12-21 12:44:20
# @Last Modified by:   caktux
# @Last Modified time: 2015-02-17 18:04:31

import os
import json
import shutil
import config as c
import logging
import logging.config
import deploy
logger = logging.getLogger(__name__)

from utils import config_dir, configure_logging
from argparse import ArgumentParser

from . import __version__

def parse_arguments(parser):
    parser.add_argument(
        "-r", "--host",
        dest="host",
        help="<host>  JSONRPC host (default: 127.0.0.1).")
    parser.add_argument(
        "-p", "--port",
        dest="port",
        help="<port>  JSONRPC port (default: 8080).")
    parser.add_argument(
        "-a", "--address",
        dest="address",
        help="Set the address from which to deploy contracts.")
    parser.add_argument(
        "-g", "--gas",
        dest="gas",
        help="Set the default amount of gas for deployment.")
    parser.add_argument(
        "-c", "--config",
        dest="config",
        help="Use another configuration file.")
    parser.add_argument(
        "-V", "--verbose",
        dest="verbosity",
        help="<0 - 3> Set the log verbosity from 0 to 3 (default: 1)")
    parser.add_argument(
        "-L", "--logging",
        dest="logging",
        help="<logger1:LEVEL,logger2:LEVEL> set the console log level for"
        " logger1, logger2, etc. Empty loggername means root-logger,"
        " e.g. ':DEBUG,:INFO'. Overrides '-V'")
    parser.add_argument(
        "filename",
        nargs='+',
        help="Package definition filenames in YAML format")

    return parser.parse_args()


def create_config(parser):
    options = parse_arguments(parser)

    # 1) read the default config at "~/.pyepm"
    config = c.read_config()

    # 2) read config from file
    cfg_fn = getattr(options, 'config')
    if cfg_fn:
        if not os.path.exists(cfg_fn):
            c.read_config(cfg_fn)  # creates default
        config.read(cfg_fn)

    # 3) apply cmd line options to config
    for section in config.sections():
        for a, v in config.items(section):
            if getattr(options, a, None) is not None:
                config.set(section, a, getattr(options, a))

    # set config_dir
    config_dir.set(config.get('misc', 'config_dir'))

    return config


def main():
    config = c.get_default_config()
    parser = ArgumentParser(version=__version__)

    config = create_config(parser)

    # Logging
    configure_logging(config.get('misc', 'logging') or '',

    verbosity=config.getint('misc', 'verbosity'))
    logger.info('PyEPM %s', __version__)
    logger.info('=====')

    logger.debug(c.dump_config(config))

    args = parser.parse_args()

    for filename in args.filename:
        if not os.path.exists(filename):
            logger.warn("File does not exist: %s" % filename)
        else:
            logger.info("Deploying %s..." % filename)
            deployment = deploy.Deploy(filename, config)
            deployment.deploy()


if __name__ == '__main__':
    main()
