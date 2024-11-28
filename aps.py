import argparse
import os 
import sys

from library.kernel import Aps

base   = os.path.dirname(os.path.realpath(__file__))

parser = argparse.ArgumentParser(description='Approximate Problem Solver.')
parser.add_argument('path', metavar='path', type=str,
                    help='path to a valid json input file')
parser.add_argument('-b'  , metavar='base', type=str, default=base,
                    help='path to the base directory')
args = parser.parse_args()

if not os.path.exists("%s/%s"%(args.b, args.path)): 
	print("ERROR: Give a valid input JSON file!")
	sys.exit()

x = Aps("aps", args.b)
x.load (args.path)
x.do   ()
x.close()

