import json
import argparse
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")))
from library.functions import readJson, writeJson

parser = argparse.ArgumentParser(description='Approximate Problem Solver.')
parser.add_argument('path', metavar='path', type=str,
                    help='path to a valid json input file')
args = parser.parse_args()

## load json
j = readJson(args.path)
channels = ("hand", "boat")

## generate valid move combinations
num   = 1
moves = []
for handle in j["handles"]:

	## object-based moves
	if handle["modulate"] == "object":

		for obj in j["task"]["objects"]:
			for slotin in j["task"]["slots"]:
				if handle["initial"]     in channels and slotin["name"] not in channels   : continue
				if handle["initial"] not in channels and slotin["type"]!=handle["initial"]: continue

				for slotout in j["task"]["slots"]:
					if handle["final"]     in channels and slotout["name"] not in channels : continue
					if handle["final"] not in channels and slotout["type"]!=handle["final"]: continue
					if slotout["name"]==slotin["name"]: continue

					name  = "lct_%03d"%num
					props = {"name": name, "handle": handle["name"], "slotin": slotin["name"], "movable": obj["name"], "slotout": slotout["name"]}
					move  = {name: props}
					moves.append(move)
					num += 1

	## slot-based moves
	if handle["modulate"] in channels:
		for slotin in j["task"]["slots"]:
			if slotin["type"]!=handle["initial"]: continue

			for slotout in j["task"]["slots"]:
				if slotout["type"]!=handle["final"]: continue
				if slotout["name"]==slotin["name"]: continue

				name  = "lct_%03d"%num
				props = {"name": name, "handle": handle["name"], "slotin": slotin["name"], "movable": handle["modulate"], "slotout": slotout["name"]}
				move  = {name: props}
				moves.append(move)
				num += 1

## write output JSON file
writeJson("lctAll.json", moves)

