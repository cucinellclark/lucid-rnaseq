import json
import time
import os,sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, Future
import asyncio
import argparse

def submit_job(command, job_name):
    """
    Simulate job submission. This function returns a simulated job ID.
    """
    print(f"[SIMULATION] Submitting job: {job_name} with command: {command}")
    # Simulate job submission by returning a unique job ID (use timestamp for simplicity)
    job_id = f"job_{int(time.time() * 1000)}"
    return job_id

async def wait_for_job(job_id):
    """
    Simulate waiting for a job to finish using non-blocking sleep.
    """
    print(f"[SIMULATION] Waiting for job {job_id} to finish...")
    await asyncio.sleep(2)  # Non-blocking sleep
    print(f"[SIMULATION] Job {job_id} finished.")

async def process_sample(job_file):

    # TODO: check if waiting for job to finish, implement slurm tracker  

    app_start_cmd = f"appserv-start-app -d {output_path} \
                -f {output_file} \
                --id-file {id_file} \
                App-LucidRNASeq {job_file}"

    '''
    appserv-start-app -d /nfs/ml_lab/projects/ml_lab/LUCID/Study_3Week_HUVEC_RNA/work_dir -f test_appserv_out --id-file test_id_file.txt App-LucidRNASeq  
    appserv-start-app.pl [-bcDdfhuv] [long options...] app-id params-data [workspace]
    --output-path STR (or -d)        Change the output path
    --output-file STR (or -f)        Change the output file
    --id-file STR                    Save the generated task id to this
                                     file
    --container-id STR (or -c)       Use the specified container
    --data-container-id STR (or -D)  Use the specified data container
    --base-url STR (or -b)           Submit with the chosen base URL
    --user-metadata STR              Tag the job with the given metadata
    --user-metadata-file STR         Tag the job with the given metadata
                                     from this file
    --verbose (or -v)                Show verbose output
    --url STR (or -u)                Service URL
    --help (or -h)                   Show this help message
    '''

    # Define commands for alignment and counting
    alignment_output = f"/nfs/ml_lab/projects/ml_lab/LUCID/alignments/{sample_id}_aligned.bam"
    alignment_command = f"aligner_program --input1 {read1} --input2 {read2} --output {alignment_output}"

    counting_output = f"/nfs/ml_lab/projects/ml_lab/LUCID/counts/{sample_id}_counts.txt"
    counting_command = f"counter_program --input {alignment_output} --output {counting_output}"

    # Submit alignment job
    alignment_job_name = f"alignment_{sample_id}"
    alignment_job_id = submit_job(alignment_command, alignment_job_name)

    # Simulate waiting for alignment job to finish
    await wait_for_job(alignment_job_id)

    # Submit counting job after alignment job finishes
    counting_job_name = f"counting_{sample_id}"
    counting_job_id = submit_job(counting_command, counting_job_name)

    # Simulate waiting for counting job to finish
    await wait_for_job(counting_job_id)

async def create_workflow(job_list):
    """
    Create a workflow for each sample with alignment and counting jobs using multithreading.
    """
    tasks = [process_sample(job_file) for job_file in job_list]
    await asyncio.gather(*tasks)

def generate_json_files(data, output_directory):
    os.makedirs(output_directory, exist_ok=True)  # Ensure the output directory exists
    json_list = []
    for entry in data["paired_end_libs"]:
        for step in data['steps']:
            # Create a new data structure with the modified fields
            modified_data = {
                "paired_end_libs": [entry],
                "single_end_libs": data["single_end_libs"],
                "experimental_conditions": [entry["condition"]],
                "steps": [step],
                "contrasts": data["contrasts"],
                "recipe": data["recipe"],
                "diffexp": data["diffexp"],
                "reference_genome_id": data["reference_genome_id"],
                "fasta": data["fasta"],
                "gff": data["gff"],
                "gtf": data["gtf"],
                "star_index": data["star_index"],
                "output_path": data["output_path"],
                "output_file": data["output_file"],
                "work_directory": data["work_directory"],
            }

            # Generate a unique file name based on the sample_id
            file_name = f"{entry['sample_id']}_{step}.json"
            file_path = os.path.join(output_directory, file_name)

            # Write the modified data to a JSON file
            with open(file_path, "w") as json_file:
                json.dump(modified_data, json_file, indent=4)
            json_list.append(file_path)
    return json_list

def main():
    parser = argparse.ArgumentParser(description="Process a JSON file to create a job workflow.")
    parser.add_argument('-j',"--json_file", type=str, help="Path to the JSON file containing job data.")
    args = parser.parse_args()

    # Load job data from JSON file
    json_file = args.json_file
    if not Path(json_file).exists():
        print(f"Error: {json_file} not found.")
        return

    with open(json_file, "r") as f:
        job_data = json.load(f)

    job_list = generate_json_files(job_data,os.path.join(job_data['work_directory'],'job_jsons'))
    print(job_list)
    sys.exit()

    # Create the workflow
    asyncio.run(create_workflow(job_list))

if __name__ == "__main__":
    main()

