import argparse
import json
import logging
import ollama
import pandas as pd
import textwrap
from scripts.utils import llm_chat, check_valid_json

logging.basicConfig(filename='app1_extraction.log', level=logging.ERROR)

SYSTEM_MESSAGE = """
You are an expert botanist. You can extract and encode data from text to JSON.
"""

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


def check_valid_json(output, taxon_dict):
    try:
        sentence_dict = json.loads(output)
        taxon_dict.update(sentence_dict)
    except Exception as e:
        logging.error(f"Failed to parse JSON {output} | Error: {e}")
    return taxon_dict


def main():
    parser = argparse.ArgumentParser(description="Extracts quantitative traits")
    parser.add_argument('input_file_sentences', help="Path to the input text file containing the sentences")
    parser.add_argument('input_file_app1', help="Path to the input text file containing the appendix1")
    parser.add_argument('output_file', help="Path to the output CSV file where the data is saved")
    parser.add_argument('--model_name', default='llama3.3', help="Name of the model to use for the chat completion (default: 'llama3.3')")
    # Parse arguments
    args = parser.parse_args()
    # Set up connection to ollama model on HPC
    ollama_client = ollama.Client(host='http://127.0.0.1:18199')
    # Read the input files
    df_sentences = pd.read_csv(args.input_file_sentences)#.drop(columns=['subject'])
    df_app1 = pd.read_csv(args.input_file_app1)
    # If subject_extract is empty, remove those rows
    df_sentences = df_sentences[~df_sentences.subject_extract.isna() & (df_sentences.subject_extract.str.strip() != "")]
    # Create an empty dataframe to store the output
    df_output = pd.DataFrame()
    # Iterate over each unique species
    for taxon_name in df_sentences.taxon_name.unique():
        # Set up dictionary to store species names
        taxon_dict = {'taxon_name': taxon_name}
        # Iterate over each subject in appendix_2 dataframe
        for subject in df_app1.subject_extract.unique():
            mask = (
                (df_sentences.subject_extract == subject) &
                (df_sentences.taxon_name == taxon_name) &
                (df_sentences.sentence.str.contains("[0-9]"))
            )
            # Sentences about the current taxon_name and subject are joined together into a paragraph
            subject_para = " ".join(
                df_sentences[mask]['sentence'].to_list()
            )
            appendix_1_subject = df_app1[
                df_app1.subject_extract == subject
            ][["description", "code"]]
            for _, row in appendix_1_subject.iterrows():
                prompt = textwrap.dedent(f"""
                    You are an expert botanist. You can extract and encode data 
                    from text. You are supplied with the description of a 
                    species ("description"), a code for a trait ("code").
                    Make a JSON dictionary with the key code and the 
                    corresponding value from the description. Do not fabricate 
                    data and ensure the values correspond to the correct code. 
                    If you cannot score the variable, set the value to null. 
                    Your answer must be as complete and accurate as possible. 
                    Ensure your output is strictly in valid JSON format, and do 
                    not include any extra text. Follow the format of the 
                    following examples.

                    ### Example 1:
                    description: "Stems clustered, climbing, 3.0 m long."
                    code: "stemlength"
                    response: {{"stemlength": "3.0 m"}}

                    ### Example 2:
                    description: "pinnae 5(5–6) per side of rachis."
                    code: "numpin"
                    response: {{"numpin": "5(5-6)"}}

                    ### Example 3:
                    description: "pistillate rachillae 3.3(1.8–4.5) cm long."
                    code: "psraclen"
                    response: {{"psraclen": "3.3(1.8–4.5) cm"}}

                    Generate the JSON for the following:\n
                    description: {subject_para}\n
                    code: {row['code']}
                """)
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
