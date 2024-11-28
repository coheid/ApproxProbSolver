import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")))
from library.functions import readJson

jscm = readJson("cache/aps/scm.json")
jicm = readJson("cache/aps/icm.json")
jint = readJson("cache/aps/int.json")
jlct = readJson("cache/aps/lct.json")

icms = {}
for entry in jicm:
	for name,icm in entry.items():
		icms[name] = icm["conceptual"]

ints = {}
for entry in jint:
	for name,eint in entry.items():
		ints[name] = eint["moves"]

lcts = {}
for entry in jlct:
	for name,lct in entry.items():
		lcts[name] = "%s --(%s %s)--> %s"%(lct["slotin"], lct["handle"].ljust(5), lct["movable"].ljust(5), lct["slotout"])


for entry in jscm:
	for name,scm in entry.items():
		print("")
		print("Solution",name)
		ctr = 0
		for icm in scm["moves"]:
			for imv in icms[icm]:
				for lct in ints[imv]:
					print(lcts[lct])
					ctr += 1
		print("(",ctr,"moves)")
		print("")
		print("-"*15)
