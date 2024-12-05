import os, sys, glob, argparse
import json
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('--threads','-t',help='number of threads to use for tools',default='4')
parser.add_argument('--config','-c',help='config file for snakemake file',default="job_config.json")

args = parser.parse_args()
print(args)

with open(args.config,'r') as i:
    config = json.load(i)

config_path = os.path.realpath(args.config)

# workflow_dir is workflow folder + recipe
workflow_dir = os.path.join(config['workflow_dir'],'lucid-star')

print(config)
single_end = []
paired_end = []
error = False
file_dict = {}
if 'single_end_libs' in config:
    single_end = config['single_end_libs']
if 'paired_end_libs' in config:
    paired_end = config['paired_end_libs']
for sample_id in single_end:
    if not os.path.exists(single_end[sample_id]['read']):
        error = True
        print(f'{single_end[sample_id]["read"]} does not exist')
for sample_id in paired_end:
    if not os.path.exists(paired_end[sample_id]['read1']):
        error = True
        print(f'{paired_end[sample_id]["read1"]} does not exist')
if error:
    print('fix file issues')
    sys.exit()

### create output directory and file and change into it
# TODO: change
if not os.path.exists(config["output_path"]):
    print(f'Output directory {config["output_path"]} doesnt exist, exiting')
    sys.exit()
output_folder = os.path.join(config["output_path"],config["output_file"])
if not os.path.exists(output_folder):
    os.mkdir(output_folder)
os.chdir(output_folder)

### Run alignment
# - all output necessary for downstream programs should be put into the aligned directory
if len(paired_end) > 0 and 'align' in config['steps']:
    # run paired snakemake
    try:
        snkfile = os.path.join(workflow_dir,'align_paired.snk')
        cmd = ['snakemake','-s',snkfile,'--configfile',config_path,'-c',args.threads]
        print(' '.join(cmd))
        subprocess.check_call(cmd)
        snkfile2 = os.path.join(workflow_dir,'abundance_paired.snk')
        cmd = ['snakemake','-s',snkfile2,'--configfile',config_path,'-c',args.threads]
        print(' '.join(cmd))
        subprocess.check_call(cmd)
    except Exception as e:
        print(f'Error running paired snakemake:\n{e}\n')
        sys.exit()
if len(single_end) > 0 and 'align' in config['steps']:
    # run single snakemake
    try:
        snkfile = os.path.join(workflow_dir,'align_single.snk')
        cmd = ['snakemake','-s',snkfile,'--configfile',config_path,'-c',args.threads]
        print(' '.join(cmd))
        subprocess.check_call(cmd)
        snkfile2 = os.path.join(workflow_dir,'abundance_single.snk')
        cmd = ['snakemake','-s',snkfile2,'--configfile',config_path,'-c',args.threads]
        print(' '.join(cmd))
        subprocess.check_call(cmd)
    except Exception as e:
        print(f'Error running single snakemake:\n{e}\n')
        sys.exit()

### consolidate counts
if 'count' in config['steps']:
    snkfile_counts = os.path.join(workflow_dir,'abundance_table.snk')
    try:
        cmd = ['snakemake','-s',snkfile_counts,'--configfile',config_path,'-c','1']
        print(' '.join(cmd))
        subprocess.check_call(cmd)
    except Exception as e:
        print(f'Error running snakemake consolidate tables:\n{e}\n')
        sys.exit()

### Run differential expression
if 'diffexp' in config['steps']:
    if 'contrasts' in config and len(config['contrasts']) > 0:
        try:
            if config['diffexp'] == 'deseq':
                snkfile_diff = os.path.join(workflow_dir,"deseq.snk")
                prep_cmd = ['python3',os.path.join(workflow_dir,'prepare_deseq_config.py'),'-c',config_path]
                print(' '.join(prep_cmd))
                subprocess.check_call(prep_cmd)
            else:
                snkfile_diff = os.path.join(workflow_dir,"cuffdiff.snk")
                prep_cmd = ['python3',os.path.join(workflow_dir,'prepare_cuffdiff_config.py'),'-c',config_path]
                print(' '.join(prep_cmd))
                subprocess.check_call(prep_cmd)
        except Exception as e:
            print(f'Error running snakemake prepare diffexp config:\n{e}\n')
            sys.exit()
        try:
            cmd = ['/home/ac.cucinell/miniforge3/envs/snakemake/bin/snakemake','-s',snkfile_diff,'--configfile',config_path,'-c','4']
            print(' '.join(cmd))
            subprocess.check_call(cmd)
        except Exception as e:
            print(f'Error running snakemake differential expression:\n{e}\n')
            sys.exit()
    else:
        print(f'Error: contrasts either doesnt exist in config or no contrasts specified')
        sys.exit()
