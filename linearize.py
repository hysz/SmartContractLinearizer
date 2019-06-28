#!/usr/bin/env python3

from pathlib import Path
import re
import pprint
import sys

# list of contracts to process (derived from input globbing pattern)
contractsToProcess = []
# list of all contracts
contracts = []
# maps contract -> dependencies of contract (the contract depends on each element)
contractDependencies = {}
# maps contract -> dependent contracts (contracts who depend on the key)
dependentContracts = {}
# maps contract -> contracts higher up in family tree (parents, grandparents, etc)
ancestors = {}
# maps contract -> contracts lower down in family tree (parents, grandparents, etc)
descendants = {}
# linearized dependentContracts (this is what we're trying to build!)
linearizedDependencyList = []
# line numbers that define the smart contract; these will be repladced fixed contract definition.
contractData = {}

pathPattern = sys.argv[1]
fixContracts = len(sys.argv) > 2 and sys.argv[2] == '--fix-contracts'

# populate <contracts> / <contractDependencies> / <dependentContracts>
pathlist = Path("./").glob(pathPattern)
for path in pathlist:
    # because path is object not string
    pathStr = str(path)
    f = open(pathStr)
    foundContractDefinition = False
    inImportSection = False
    for lineNumber,line in enumerate(f):
        if re.search('^library .* [ ]*$', line) or re.search('^interface .* is[ ]*$', line):
            break
        elif re.search('^contract .* is[ ]*$', line):
            foundContractDefinition = True
            inImportSection = True
            contractName = line.split()[1]
            print('Processing contract %s'%contractName)
            contractDependencies[contractName] = []
            # add contract to lists of contracts
            contractsToProcess.append(contractName)
            if not contractName in contracts:
                contracts.append(contractName)
            if not contractName in dependentContracts:
                dependentContracts[contractName] = []
            # store contract data
            contractData[contractName] = {}
            contractData[contractName]["path"] = pathStr
            contractData[contractName]["startLine"] = lineNumber
            contractData[contractName]["endLine"] = -1

        elif inImportSection:
            if re.search('^{$', line):
                inImportSection = False
                contractData[contractName]["endLine"] = lineNumber - 1
                continue
            elif re.search('//', line):
                # skip comment
                continue
            dependencyName = re.sub(',|\n| ', '', line)
            contractDependencies[contractName].append(dependencyName)
            if not dependencyName in dependentContracts:
                dependentContracts[dependencyName] = []
            dependentContracts[dependencyName].append(contractName) 
            
            # add dependency to list of contracts
            if not dependencyName in contracts:
                contracts.append(dependencyName)

    if foundContractDefinition == False:
        print('no dependencies found in %s'%pathStr)

print()
# pprint.pprint(dependentContracts)

# populate <ancestors>
def populateAncestors(rootContractName, currentContractName):
    for dependent in dependentContracts[currentContractName]:
        if not dependent in ancestors[rootContractName]:
            ancestors[rootContractName].append(dependent)
        populateAncestors(rootContractName, dependent)

for contractName in contracts:
    ancestors[contractName] = []
    populateAncestors(contractName, contractName)

# pprint.pprint(ancestors)

# populate <descendants>
def populateDescendants(rootContractName, currentContractName):
    if not currentContractName in contractDependencies:
        # No dependencies for this contract
        return

    for dependency in contractDependencies[currentContractName]:
        if not dependency in descendants[rootContractName]:
            descendants[rootContractName].append(dependency)
        populateDescendants(rootContractName, dependency)

for contractName in contracts:
    descendants[contractName] = []
    populateDescendants(contractName, contractName)

#print('-- DESCENDANTS -- ')
#pprint.pprint(descendants)

# get list of contracts in alphabetical order with least..most descendants ("most base-like" to "most-derived")
# note - the alphabetization means that interfaces (IFoobar.sol) will be ordered first
descendantsAsListSortedAlpha = sorted(descendants.items())
descendantsAsListSortedByLeastDescendants = sorted(descendantsAsListSortedAlpha, key=lambda item: len(item[1]))
contractsSortedByLeastDescendants = [x[0] for x in descendantsAsListSortedByLeastDescendants]

