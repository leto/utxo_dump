#!/usr/bin/env python

from argparse import ArgumentParser
from os.path import isfile, isdir
from utxo.util import read_utxos, utxo_file_name

parser = ArgumentParser()
parser.add_argument('utxo_dir')
parser.add_argument('--filenum', type=int)
args = parser.parse_args()

utxo_dir = args.utxo_dir
filenum = args.filenum
total_amount = 0
assert isdir(utxo_dir)

if filenum is not None:
    total_amount = read_utxos(utxo_dir, filenum)
else:
    i = 0
    while isfile(utxo_file_name(utxo_dir, i)):
        total_amount += read_utxos(utxo_dir, i)
        i += 1

amount        =  "%d.%08d" %  (total_amount / 100000000 , total_amount % 100000000 )
print amount
