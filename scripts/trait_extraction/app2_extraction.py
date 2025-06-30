import argparse
import json
import logging
import ollama
import pandas as pd
from scripts.utils import llm_chat, check_valid_json
from .prompts import *

logging.basicConfig(filename='app2_extraction.log', level=logging.ERROR)

# Ensure that entire descriptions can be printed and used
pd.set_option('display.max_colwidth', None)
pd.set_option('display.max_rows', None)

SYSTEM_MESSAGE = "You are an expert botanist. You can extract and encode data from text to JSON."


def read_input_files(input_file_sentences, input_file_app2):
    # Convert the csv files into pandas dataframes, remove unwanted columns, and rename columns
    df_sentences = (
        pd.read_csv(input_file_sentences)
        .drop(['subject_gen'], axis=1)
        .rename(columns={'subject_extract': 'subject'})
    )
    # If subject_extract is empty, remove those rows
    df_sentences = df_sentences[~df_sentences.subject.isna() & (df_sentences.subject.str.strip() != "")]
    df_app2 = (
        pd.read_csv(input_file_app2)
        .drop(['number', 'extra', 'subject_gen'], axis=1)
        .rename(columns={'description': 'rules', 'subject_extract': 'subject'})
    )
    return df_sentences, df_app2


def parse_args():
    """
    Function to parse command line arguments.
    """
    parser = argparse.ArgumentParser(description="Extracts qualitative traits from text files.")
    parser.add_argument('input_file_sentences', help="Path to the input text file containing the sentences")
    parser.add_argument('input_file_app2', help="Path to the input text file containing the appendix2")
    parser.add_argument('prompt_style', choices=['zeroshot', 'fewshot', 'cot', 'cot-fewshot'], 
                        help=(
                        "Choice of prompt style:\n"
                        "  - zeroshot: No examples or intermediate reasoning, directly generates the output.\n"
                        "  - fewshot: Provides a few examples to guide the model's response.\n"
                        "  - cot: Chain-of-thought prompting, breaking down the task into logical steps.\n"
                        "  - cot-fewshot: Combines chain-of-thought reasoning with a few examples."
                    ))   
    parser.add_argument('output_file', help="Path to the output CSV file where the data is saved")
    parser.add_argument('--model_name', default='llama3.3', help="Name of the model to use for the chat completion (default: 'llama3.3')")
    return parser.parse_args()


def main():
    # Parse arguments
    args = parse_args()
    # Set up connection to ollama model on HPC
    ollama_client = ollama.Client(host='http://127.0.0.1:18199')
    # Read in the input files
    df_sentences, df_app2 = read_input_files(args.input_file_sentences, args.input_file_app2)
    # Create an empty dataframe to store the output
    df_output = pd.DataFrame()
    # Iterate over each unique taxon_name
    for taxon_name in df_sentences.taxon_name.unique():
        # Set up dictionary to store species names
        taxon_dict = {'taxon_name': taxon_name}
        # Iterate over each subject in appendix_2 dataframe
        for subject in df_app2.subject.unique():
            mask = (
                (df_sentences.subject == subject) &
                (df_sentences.taxon_name == taxon_name)
            )
            # Sentences about the current taxon_name and subject are joined together into a paragraph
            subject_para = " ".join(
                df_sentences[mask]['sentence'].to_list()
            )
            # Batch size
            batch_size = 8
            # Filter df_app2 to get rows matching current subject and code, selecting only the 'code' and 'rules' columns
            df_app2_subject = df_app2[df_app2.subject == subject][["code", "rules"]]
            # Split the DataFrame into batches of length batch_size using list comprehension
            batches = [df_app2_subject[i:i + batch_size] for i in range(0, len(df_app2_subject), batch_size)]
            # Iterate through each batch and convert to json
            for batch in batches: 
                print(f"this is a batch: {batch}")
                appendix_2_subject_batch = json.loads(batch.to_json(orient="records"))
                if args.prompt_style == 'zeroshot':
                    prompt_outline = ZERO_SHOT_PROMPT
                elif args.prompt_style == 'fewshot':
                    prompt_outline = FEW_SHOT_PROMPT
                elif args.prompt_style == 'cot':
                    prompt_outline = COT_PROMPT
                elif args.prompt_style == 'cot-fewshot':
                    prompt_outline = COT_FEWSHOT_PROMPT
                prompt = prompt_outline.format(subject_para=subject_para, appendix_2_subject_batch=appendix_2_subject_batch)
                output = llm_chat(ollama_client, args.model_name, SYSTEM_MESSAGE, prompt)
                # Check if the output is a valid JSON object
                taxon_dict = check_valid_json(output, taxon_dict)
        # Convert taxon_dict into a pandas dataframe and join it to the output
        df_taxon = pd.DataFrame([taxon_dict])
        df_output = pd.concat([df_output, df_taxon])
    # Save the output to a CSV file
    df_output.to_csv(args.output_file, index=False)

if __name__ == "__main__":
    main()
