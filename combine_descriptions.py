# Script to combine the outputs of app1_descriptions and app2_descriptions
# Use LLM to combine the sentences for a specific subject
import argparse
import json
import pandas as pd
import textwrap
import ollama

# Ensure that entire descriptions can be printed and used
pd.set_option('display.max_colwidth', None)

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

SYSTEM_MESSAGE = """
You are an expert in botanical monography and concise writing. 
Always refer to plant parts or traits directly, avoiding pronouns like 'it' or 'they'. 
Clarity and specificity are essential. Ensure the style is concise and technical. Avoid narrative or explanatory language.
Follow the style and tone of formal taxonomic monographs.
"""


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


def main():
    parser = argparse.ArgumentParser(
    description="Generates descriptions based on the appendix 2 data"
    )
    parser.add_argument(
        'input_file_app1', 
        help="Path to the input csv file containing the appendix 1 descriptions"
    )
    parser.add_argument(
        'input_file_app2', 
        help="Path to the input csv file containing the appendix 2 descriptions"
    )
    parser.add_argument(
        'output_file', 
        help="Path to the output CSV file where the descriptions are saved"
    )
    parser.add_argument(
        '--model_name',
        default='llama3.3',
        help="Name of the model to use for the chat completion (default: 'llama3.3')"
    )

    # Parse arguments
    args = parser.parse_args()

    # Set up ollama connection
    ollama_client = ollama.Client(host='http://127.0.0.1:18199')

    # Call the function with the paths to the CSV files
    all_descriptions = combine_descriptions(args.input_file_app1, args.input_file_app2)

    # Create an empty list to store the output
    output_list = []

    # Iterate over each taxon name
    for taxon_name in all_descriptions.taxon_name.unique():

        # Iterate over each subject in the descriptions
        for subject in all_descriptions.subject.unique():

            # Join sentences for each subject
            sentences = all_descriptions[
                (all_descriptions.subject == subject) &
                (all_descriptions.taxon_name == taxon_name)
            ]['output_sentence'].to_list()

            # Skip if sentences is empty
            if not sentences:
                continue

            sentences = json.dumps(sentences)
            
            # Set up the prompt
            prompt = textwrap.dedent(f"""
                Combine the following sentences / clauses as concisely as possible:\n {sentences}
                This must be written in the style of a traditional botanical monograph.  
                Avoid excessive negations or long lists of features that are not present unless those absences are crucial for species identification. 
                Retain all measurements. Return the combination with NO EXTRA TEXT.
            """)
            #print(prompt)
            # If "sentences" contains multiple sentences, combine them using a LLM
            if len(sentences) > 1:
                chat_completion = ollama_client.chat(
                    model=args.model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": SYSTEM_MESSAGE,
                        },
                        {
                            "role": "user",
                            "content": prompt,
                        },
                    ],
                    options={"temperature": 0}
                )

                # Get the output from the chat completion
                output = chat_completion['message']['content']

            # If there is only one sentence, just return the sentence
            else:
                output = sentences[0]

            # Store the output in a dictionary
            loop_dict = {
                "taxon_name": taxon_name,
                "species_description": output,
                "subject": subject
            }
            print(loop_dict)
            # Append the dictionary to the output list
            output_list.append(loop_dict)

    # Create a DataFrame from the output list
    df_output = pd.DataFrame(output_list)

    # Remove any rows where the species_description is an empty string
    df_output = df_output[df_output["species_description"].str.strip() != ""]

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
    # and group by 'taxon_name'
    df_output = (
        df_output.sort_values(by=['taxon_name', 'subject'])
        # .drop(columns=['subject'])
        # .groupby('taxon_name')
        # .agg({'species_description': ' '.join})
        # .reset_index()
    )

    # Save output DataFrame as a csv file
    df_output.to_csv(args.output_file, index=False)

if __name__ == "__main__":
    main()
