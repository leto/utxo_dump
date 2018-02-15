#!/usr/bin/perl

use strict;
use warnings;
use Data::Dumper;

my $total = 0;
my $avg   = 0;
my $total_new = 0;
my $avg_new   = 0;
my $total_taddrs = 0;

while (<>) {
        my ($amount,$taddr) = split ",";
	chomp $taddr;
	# 693132.45621953 /  7375458.89560229
	my $scale   = .09397821424139709226;
	my $new     = $amount * (1 - $scale);
	$total     += $amount;
	$total_new += $new;
	print "$amount,$new,$taddr\n";
	$total_taddrs++;
}

$avg     = sprintf "%f",$total     / $total_taddrs;
$avg_new = sprintf "%f",$total_new / $total_taddrs;
warn "total=$total, avg=$avg , $total_taddrs taddrs\n";
warn "total_new=$total_new, avg=$avg_new , $total_taddrs taddrs\n";
my $diff = $total - $total_new;
warn "Diff=$diff";
