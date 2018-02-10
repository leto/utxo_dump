# UTXO Dumper

This talks directly to the internal Bitcoin LevelDB to dump UTXO data, using Python.

# Install

	sudo apt-get install libleveldb-dev
	pip install -r requirements.txt

# Example

Sync your bitcoin-compatible daemon to the block height that is wanted and then
shut down the server, since LevelDB does not allow multiple applications to connect at the same time:

This tools looks at the LevelDB chainstate index, which has an index of UTXOs for each transaction id (txid).

./dump.py ~/.bitcoin ~/utxos/ --verbose=True 
