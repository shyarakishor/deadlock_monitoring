#!/usr/bin/perl -w
use strict;

# Dependencies ###################################
use FileHandle qw();
use File::Basename qw();
use Cwd qw();
my $base_dir;
my $relative_path;

BEGIN {
   $relative_path = './';
   $base_dir = Cwd::realpath(File::Basename::dirname(__FILE__) . '/' . $relative_path);
}
# Dependencies ####################################

use lib "$base_dir/lib64/perl5";
use CGI qw(:standard);
use CGI::Carp qw(fatalsToBrowser) ;
use YAML::XS qw(LoadFile Load);
use Template;
use JSON;

##################################################

# Version Info ###################################
my $VERSION = "1.0.0";
##################################################

my $q = new CGI;
print $q->header;

#################
# Config Values #
#################
my $CONFIG_FILE = "$base_dir/resources/deadcheckconf.yml";

# Load Config Data #######################################	
my $filedata = LoadFile($CONFIG_FILE);

my $header_title    = $filedata->{header_title};
my $csv_file        = $filedata->{file};
my $from_date       = $filedata->{fromdate};
my $to_date         = $filedata->{todate};
my $graph_frequency = $filedata->{graph_frequency};
my $footer_hash     = $filedata->{footer};

####Read CSV File and Collect Lines
my $csv_lines = [];
my $fh = FileHandle->new;
if ( $fh->open("< $csv_file") ) {
	while (my $line = $fh->getline()) {
		chomp($line);
		push @$csv_lines, $line;
	}
	$fh->close;
} 
else {
	print "Cannot open $csv_file"; 
	die;
}
####Read CSV File and Collect Lines END

if ( $from_date && $from_date !~ /^\s*$/ ) {
	$from_date = &check_convert_date_format( $from_date );
}
if ( $to_date && $to_date !~ /^\s*$/ ) {
	$to_date   = &check_convert_date_format( $to_date );
}

##start read and prepare Graph
my $final_data_array = [];
if( scalar @$csv_lines ) {
	foreach my $line ( @$csv_lines ) {
		$line = &trim_space( $line );

		my ( $date_time, $value ) = split(',', $line);

		if( $date_time ) {
			if ( $from_date !~ /^\s*$/ && $to_date !~ /^\s*$/ ) {
				$date_time = &check_convert_date_format( $date_time );
				
				if ( $date_time ge $from_date && $date_time le $to_date ) {

					my ( $date ) = $date_time =~ /(.*?)\s+(.*)/;

					if ( $date ) {
						$date  = &trim_space( $date );
						
						my ( $m, $d, $y ) = $date =~ /(\d+)\/(\d+)\/(\d+)/;
						$m -= 1;
						my $new_date = sprintf('%02d', $m).'/'.sprintf('%02d', $d).'/'.sprintf('%02d', $y);

						$value = &trim_space( $value );

						push @$final_data_array, {
							x => "new Date($y, $m, $d)",
							y => $value
						};
					}
				}
			}
			else {
				my ( $date ) = $date_time =~ /(.*?)\s+(.*)/;
				if ( $date ) {
					$date  = &trim_space( $date );
					$value = &trim_space( $value );

					my ( $m, $d, $y ) = $date =~ /(\d+)\/(\d+)\/(\d+)/;
					$m -= 1;
					my $new_date = sprintf('%02d', $m).'/'.sprintf('%02d', $d).'/'.sprintf('%02d', $y);

					push @$final_data_array, {
						x => "new Date($y, $m, $d)",
						y => $value
					};
				}
			}
		}
	}
}

my $data_json = to_json( $final_data_array );
$data_json =~ s/\"//g;
##generate template
my $config_template = {
	INCLUDE_PATH => $base_dir."/Templates",  # or list ref
	INTERPOLATE  => 1,               # expand "$var" in plain text
	POST_CHOMP   => 1,               # cleanup whitespace
	PRE_PROCESS  => '',              # prefix each template
	EVAL_PERL    => 1,               # evaluate Perl code blocks
};

my $obj_template = Template->new($config_template);

##feeddata in template
my $template_hash = {};
if ( $graph_frequency =~ /Day/i ) {
	$template_hash->{'value_format_string'} = 'MM/DD/YYYY';
}
elsif ( $graph_frequency =~ /Month/i ) {
	$template_hash->{'value_format_string'} = 'MMM';
}
elsif ( $graph_frequency =~ /Year/i ) {
	$template_hash->{'value_format_string'} = 'YYYY';
}
elsif ( $graph_frequency =~ /Week/i ) {
	$template_hash->{'value_format_string'} = 'DDD';
}
else {
	$template_hash->{'value_format_string'} = 'MM/DD/YYYY';
}

$template_hash->{'final_data_array'}    = $final_data_array;
$template_hash->{'data_json'}    = $data_json;
$template_hash->{'footer_hash'}  = $footer_hash;
$template_hash->{'header_title'} = $header_title;

$obj_template->process('linechart.html', $template_hash) || die "Template process failed: ", $obj_template->error(), "\n";

##trim
sub trim_space {
	my $line = shift;

	$line =~ s/^\s+//g;
	$line =~ s/\s+$//g;

	return $line;
}

sub check_convert_date_format {
	my $date_string = shift;

	my ( $m, $d, $y, $hh, $mm ) = $date_string =~ /(\d+)\/(\d+)\/(\d+)\s+(\d+):(\d+)/;
	if ( length($y) == 2 ) {
		$y = '20'.$y;
	}
	
	my $new_date = sprintf('%02d', $m).'/'.sprintf('%02d', $d).'/'.sprintf('%02d', $y).' '.sprintf('%02d', $hh).':'.sprintf('%02d', $mm);
	
	return $new_date;
}
