import argparse
import json
import os
import sys
import pandas as pd

parser = argparse.ArgumentParser()

parser.add_argument('-c','--config',required=True)
parser.add_argument('-o','--output',default='cuffdiff_diffexp.json')

args = parser.parse_args()

with open(args.config,'r') as i:
    config = json.load(i)

contrasts = config['contrasts'] 
reads_libs = list(config['single_end_libs'].values()) + list(config['paired_end_libs'].values())

condition_dict = {}
bam_dict = {}
for read_obj in reads_libs:
    print(read_obj)
    cond = read_obj['condition']
    if cond not in condition_dict:
        condition_dict[cond] = []
    sample_id = read_obj['sample_id']
    condition_dict[cond].append(read_obj['sample_id'])
    bam_file = os.path.join('aligned',f'{sample_id}_Aligned.sortedByCoord.out.bam')
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
    output = f"results/{cond1}_vs_{cond2}_diff"
    data = [output,cond1,cond2,','.join(cond1_bams),','.join(cond2_bams)]
    data_list.append(data)

data_df = pd.DataFrame(data_list)
data_df.columns = ['Output','Cond1','Cond2','Bams1','Bams2']

data_df.to_csv('cuffdiff_contrasts_table.txt',sep='\t',index=False)
