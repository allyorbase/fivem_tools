#!/bin/python3
import json
import random
    
with open("locations.json") as f:
    locs = json.loads(f.read())

with open("peds.json") as f:
    peds = json.loads(f.read())


#for ped in peds:
#    rand = random.randrange(0,len(locs)+1)
#    print("spawnpoint '{}' {{ x = {}, y = {}, z = {} }}".format(ped, locs['teleports'][rand]['coordinates']['X'], locs['teleports'][rand]['coordinates']['Y'], locs['teleports'][rand]['coordinates']['Z']))

for loc in locs['teleports']:
    rand = random.randrange(0, len(peds))
    print("spawnpoint '{}' {{ x = {}, y = {}, z = {} }}".format(peds[rand], loc['coordinates']['X'], loc['coordinates']['Y'], loc['coordinates']['Z']))
        
