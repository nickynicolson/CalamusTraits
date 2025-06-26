import argparse
import numpy as np
import ollama
import pandas as pd
import re
import textwrap
from scripts.utils import *

# Ensure that entire descriptions can be printed and used
pd.set_option('display.max_colwidth', None)

SYSTEM_MESSAGE = "You are an expert botanist."

def process_supp_data(file_path):
    # Read in the formatted supplementary data
    supp_data = (
        pd.read_csv(file_path)
        .replace(to_replace=np.nan, value='')
        .iloc[:, 0:15]
    )

    tidy_supp_data = (
        supp_data.melt(id_vars=["taxon_name"], var_name="code", value_name="value")
    )
    
    return supp_data, tidy_supp_data


def process_appendix1(file_path):
    # Read in the appendix
    df_app1 = (
        pd.read_csv(file_path)
        .drop(['number', 'source', 'subject_extract'], axis=1)
        .rename(columns={"subject_gen": "subject"})
        .replace(to_replace=np.nan, value='')
    )
    return df_app1


def get_supp_codes(tidy_supp_data, code, taxon_name):
    """
    Function to get the code and value from the tidy supplementary data
    for a specific taxon name.
    """
    return tidy_supp_data[
        (tidy_supp_data.code == code) &
        (tidy_supp_data.taxon_name == taxon_name)
    ][["code", "value"]].to_json(orient='records')


def llm_chat(ollama_client, model_name,system_mesage, prompt):
    """
    Function to generate a description using the Ollama model.
    """
    chat_completion = ollama_client.chat(
        model=model_name,
        messages=[
            {"role": "system", "content": system_mesage},
            {"role": "user", "content": prompt}
        ],
        options={"temperature": 0}
    )
    return chat_completion['message']['content']


def process_output(output):
    # Check if the output contains any digits
    if not re.search(r'\d', output):
        output = ''

    # Remove .0 from numpin
    if re.search(r'Number of pinnae', output):
        output = re.sub(r'\.0', '', output)
    
    return output


def append_output(output_list, taxon_name, output, subject):
    """
    Appends a dictionary with taxon_name, output_sentence, and subject to the output_list.
    """
    loop_dict = {
        "taxon_name": taxon_name,
        "output_sentence": output,
        "subject": subject
    }
    output_list.append(loop_dict)


def main():
    parser = argparse.ArgumentParser(description="Generates descriptions based on the appendix 1 data")
    parser.add_argument('input_file_app1', help="Path to the input text file containing the appendix1")
    parser.add_argument('input_file_supp_data', help="Path to the input CSV file containing the supplementary data")
    parser.add_argument('output_file', help="Path to the output CSV file where the descriptions are saved")
    parser.add_argument('--model_name', default='llama3.3', help="Name of the model to use for the chat completion (default: 'llama3.3')")
    # Parse arguments
    args = parser.parse_args()
    # Set up connection to ollama model on HPC
    ollama_client = ollama.Client(host='http://127.0.0.1:18199')
    # Read in the input files
    df_app1 = process_appendix1(args.input_file_app1)
    supp_data, tidy_supp_data = process_supp_data(args.input_file_supp_data)
    # Create an empty list to store the output
    output_list = []
    # Iterate over each taxon_name
    for taxon_name in supp_data.taxon_name.unique():
        # Iterate over each code in the app1 DataFrame
        for code in df_app1.code.unique():
            # Look up subject that relates to code
            subject = df_app1.loc[df_app1["code"] == code, "subject"].iloc[0]
            # Filter the supplementary data for the specific code and taxon_name 
            # And convert to json
            supp_codes = get_supp_codes(tidy_supp_data, code, taxon_name)
            # Filter the app1 DataFrame for the specific code
            # And convert to json
            app1_descriptions = df_app1[
                df_app1.code == code
            ][["code", "description", "unit"]].to_json(orient='records')
            # Set up the prompt
            prompt = textwrap.dedent(f"""
                ### Instructions ###
                Use the "description" and "unit" in {app1_descriptions} and the 
                corresponding "value" in {supp_codes} to create a simple sentence 
                describing that particular trait. Your output should be one 
                sentence. Blank values should return an empty string. Include no 
                extra text.

                ### Example ###
                Using {{"code":"rachislen","description":"Rachis length","unit":"cm"}} 
                and {{"code":"rachislen","value":"41.0(25.5-70.0)"}}, the output 
                would be 'Rachis length is 41.0(25.5-70.0)cm'.
            """)
            # Send the prompt to the LLM
            output = llm_chat(ollama_client, args.model_name, SYSTEM_MESSAGE, prompt)
            # Clean the output
            output = process_output(output)
            # Store the output in a dictionary and append to output list
            append_output(output_list, taxon_name, output, subject)
    # Create a DataFrame from the output list
    df_output = pd.DataFrame(output_list)
    # Remove any rows where the output_sentence is an empty string
    df_output = df_output[df_output["output_sentence"].str.strip() != ""]
    # Save the output to a CSV file
    df_output.to_csv(args.output_file, index=False)

if __name__ == "__main__":
    main()