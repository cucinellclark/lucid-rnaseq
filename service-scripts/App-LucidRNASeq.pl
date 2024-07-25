#
# The LUCID RNASeq application
#

use Bio::KBase::AppService::AppScript;
use Bio::KBase::AppService::AppConfig;
use Bio::KBase::AppService::ReadSet;
use Bio::P3::LucidRNASeq::AppConfig qw(lrna_service_data);

use strict;
use Data::Dumper;
use File::Basename;
use File::Slurp;
use File::Temp;
use LWP::UserAgent;
use JSON::XS;
use IPC::Run qw(run);
use Cwd qw(abs_path getcwd);
use Clone;
use P3DataAPI;

my $script = Bio::KBase::AppService::AppScript->new(\&process_rnaseq, \&preflight);

my $rc = $script->run(\@ARGV);

exit $rc;

# TODO: copy RNASeq preflight
sub preflight
{

}

# TODO: upload workspace data
sub process_rnaseq
{
    my($app, $app_def, $raw_params, $params) = @_;

    print 'Proc lucid rnaseq ', Dumper($app_def, $raw_params, $params);

    my $params_copy = Clone::clone($params);

    my $token = $app->token();
    my $ws = $app->workspace();

    # CLEANUP = 0 (dont delete), CLEANUP = 1 (delete)
    my $cwd = File::Temp->newdir( CLEANUP => 0 );
    #my $cwd = "/tmp/AmR8g5Sr7H"; # use existing folder for testing, skip steps

    my $work_dir = "$cwd/work";
    my $stage_dir = "$cwd/stage";

    -d $work_dir or mkdir $work_dir or die "Cannot mkdir $work_dir: $!";
    -d $stage_dir or mkdir $stage_dir or die "Cannot mkdir $stage_dir: $!";

    # download reads
    my $readset = Bio::KBase::AppService::ReadSet->create_from_asssembly_params($params,1);

    my($ok, $errs, $comp_size, $uncomp_size) = $readset->validate($app->workspace);

    if (!$ok)
    {
        die "Readset failed to validate. Errors:\n\t" . join("\n\t", @$errs);
    }

    $readset->localize_libraries($stage_dir);
    $readset->stage_in($app->workspace);

    my $data_api = Bio::KBase::AppService::AppConfig->data_api_url;
    my $dat = { data_api => $data_api };
    my $sstring = encode_json($dat);

    my $parallel = $ENV{P3_ALLOCATED_CPU};

    my $nparams = { single_end_libs => [], paired_end_libs => [], srr_libs => [] };
    $readset->visit_libraries(sub { my($pe) = @_;
                    my $lib = {
                    read1 => abs_path($pe->{read_path_1}),
                    read2 => abs_path($pe->{read_path_2}),
                    (exists($pe->{sample_id}) ? (sample_id => $pe->{sample_id}) : ()),
                    (exists($pe->{condition}) ? (condition => $pe->{condition}) : ())
                    };
                    print "PAIRED LIB\n";
                    warn Dumper ($pe);
                    push(@{$nparams->{paired_end_libs}}, $lib);
                },
                  sub {
                  my($se) = @_;
                  my $lib = {
                      read => abs_path($se->{read_path}),
                      (exists($se->{sample_id}) ? (sample_id => $se->{sample_id}) : ()),
                      (exists($se->{condition}) ? (condition => $se->{condition}) : ())
                      };
                  push(@{$nparams->{single_end_libs}}, $lib);
                  },
                 );
    $params->{$_} = $nparams->{$_} foreach keys %$nparams;

    # add service data to params
    $params->{service_data} = lrna_service_data;

    # change output path to working directory
    $params->{output_path} = "$work_dir/$params->{output_folder}";

    #
    # Create json config file for the execution of this workflow.
    # If we are in a production deployment, we can find the workflows
    # by looking in $KB_TOP/workflows/app-name
    # Otherwise they are in the module directory; this is indicated
    # by the value of $KB_MODULE_DIR (note this is set for both
    # deployed and dev-container builds; the deployment case
    # is determined by the existence of $KB_TOP/workflows)
    #
    my $wf_dir = "$ENV{KB_TOP}/modules/$ENV{KB_MODULE_DIR}/workflow";
    -d $wf_dir or die "Workflow directory $wf_dir does not exist";
    $params->{workflow_dir} = $wf_dir;

    #
    # Write job description.
    #  
    my $jdesc = "$work_dir/jobdesc.json";
    open(JDESC, ">", $jdesc) or die "Cannot write $jdesc: $!";
    print JDESC JSON::XS->new->pretty(1)->encode($params);
    close(JDESC);

    # Prepare config file
    # - assuming previous bvbrc setup
    # parser.add_argument('--job_json',help="Job Json file with samples, reference genome id, conditions, etc",required=True)
    # parser.add_argument('--config_file',help="Output name for the generated snakemake config file",default='job_config.json')
    my $job_config = "$work_dir/modjob_config.json";
    my @prep_cmd = ('lrna-star-prepare_config','--job_json',$jdesc,'--config_file',$job_config);
    warn Dumper (\@prep_cmd, $params);
    my $prep_ok = run(\@prep_cmd);

    if (!$prep_ok)
    {
        die "prepare_config.py failed: @prep_cmd\n";
    }
}
