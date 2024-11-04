import argparse
import json
import os
import sys
import pandas as pd

parser = argparse.ArgumentParser()

parser.add_argument('-c','--config',required=True)
parser.add_argument('-o','--output',default='deseq_contrasts_table.txt')

args = parser.parse_args()

with open(args.config,'r') as i:
    config = json.load(i)

contrasts = config['contrasts'] 
reads_libs = []
if len(config['single_end_libs']) > 0:
    reads_libs += list(config['single_end_libs'].values())
if len(config['paired_end_libs']) > 0:
    reads_libs += list(config['paired_end_libs'].values())

condition_dict = {}
bam_dict = {}
for read_obj in reads_libs:
    cond = read_obj['condition']
    if cond not in condition_dict:
        condition_dict[cond] = []
    condition_dict[cond].append(read_obj['sample_id'])
    #bam_file = os.path.join('aligned',f'{read_obj["sample_id"]}_Aligned.sortedByCoord.out.bam')
    #print(read_obj)
    #bam_file = os.path.join(read_obj['bam_dir'],f'{read_obj["sample_id"]}_Aligned.sortedByCoord.out.bam')
    #if not os.path.exists(bam_file):
    #    print(bam_file)
    bam_file = 'temp'
    bam_dict[read_obj['sample_id']] = bam_file 


data_list = []
for pair in contrasts: 
    cond1,cond2 = pair
    cond1_bams = [] 
    cond2_bams = [] 
    for sample_id in condition_dict[cond1]:
        cond1_bams.append(bam_dict[sample_id])
    for sample_id in condition_dict[cond2]:
        cond2_bams.append(bam_dict[sample_id])
    output = f"results/{cond1}_vs_{cond2}_deseq.txt"
    data = [output,cond1,cond2,','.join(cond1_bams),','.join(cond2_bams)]
    data_list.append(data)

data_df = pd.DataFrame(data_list)
data_df.columns = ['Output','Cond1','Cond2','Bams1','Bams2']

data_df.to_csv(f'{args.output}',sep='\t',index=False)
