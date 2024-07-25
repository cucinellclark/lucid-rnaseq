import os, sys, glob, argparse
import json, subprocess

parser = argparse.ArgumentParser()
parser.add_argument('--threads','-t',help='number of threads to use for tools',default='4')
parser.add_argument('--config','-c',help='config file for snakemake',default='job_config.json')

args = parser.parse_args()
print(args)

with open(args.config,'r') as i:
    config = json.load(i)

config_path = os.path.realpath(args.config)

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
        print(f'{single_end[sample_id]["read1"]} does not exist')
if error:
    print('fix file issues')
    sys.exit()

### create output directory and file and change into it
if not os.path.exists(config["output_path"]):
    print(f'Output directory {config["output_path"]} doesnt exist, exiting')
    sys.exit()
output_folder = os.path.join(config["output_path"],config["output_file"])
if not os.path.exists(output_folder):
    os.mkdir(output_folder)
os.chdir(output_folder)

### run snakemake for trim_galore
if len(paired_end) > 0:
    # run paired 
    try:
        cmd = ['snakemake','-s',os.path.join(pipeline_path,'qa_paired.snk'),'--configfile',config_path,'-c',args.threads]
        print(' '.join(cmd))
        subprocess.check_call(cmd)
    except Exception as e:
        print(f'Error running paired snakemake:\n{e}\n')
        sys.exit()
if len(single_end) > 0:
    #run single
    try:
        cmd = ['snakemake','-s',os.path.join(pipeline_path,'qa_single.snk'),'--configfile',config_path,'-c',args.threads]
        print(' '.join(cmd))
        subprocess.check_call(cmd)
    except Exception as e:
        print(f'Error running single snakemake:\n{e}\n')
        sys.exit()

### write new job json
new_config_path = os.path.join(os.path.dirname(config_path),'job_config_trimmed.json')
new_config = json.loads(json.dumps(config))
# single
for tr in glob.glob('trimmed/*trimmed.fq.gz'):
    sid = os.path.basename(tr).replace('_trimmed.fq.gz','')
    new_config['single_end_libs'][sid]['read'] = os.path.realpath(tr)
# paired
for tr1 in glob.glob('trimmed/*val_1.fq.gz'):
    sid = os.path.basename(tr1).replace('_val_1.fq.gz','')
    tr2 = os.path.join(os.path.dirname(tr1),f'{sid}_val_2.fq.gz')
    new_config['paired_end_libs'][sid]['read1'] = os.path.realpath(tr1)
    new_config['paired_end_libs'][sid]['read2'] = os.path.realpath(tr2)
with open(new_config_path,'w') as o:
    json.dump(new_config,o)
