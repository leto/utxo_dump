#!/usr/bin/perl

use strict;
use warnings;
use Data::Dumper;

my %totals;
my %utxos;
my $utxos = 0;
my $total = 0;
my $avg   = 0;
my $total_length = 0;
my %taddrs;

while (<>) {
        my ($type,$amount,$taddr,$utxo) = split ",";
	$totals{$type} += $amount;
	$utxos{$type}++;
	$total         += $amount;
	$total_length  += length($utxo);
	if ($taddrs{$taddr}) {
		$taddrs{$taddr}++;
	} else {
		$taddrs{$taddr} = 1;
	}
	$utxos++;
}

while (my ($k,$v) = each %totals) {
	my $s = sprintf "%2.2f", $total > 0 ? (100* $v / $total) : 0;
	my $f = sprintf "%2.2f", 100* $utxos{$k} / $utxos;
	print "$k=${v}BTC ($s%), $utxos{$k} utxos ($f%)\n";
}
$avg = sprintf "%f",$total / $utxos;
my $total_taddrs = keys %taddrs;
print "total=$total, avg=$avg in $utxos UTXOs, $total_taddrs taddrs\n";
