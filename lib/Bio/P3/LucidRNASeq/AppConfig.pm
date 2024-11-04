package Bio::P3::LucidRNASeq::AppConfig;

use constant        lrna_service_data      => '/home/ac.cucinell/LUCID/RNASeq/Genome/';

use base 'Exporter';
our @EXPORT_OK = qw(lrna_service_data);
our %EXPORT_TAGS = (all => [@EXPORT_OK]);
1;
