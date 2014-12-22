PyEPM
==========

Python-based EPM (Ethereum Package Manager) for Serpent 2 contract deployment using YAML for package definitions.


## Installation
`pip install pyepm`

#### Development
```
git clone https://github.com/etherex/pyepm.git
cd pyepm
pip install -e .
```

## Requirements
[cpp-ethereum](https://github.com/ethereum/cpp-ethereum) node with JSONRPC

## Configuration

First run `pyepm -h` to create a config file in `~/.pyepm/config` on Linux and OSX and `~/AppData/Roaming/PyEPM` on Windows.

Then edit the configuration file, make sure you set the `address` from which to deploy contracts.

You will need a package definition file in YAML format to get started:
```
-
# Set some variables.
  set:
    NameReg: "0x72ba7d8e73fe8eb666ea66babc8116a41bfb10e2"
-
# Deploy contracts
  deploy:
    NameCoin:
      contract: namecoin.se
      wait: True
    Subcurrency:
      contract: subcurrency.se
      gas: 100000
      endowment: 1000000000000000000
-
# Make transactions
  transact:
    NameReg:
      to: $NameReg
      value: 0
      data: "register" "caktux"
      gas: 10000
      gas_price: 10000000000000
      wait: True
-
# Another deploy
  deploy:
    extra:
      contract: short_namecoin.se
```

## Usage

`pyepm YourPackageDefinitions.yaml`

```
usage: pyepm [-h] [-v] [-r HOST] [-p PORT] [-a ADDRESS] [-g GAS] [-c CONFIG]
             [-V VERBOSITY] [-L LOGGING]
             filename [filename ...]

positional arguments:
  filename              Package definition filenames in YAML format

optional arguments:
  -h, --help            show this help message and exit
  -v, --version         show program's version number and exit
  -r HOST, --host HOST  <host> JSONRPC host (default: 127.0.0.1).
  -p PORT, --port PORT  <port> JSONRPC port (default: 8080).
  -a ADDRESS, --address ADDRESS
                        Set the address from which to deploy contracts.
  -g GAS, --gas GAS     Set the default amount of gas for deployment.
  -c CONFIG, --config CONFIG
                        Use another configuration file.
  -V VERBOSITY, --verbose VERBOSITY
                        <0 - 3> Set the log verbosity from 0 to 3 (default: 1)
  -L LOGGING, --logging LOGGING
                        <logger1:LEVEL,logger2:LEVEL> set the console log
                        level for logger1, logger2, etc. Empty loggername
                        means root-logger, e.g. ':DEBUG,:INFO'. Overrides '-V'
```

## TODO
- ***Transact not implemented yet***
- ***Variables from "set" steps***
- Endowments
- Support named values (1 ether)
