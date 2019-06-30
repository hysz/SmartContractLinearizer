# SmartContractLinearizer
For the error 'Linearization of inheritance graph impossible'. Worked on my repo, might work on yours ¯\\\_(ツ)_/¯.

It will read through a list of input solidity contracts and create a linearized dependency list.

If you include `--fix then it will also update your contracts - THIS SCRIPT IS IN BETA - backup your work first.

If you do not incldue `--fix` then it will output the fixed contract definitions for to apply manually.

# Usage
```
usage: linearize.py [-h] [--path PATH] [--glob GLOB] [--fix]

Linearize solidity smart contracts.

optional arguments:
  -h, --help   show this help message and exit
  --path PATH  directory with smart contracts; defaults to current directory.
  --glob GLOB  globbing pattern to find contracts within `--path`; defaults
               finding all files with extension '*.sol'
  --fix        include to fix contracts (backup your contracts first! #inbeta)
```

# Example Usage
```
linearize.py --path ./contracts --glob '**/*.sol' --fix
```

# Example Outputs
```
$ linearize.py --glob '*.sol'

--LINEARIZED DEPENDENCY LIST--
B (descendants=0),
C (descendants=0),
A (descendants=2)

contract A is
  B,
  C
```

```
$ linearize.py --glob '*.sol' --fix

--LINEARIZED DEPENDENCY LIST--
B (descendants=0),
C (descendants=0),
A (descendants=2)

***** Fixing A.sol *****
***** Fixing B.sol *****
***** Fixing C.sol *****
```
