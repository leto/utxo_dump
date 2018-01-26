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

    for value in ldb_iter(datadir, prefix):
        if prefix == b'C':
            tx_hash, height, index, amt, script = value
            amount =  "%d.%08d" %  (amt / 100000000 , amt % 100000000 )
            #if debug:
            #    print("{},{},{},{},{}".format( height,
            #            hexlify(tx_hash[::-1]), index, amount, hexlify(script)
            #    ))

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
        else:
            height, outs = value
            #print "outs=" + str(outs)
            for j in range(0,len(outs)):
                index, amt, out_type, script = outs[j]
                if convert_segwit:
                    script = unwitness(script, debug)
                f.write(struct.pack('<QQ', amt, len(script)))
                f.write(script)
                f.write('\n')

                amount =  "%d.%08d" %  (amt / 100000000 , amt % 100000000 )
                if debug:
                    print("{},{},{},{}".format( height, index, amount, hexlify(script)))

                i += 1
                if i % n == 0:
                    f.close()

                    k += 1
                    print('new file: {}'.format(k))
                    f = new_utxo_file(output_dir, k)

            if maxT != 0 and i >= maxT:
                break
        #exit()


    print "Finished dumping " + str(i) + " UTXOs"
    f.close()
