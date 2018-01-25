import os
import struct

from binascii import hexlify

from utxo.chainstate import ldb_iter
from utxo.script import unwitness
from utxo.util import new_utxo_file
from utxo.b128 import decompress_amount

def snap_utxos(bitcoind, bitcoind_datadir, stop_block):

    cmd = "{} -reindex-chainstate -datadir={} -stopatheight={}".format(
        bitcoind, bitcoind_datadir, stop_block)
    print("running " + cmd)
    os.system(cmd)


def dump_utxos(datadir, output_dir, n, convert_segwit, maxT=0, debug=True, prefix='new'):
    if prefix == 'old':
        prefix = b'c'
    else:
        prefix = b'C'

    i = 0
    k = 0

    f = new_utxo_file(output_dir, k)
    print "Created k=0 file"
    for value in ldb_iter(datadir, prefix):
	print "Found iter value"

        tx_hash, height, index, amt, script = value
        if convert_segwit:
	    print "unwitnessing"
            script = unwitness(script, debug)

        amount =  "%d.%08d" %  (amt / 100000000 , amt % 100000000 )
        if debug:
            print("{},{},{},{},{}".format( height,
                    hexlify(tx_hash[::-1]), index, amount, hexlify(script)
            ))

        f.write(struct.pack('<QQ', amt, len(script)))
        f.write(script)
        f.write('\n')

        i += 1
        if i % n == 0:
            f.close()

            k += 1
            print('new file: {}'.format(k))
            f = new_utxo_file(output_dir, k)

        if maxT != 0 and i >= maxT:
            break

    f.close()
    print "Finished dumping UTXOs"
