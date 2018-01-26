import b128
import itertools
import os
import plyvel
import secp256k1

from binascii import unhexlify, hexlify
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

        if ldb_prefix == b'C':
            return parse_ldb_value(key, value)
        else:
            return parse_old_ldb_value(key,value)

    it = db.iterator(prefix=ldb_prefix)
    print "prefix=" + ldb_prefix
    return itertools.imap(norm, it)


def parse_old_ldb_value(key, utxo):
    "Extract UTXOs from 0.8-0.14.x"
    # Version is extracted from the first varint of the serialized utxo
    version, offset = b128.parse(utxo)

    # The next MSB base 128 varint is parsed to extract both is the utxo is coin base (first bit) and which of the
    # outputs are not spent.
    code, offset = b128.parse(utxo, offset)
    coinbase = code & 0x01

    # Check if the first two outputs are spent
    vout = [(code | 0x01) & 0x02, (code | 0x01) & 0x04]

    # The higher bits of the current byte (from the fourth onwards) encode n, the number of non-zero bytes of
    # the following bitvector. If both vout[0] and vout[1] are spent (v[0] = v[1] = 0) then the higher bits encodes n-1,
    # since there should be at least one non-spent output.
    if not vout[0] and not vout[1]:
        n = (code >> 3) + 1
        vout = []
    else:
        n = code >> 3
        vout = [i for i in xrange(len(vout)) if vout[i] is not 0]

    # If n is set, the encoded value contains a bitvector. The following bytes are parsed until n non-zero bytes have
    # been extracted. (If a 00 is found, the parsing continues but n is not decreased)
    if n > 0:
        bitvector = ""
        while n:
            data = utxo[offset:offset+1]
            if data != b'0':
                n -= 1
            bitvector += data
            offset += 1

        bitvector = hexlify(bitvector)
        print "bitvector=" + bitvector
        # Once the value is parsed, the endianness of the value is switched from LE to BE and the binary representation
        # of the value is checked to identify the non-spent output indexes.
        print "len(bitvector) = " + str(len(bitvector))
        bin_data = format(int(change_endianness(bitvector), 16), '0'+str(n*8)+'b')[::-1]
        print "bin_data=" + str(bin_data)
        print "len(bin_data) = " + str(len(bin_data))
        bin_data = unhexlify(bin_data)
        print "unhex bin_data=" + str(bin_data)

        # Every position (i) with a 1 encodes the index of a non-spent output as i+2, since the two first outs (v[0] and
        # v[1] has been already counted)
        # (e.g: 0440 (LE) = 4004 (BE) = 0100 0000 0000 0100. It encodes outs 4 (i+2 = 2+2) and 16 (i+2 = 14+2).
        extended_vout = [i+2 for i in xrange(len(bin_data))
                         if bin_data.find('1', i) == i]  # Finds the index of '1's and adds 2.

        # Finally, the first two vouts are included to the list (if they are non-spent).
        vout += extended_vout

    print hexlify(utxo)

    # Once the number of outs and their index is known, they could be parsed.
    outs = []
    print "iterating vouts"
    for i in vout:
        print i, vout[i]
        # The satoshi amount is parsed, decoded and decompressed.
        amount, offset  = b128.parse(utxo, offset)
        amount          = b128.decompress_amount(amount)
        # The output type is also parsed.
        out_type, offset = b128.parse(utxo, offset)
        # Depending on the type, the length of the following data will differ.  Types 0 and 1 refers to P2PKH and P2SH
        # encoded outputs. They are always followed 20 bytes of data, corresponding to the hash160 of the address (in
        # P2PKH outputs) or to the scriptHash (in P2PKH). Notice that the leading and tailing opcodes are not included.
        # If 2-5 is found, the following bytes encode a public key. The first byte in this case should be also included,
        # since it determines the format of the key.
        if out_type in [0, 1]:
            data_size = 20  # 20 bytes
        elif out_type in [2, 3, 4, 5]:
            data_size = 33  # 33 bytes (1 byte for the type + 32 bytes of data)
            offset   -= 1
        # Finally, if another value is found, it represents the length of the following data, which is uncompressed.
        else:
            data_size = (out_type - NSPECIALSCRIPTS) * 2  # If the data is not compacted, the out_type corresponds
            # to the data size adding the number of special scripts (nSpecialScripts).

        # And finally the address (the hash160 of the public key actually)
        script, offset = utxo[offset:offset+data_size], offset + data_size
        parsed_utxo = [i, amount, out_type,  script]
        outs.append( parsed_utxo )

    # Once all the outs are processed, the block height is parsed
    height, offset = b128.parse(utxo, offset)

    return height, outs


# from bitcoin_tools
def change_endianness(x):
    """ Changes the endianness (from BE to LE and vice versa) of a given value.

    :param x: Given value which endianness will be changed.
    :type x: hex str
    :return: The opposite endianness representation of the given value.
    :rtype: hex str
    """
    # If there is an odd number of elements, we make it even by adding a 0
    if (len(x) % 2) == 1:
        x += "0"
    y = x.decode('hex')
    z = y[::-1]
    return z.encode('hex')

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
