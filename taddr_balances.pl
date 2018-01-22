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
my $dust = shift || 0.00115260;
my $dusts;
my $above_dusts = 0;

while (<>) {
        my ($type,$amount,$taddr,$utxo) = split ",";
	# amount=0 UTXOs do exist, filter them
	next unless $amount > 0;
	$totals{$type} += $amount;
	$utxos{$type}++;
	$total         += $amount;
	$total_length  += length($utxo);
	if ($taddrs{$taddr}) {
		$taddrs{$taddr} += $amount;
	} else {
		$taddrs{$taddr} = $amount;
	}
	$utxos++;
}

while (my ($taddr,$amount) = each %taddrs) {
	if ($amount >= $dust) {
		print "$taddr,$amount\n";
		$above_dusts++;
	} else {
		$dusts++;
	}

}
my $total_taddrs = keys %taddrs;
print "total=$total, $utxos UTXOs, $total_taddrs taddrs, $dusts taddrs below, $above_dusts above, dust=$dust\n";
