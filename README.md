# SmartContractLinearizer
For the error 'Linearization of inheritance graph impossible'. Worked on my repo, might work on yours ¯\\\_(ツ)_/¯.

It will read through a list of input solidity contracts and create a linearized dependency list.

If you include `--fix-contracts` then it will also update your contracts - THIS SCRIPT IS IN BETA - backup your work first.

If you do not incldue `--fix-contracts` then it will output the fixed contract definitions for to apply manually.

# Usage
```
python3 linearize.py <globbing pattern>
```

# Example Usage
```
python3 linearize.py '*.sol' 
python3 linearize.py '**/*.sol' 
```

# Example Outputs
```
$ python3 linearize.py '*.sol'

--LINEARIZED DEPENDENCY LIST--
B (descendants=0),
C (descendants=0),
A (descendants=2)

contract A is
  B,
  C
```

```
$ python3 linearize.py '*.sol' --fix-contracts

--LINEARIZED DEPENDENCY LIST--
B (descendants=0),
C (descendants=0),
A (descendants=2)

***** Fixing A.sol *****
***** Fixing B.sol *****
***** Fixing C.sol *****
```
