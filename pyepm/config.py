#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Author: caktux
# @Date:   2014-12-21 12:44:20
# @Last Modified by:   caktux
# @Last Modified time: 2014-12-22 00:34:32

import os
import uuid
import StringIO
import ConfigParser
from utils import config_dir

def default_config_dir():
    config_dir._set_default()
    return config_dir.path

def default_config_path():
    return os.path.join(default_config_dir(), 'config')


config_template = \
"""
[api]
# JSONRPC host and port
host = 127.0.0.1
port = 8080
address = cd2a3d9f938e13cd947ec05abc7fe734df8dd826

[deploy]
gas = 10000
gas_price = 10000000000000

[misc]
config_dir = {0}
verbosity = 1

# :INFO, :WARN, :DEBUG, pyepm.deploy:DEBUG ...
logging = :INFO
""".format(default_config_dir())


def get_default_config():
    f = StringIO.StringIO()
    f.write(config_template)
    f.seek(0)
    config = ConfigParser.ConfigParser()
    config.readfp(f)
    return config

def read_config(cfg_path=default_config_path()):
    # create default if not existent
    if not os.path.exists(cfg_path):
        open(cfg_path, 'w').write(config_template)
    # extend on the default config
    config = get_default_config()
    config.read(cfg_path)
    return config

def dump_config(config):
    r = ['']
    for section in config.sections():
        for a, v in config.items(section):
            r.append('[%s] %s = %r' % (section, a, v))
    return '\n'.join(r)
