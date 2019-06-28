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

pathPattern = sys.argv[1]

# populate <contracts> / <contractDependencies> / <dependentContracts>
pathlist = Path("./").glob(pathPattern)
for path in pathlist:
    # because path is object not string
    pathStr = str(path)
    f = open(pathStr)
    foundContractDefinition = False
    inImportSection = False
    for line in f:
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

        elif inImportSection:
            if re.search('^{$', line):
                inImportSection = False
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
    print('contract %s is'%contractName)
    numDependenciesFound = 0
    numDependenciesToFind = len(descendants[contractName])
    for dependencyName in linearizedDependencyList:
        if dependencyName in descendants[contractName]:
            numDependenciesFound += 1
            if numDependenciesFound == numDependenciesToFind:
                print('    %s'%dependencyName)
            else:
                print('    %s,'%dependencyName)
    print()
print()
            