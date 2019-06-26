# SmartContractLinearizer
For the error 'Linearization of inheritance graph impossible'. Worked on my repo, might work on yours ¯\\\_(ツ)_/¯.

It will read through a list of input solidity contracts and create a linearized dependency list. Use this ordering throughout your contracts.

It will also output contract definitions with dependency list for each input file.

# Usage
```
python3 linearize.py <globbing pattern>
```

# Example Usage
```
python3 linearize.py '*.sol' 
python3 linearize.py '**/*.sol' 
```

# Example Output
```
--LINEARIZED DEPENDENCY LIST--
B (descendants=0),
C (descendants=0),
A (descendants=2)

contract A is
  B,
  C
```
