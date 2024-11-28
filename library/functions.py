import json
import os


## General-Purpose Functions
## ========================================================================

## cmd
## ------------------------------------------------------------------------
def cmd(c):
	""" executes a system command """
	os.system(c)

## areEqualLists
## ------------------------------------------------------------------------
def areEqualLists(list1, list2):
	""" compares two lists for equal content """
	return set([x for x in list1 if x in list2]) == set(list2)

## mkfile
## ------------------------------------------------------------------------
def mkfile(path):
	""" creates an empty file """
	if os.path.exists(path): return
	cmd("touch "+path)

## mkdir
## ------------------------------------------------------------------------
def mkdir(path):
	""" creates an empty directory """
	if os.path.exists(path): return
	cmd("mkdir "+path)

## mv
## ------------------------------------------------------------------------
def mv(fr, to):
	""" moves a directory of file from a path to another path """
	if not os.path.exists(fr): return
	cmd("mv %s %s"%(fr, to))

## readJson
## ------------------------------------------------------------------------
def readJson(path):
	""" opens a JSON file and reads the data """
	f = open(path, "r", newline="")
	j = json.load(f)
	f.close()
	return j

## writeJson
## ------------------------------------------------------------------------
def writeJson(path, j):
	""" writes data into a JSON file """
	f = open(path, "w")
	json.dump(j, f)
	f.close()
	return True

