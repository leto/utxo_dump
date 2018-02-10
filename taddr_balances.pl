#!/usr/bin/perl

use strict;
use warnings;
use Data::Dumper;

my %totals;
my %utxos;
my $utxos = 0;
my $total = 0;
my $total_above = 0;
my $total_below = 0;
my $avg   = 0;
my $total_length = 0;
my %taddrs;
my $dust = shift || 0.01;
my $dusts = 0;
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
		$total_above += $amount;
	} else {
		$dusts++;
		$total_below += $amount;
	}

}
$total_below = sprintf "%2.3f", $total_below;
$total_above = sprintf "%2.3f", $total_above;
my $total_taddrs = keys %taddrs;
warn "total=$total, $utxos UTXOs, $total_taddrs taddrs, $dusts taddrs below (${total_below}BTC), $above_dusts above (${total_above}BTC), dust=$dust\n";