#print('-- SORTED INPUT -- ')
#for contractName in contractsSortedByLeastDescendants:
#    print('%s %d,'%(contractName,len(descendants[contractName])))

# build linearized dependency list
def isLinearized(dependencyList):
    # each contract must not be an ancestor of contracts listed after it
    for i, contractName in enumerate(dependencyList):
        j = i + 1
        while j < len(dependencyList):
            if contractName in ancestors[dependencyList[j]]:
                return False
            j += 1
    return True

# we go through the list of contracts that are sorted alphabetically / least..most descendants ("most base-like" to "most-derived").
# we try to place each element as early in the output list as possible.
# we end up with ordering: alphabetically / least..most descendants / linearized
# we iterate with the invariant that <currentList> is always linearized.
def createList(contractNameIdx, contractList, currentList):
    # base case
    if contractNameIdx == len(contractsSortedByLeastDescendants):
        return True

    # try to insert
    contractName = contractList[contractNameIdx]
    insertedAtIdx = -99
    iteratorRange = range(len(currentList), -1 , -1)
    for i in iteratorRange:
        currentList.insert(i, contractName)
        if isLinearized(currentList):
            if createList(contractNameIdx + 1, contractList, currentList):
                insertedAtIdx = i
                break  
        currentList.pop(i)

    return insertedAtIdx != -99

createList(0, contractsSortedByLeastDescendants, linearizedDependencyList)    

print('--LINEARIZED DEPENDENCY LIST--')
for i,dependencyName in enumerate(linearizedDependencyList):
    if i < len(linearizedDependencyList) - 1:
        print('%s (descendants=%d),'%(dependencyName,len(descendants[dependencyName])))
    else:
        print('%s (descendants=%d)'%(dependencyName,len(descendants[dependencyName])))
print()

# print out fixed contract headers
print('--CONTRACT DEFINITIONS FOR CONTRACTS WE PROCESSED--')
# Note that we construct the dependency list using the *entire* list of decscendants.
# This removes any ambiguity caused by implicitly inheriting members.
# Ex:
# contract A {}
# contract B {}
# contract C {}
# contract D is A, B {}
#
# Suppose now that contract E will inherit from B{} and D{}
# The following follows "most base-like" to "most-derived":
#   contract E is B, D {}
# However, it unfolds to: B{}, A{}, B{}, D{}, E{} - which is wrong because B{} appears twice.
# The contract inheritance for E{} is:
#   contract E is A{}, B{}, D{}
# 
# So, even though contract E{} does not directly depend on A{} - it still must be included in the dependency list
# Because of this, we include all descendants in the output.
for contractName in contractsToProcess:
    # open contract & read lines
    _contractData = contractData[contractName]
    f = open(_contractData["path"], 'r+')
    contractContents = f.readlines()
    contractPreamble = contractContents[0 : _contractData["startLine"] + 1]
    conractImplementation = contractContents[_contractData["endLine"] + 1:]
    contractDependenciesInSolidity = []

    # remove lines with existing, incorrect definitin.
    del contractContents[_contractData["startLine"] : _contractData["endLine"] - 1]

    numDependenciesFound = 0
    currentLineIndex = _contractData["startLine"]
    numDependenciesToFind = len(descendants[contractName])
    for dependencyName in linearizedDependencyList:
        if dependencyName in descendants[contractName]:
            numDependenciesFound += 1
            dependencyStr = ""
            if numDependenciesFound < numDependenciesToFind:
                dependencyStr = '    %s,\n'%dependencyName
            else:
                dependencyStr = '    %s\n'%dependencyName

            # add dependency to contract contents
            contractDependenciesInSolidity.append(dependencyStr)

    # update contract contents
    if fixContracts == True:
        print("***** Fixing %s *****"%contractData[contractName]["path"])
        updatedContractContents = contractPreamble + contractDependenciesInSolidity + conractImplementation
        f.seek(0)
        f.writelines(updatedContractContents) # no truncation bc length is >= original
    else:
        print("contract %s is"%contractName)
        for line in contractDependenciesInSolidity:
                print(line, end="")
        print()
    f.close()
            