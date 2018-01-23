#!/usr/bin/perl

use strict;
use warnings;
no warnings 'experimental';
use JSON;
use Data::Dumper;

my $ignored = 0;
sub taddr_of_utxo {
	my ($utxo)  = @_;
	my $bitcoin = "$ENV{HOME}/git/bitcoin/src/bitcoin-cli";
	my $json    = qx{$bitcoin decodescript $utxo};
	my $data    = decode_json($json);
	my $taddr;

	# be generous
	if ($data->{p2sh}) {
		$taddr = $data->{p2sh};
	}
	return $taddr;
}

while (<>) {
        my ($type,$amount,$taddr,$utxo) = split ",";
	chomp $utxo;
	unless ($taddr) {
		$taddr = taddr_of_utxo($utxo);
		print "$type,$amount,$taddr,$utxo\n";
	}
}
warn "Ignored $ignored";
