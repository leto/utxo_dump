import b128
import itertools
import os
import plyvel
import secp256k1

from binascii import unhexlify
from utxo.script import OP_DUP, OP_HASH160, OP_EQUAL, \
    OP_EQUALVERIFY, OP_CHECKSIG


def ldb_iter(datadir, ldb_prefix):
    db = plyvel.DB(os.path.join(datadir, "chainstate"), compression=None)

    # Load obfuscation key (if it exists)
    o_key = db.get((unhexlify("0e00") + "obfuscate_key"))

    # If the key exists, the leading byte indicates the length of the key (8 byte by default). If there is no key,
    # 8-byte zeros are used (since the key will be XORed with the given values).
    if o_key is not None:
        o_key = o_key[2:]

    def norm(raw):
        key, value = raw
	if o_key is not None:
	    value = deobfuscate(o_key, value)

        return parse_ldb_value(key, value)

    it = db.iterator(prefix=ldb_prefix)
    print "prefix=" + ldb_prefix
    return itertools.imap(norm, it)


def parse_ldb_value(key, raw):
    tx_hash = key[1:33]

    index = b128.parse(key[33:])[0]

    code, raw = b128.read(raw)
    height = code >> 1

    amt_comp, raw = b128.read(raw)
    amt = b128.decompress_amount(amt_comp)

    script_code, raw = b128.read(raw)
    script = decompress_raw(script_code, raw)

    return tx_hash, height, index, amt, script


def decompress_raw(comp_type, data):

    if comp_type == 0:
        assert len(data) == 20
        return OP_DUP + OP_HASH160 + chr(20) + data + \
            OP_EQUALVERIFY + OP_CHECKSIG

    elif comp_type == 1:
        assert len(data) == 20
        return OP_HASH160 + chr(20) + data + OP_EQUAL

    elif comp_type == 2 or comp_type == 3:
        assert len(data) == 32

        return chr(33) + chr(comp_type) + data + OP_CHECKSIG

    elif comp_type == 4 or comp_type == 5:
        assert len(data) == 32

        comp_pubkey = chr(comp_type - 2) + data
        pubkey = secp256k1.PublicKey(
            comp_pubkey, raw=True
        ).serialize(compressed=False)

        return chr(65) + pubkey + OP_CHECKSIG

    else:
        assert len(data) == comp_type - 6
        return data


def deobfuscate(key, obf):
    n = len(key)
    de = [chr(key[i % n] ^ ord(b)) for i, b in enumerate(obf)]

    return "".join(de)
