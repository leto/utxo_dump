import hashlib
import os
import struct

from binascii import hexlify
from utxo.b128 import decompress_amount


def utxo_file_name(directory, i):
    return os.path.join(directory, "utxo_{:06}.bin".format(i))


def read_utxos(directory, i):
    name = utxo_file_name(directory, i)
    f = open(name, 'rb')
    read_utxo_file(f)
    f.close()


def read_utxo_file(f):
    head = f.read(16)
    while head != "":
        amt, sz = struct.unpack('<QQ', head)
        script = f.read(sz)

        assert f.read(1) == '\n'
        amount =  "%d.%08d" %  (amt / 100000000 , amt % 100000000 )
        print("{},{}".format(amount, hexlify(script)))
        head = f.read(16)


def new_utxo_file(output_dir, k):
    p = utxo_file_name(output_dir, k)
    return open(p, "wb")


def ripemd160(st):
    r = hashlib.new('ripemd160')
    r.update(st)
    return r.digest()
