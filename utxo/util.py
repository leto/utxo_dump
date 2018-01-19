import hashlib
import os
import struct
import base58
import secp256k1

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
        amount     =  "%d.%08d" %  (amt / 100000000 , amt % 100000000 )
        data       = hexlify(script)

        if data[0:4]==b'76a9':
            # P2PKH
            num_bytes  = script[2]
            public_key = script[3:23]
            z          = b'\00'+public_key
            z          = base58.b58encode_check(z)
            #print("p2pkh,{},{},{}".format(amount, z, hexlify(script)))
        elif data[0:2] == b'a9':
            # P2SH
            num_bytes  = script[1]
            public_key = script[2:22]
            z          = b'\05'+public_key
            z          = base58.b58encode_check(z)
            #print("p2sh,{},{},{}".format(amount, z, hexlify(script)))
        elif data[0:2] == b'51' and data[-2:] == b'ae':
            # CHECKMULTISIG
            public_key = script[2:22]
            z          = b'\00'+public_key
            z          = base58.b58encode_check(z)
            #print("multisig,{},{},{}".format(amount, z, hexlify(script)))
            #print("{},,{}".format(amount, hexlify(script)))
        elif data[-2:] == b'ac':
            print len(data), len(script)
            # P2PK 
            comp_type = 4
            if data[0:2] == b'41':
                offset = 64
            elif data[0:2] == b'21':
                comp_type = 5
                offset  = 32

            comp_pubkey = chr(comp_type - 2) + script[2:2+offset]
            print len(comp_pubkey)
            pubkey = secp256k1.PublicKey(
                comp_pubkey, raw=True
            ).serialize(compressed=False)

            # TODO: proper prefix?
            z          = b'\00'+pubkey
            z          = base58.b58encode_check(z)
            print("p2pk,{},{},{}".format(amount, z, hexlify(script)))
            #print("p2pk: {},,{}".format(amount, hexlify(script)))
        elif data[:4] == b'0014':
            print("P2WPKH,{},,{}".format(amount, hexlify(script)))
        elif data[:4] == b'0020':
            print("P2WSH,{},,{}".format(amount, hexlify(script)))
        elif data[:3] == b'160014':
            print("'P2WPKH embedded in P2SH',{},,{}".format(amount, hexlify(script)))
        elif data[:2] == b'a914' and data[-1] == b'\x87':
            print("'P2WSH embedded in P2SH',{},,{}".format(amount, hexlify(script)))
        else:
            print("unknown: {},,{}".format(amount, hexlify(script)))

        head = f.read(16)


def new_utxo_file(output_dir, k):
    p = utxo_file_name(output_dir, k)
    return open(p, "wb")


def ripemd160(st):
    r = hashlib.new('ripemd160')
    r.update(st)
    return r.digest()
