import argparse
import json
import ollama
import pandas as pd
import textwrap
from scripts.utils import llm_chat, append_output

# Ensure that entire descriptions can be printed and used
pd.set_option('display.max_colwidth', None)

SYSTEM_MESSAGE = """
You are an expert in botanical monography and concise writing. 
Always refer to plant parts or traits directly, avoiding pronouns like 'it' or 'they'. 
Clarity and specificity are essential. Ensure the style is concise and technical. Avoid narrative or explanatory language.
Follow the style and tone of formal taxonomic monographs.
"""

PROMPT = textwrap.dedent(f"""
Combine the following sentences / clauses as concisely as possible:\n {{sentences}}
This must be written in the style of a botanical monograph.  
Avoid excessive negations or long lists of features that are not present unless those absences are crucial for species identification. 
Retain all measurements. Return the combination with NO EXTRA TEXT.
""")

# Define subject order as a constant
SUBJECT_ORDER = [
    'Stem',
    'Leaf',
    'Ocrea',
    'Flagellum',
    'Petioles and rachises',
    'Pinna',
    'Inflorescence',
    'Peduncle',
    'Prophyll',
    'Partial inflorescence',
    'Rachilla',
    'Staminate structures',
    'Pistillate structures',
    'Fruit',
    'Seed',
]


def parse_args():
    """
    Function to parse command line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Combines descriptions of qualitative and quantitative traits from two CSV files into a single output file."
    )
    parser.add_argument('input_file_app1', help="Path to the input csv file containing the appendix 1 descriptions")
    parser.add_argument('input_file_app2', help="Path to the input csv file containing the appendix 2 descriptions")
    parser.add_argument('output_file', help="Path to the output CSV file where the descriptions are saved")
    parser.add_argument('--model_name', default='llama3.3', help="Name of the model to use for the chat completion (default: 'llama3.3')")
    parser.add_argument('--subject_sentences', action='store_true', help="If set, the output will contain subject separation.")
    return parser.parse_args()


def combine_descriptions(app1_path, app2_path):
    """
    Combine descriptions from two CSV files into a single DataFrame.

    Parameters:
    app1_path (str): Path to the quantitative traits' descriptions CSV file.
    app2_path (str): Path to the qualitative traits' descriptions CSV file.

    Returns:
    DataFrame: A pandas DataFrame containing descriptions from both CSV files.
    """
    # Read in csv file descriptions
    df_app1 = pd.read_csv(app1_path)
    df_app2 = pd.read_csv(app2_path)
    # Concatenate
    all_descriptions = pd.concat([df_app1, df_app2])
    return all_descriptions


def format_output(output_list, args, SUBJECT_ORDER):
    # Create a DataFrame from the output list
    df_output = pd.DataFrame(output_list)
    # Remove any rows where the species_description is an empty string
    df_output = df_output[df_output["output_sentence"].str.strip() != ""]
    # define a custom order for the subjects
    subject_order = SUBJECT_ORDER
    # Ensure all subjects in the custom order are present in the DataFrame
    df_output['subject'] = pd.Categorical(
        df_output['subject'],
        categories=[
            subject for subject in subject_order
            if subject in df_output['subject'].unique()
        ],
        ordered=True,
    )
    # Sort the DataFrame by 'taxon_name' and 'subject',
    df_output = df_output.sort_values(by=['taxon_name', 'subject'])
    if getattr(args, 'subject_sentences', False):
        return df_output
    else:
        df_output = (
            df_output
            .drop(columns=['subject'])
            .groupby('taxon_name', sort=False)
            .agg({'output_sentence': ' '.join})
            .reset_index()
        )
    return df_output


def main():
    # Parse arguments
    args = parse_args()
    # Set up connection to ollama model on HPC
    ollama_client = ollama.Client(host='http://127.0.0.1:18199')
    # Read in the input files
    all_descriptions = combine_descriptions(args.input_file_app1, args.input_file_app2)
    # Create an empty list to store the output
    output_list = []
    # Iterate over each taxon_name
    for taxon_name in all_descriptions.taxon_name.unique():
        # Iterate over each subject in the descriptions
        for subject in all_descriptions.subject.unique():
            # Join sentences for each subject
            mask = (
                (all_descriptions.subject == subject) &
                (all_descriptions.taxon_name == taxon_name)
            )
            sentences = all_descriptions[mask]['output_sentence'].to_list()
            # Skip if sentences is empty
            if not sentences:
                continue
            sentences = json.dumps(sentences)
            # Set up the prompt
            prompt_outline = PROMPT
            prompt = prompt_outline.format(sentences=sentences)
            # If "sentences" contains multiple sentences, combine them using a LLM
            if len(sentences) > 1:
                output = llm_chat(ollama_client, args.model_name, SYSTEM_MESSAGE, prompt)
            # If there is only one sentence, just return the sentence
            else:
                output = sentences[0]
            # Store the output in a dictionary and append to output list
            append_output(output_list, taxon_name, output, subject)
    # Format the output DataFrame
    df_output = format_output(output_list, args, SUBJECT_ORDER)
    # Save output DataFrame as a csv file
    df_output.to_csv(args.output_file, index=False)

if __name__ == "__main__":
    main()
