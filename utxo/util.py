import hashlib
import os
import struct
import base58
import secp256k1

from binascii import hexlify, unhexlify
from utxo.b128 import decompress_amount
from hashlib import sha256


def utxo_file_name(directory, i):
    return os.path.join(directory, "utxo_{:06}.bin".format(i))


def read_utxos(directory, i):
    name = utxo_file_name(directory, i)
    f = open(name, 'rb')
    total_amount = read_utxo_file(f)
    f.close()
    return total_amount


def read_utxo_file(f):
    head = f.read(16)
    total_amount = 0
    while head != "":
        amt, sz = struct.unpack('<QQ', head)
        script = f.read(sz)

        assert f.read(1) == '\n'
        amount        =  "%d.%08d" %  (amt / 100000000 , amt % 100000000 )
        total_amount += amt
        data          = hexlify(script)

        if data[0:4]==b'76a9':
            # P2PKH
            num_bytes  = script[2]
            public_key = script[3:23]
            z          = b'\00'+public_key
            z          = base58.b58encode_check(z)
            print("p2pkh,{},{},{}".format(amount, z, hexlify(script)))
        elif data[0:2] == b'a9':
            # P2SH
            num_bytes  = script[1]
            public_key = script[2:22]
            z          = b'\05'+public_key
            z          = base58.b58encode_check(z)
            print("p2sh,{},{},{}".format(amount, z, hexlify(script)))
        elif( data[0:1] == b'5') and data[-2:] == b'ae':
            #public_key = script[2:22]
            #z          = b'\00'+public_key
            #z          = base58.b58encode_check(z)
            #print("multisig,{},{},{}".format(amount, z, hexlify(script)))
            print("multisig,{},,{}".format(amount, hexlify(script)))
        elif data[-2:] == b'ac' and (data[0:2] == b'41' or data[0:2] == b'21'):
            #print len(data), len(script)
            # P2PK 
            if data[0:2] == b'41':
                offset = 65
            elif data[0:2] == b'21':
                offset  = 33
            
            pubkey = script[1:1+offset]
            #print hexlify(pubkey)
            #print len(pubkey)
            pubkeyhash = ripemd160(sha256(pubkey).digest())

            z          = '\00'+pubkeyhash
            z          = base58.b58encode_check(z)
            print("p2pk,{},{},{}".format(amount, z, hexlify(script)))
        elif data[:4] == b'0014':
            print("P2WPKH,{},,{}".format(amount, hexlify(script)))
        elif data[:4] == b'0020':
            print("P2WSH,{},,{}".format(amount, hexlify(script)))
        elif data[:3] == b'160014':
            print("P2WPKH_embedded,{},,{}".format(amount, hexlify(script)))
        elif data[:2] == b'a914' and data[-1] == b'\x87':
            print("P2WSH_embedded,{},,{}".format(amount, hexlify(script)))
        else:
            print("unknown,{},,{}".format(amount, hexlify(script)))

        head = f.read(16)
    return total_amount


def new_utxo_file(output_dir, k):
    p = utxo_file_name(output_dir, k)
    return open(p, "wb")

def ripemd160(st):
    r = hashlib.new('ripemd160')
    r.update(st)
    return r.digest()
