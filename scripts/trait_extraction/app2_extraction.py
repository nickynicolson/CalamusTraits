import argparse
import json
import logging
import ollama
import pandas as pd
from scripts.utils import llm_chat, check_valid_json
from prompts import *

logging.basicConfig(filename='app2_extraction.log', level=logging.ERROR)

# Ensure that entire descriptions can be printed and used
pd.set_option('display.max_colwidth', None)
pd.set_option('display.max_rows', None)

SYSTEM_MESSAGE = "You are an expert botanist. You can extract and encode data from text to JSON."

# ZERO_SHOT_PROMPT = textwrap.dedent(f"""
#     ### Task ###
#     Create a JSON object where the key is the "code" and its corresponding value is a numeric score derived by applying the given rules to the respective descriptions. 
#     Ensure the JSON object includes all specified codes, with scores accurately matching their respective codes. 
#     If a score cannot be determined for a code, assign a value of null. 
#     Provide a complete and accurate JSON object without any extra text or fabricated data, and export it as a JSON object with no whitespace or trailing commas.
                        
#     ### Materials ###
#     A description of a species: {{subject_para}}\n
#     A JSON dictionary of trait codes ("code") and sets of rules ("rules") for encoding trait values:\n
#     {{appendix_2_subject_batch}}
#     Carefully analyse the description and apply the rules systematically before generating the JSON response.
# """)

# FEW_SHOT_PROMPT = textwrap.dedent(f"""
#     ### Task ###
#     Create a JSON object where the key is the "code" and its corresponding value is a numeric score derived by applying the given rules to the respective descriptions. 
#     Ensure the JSON object includes all specified codes, with scores accurately matching their respective codes. 
#     If a score cannot be determined for a code, assign a value of null. 
#     Provide a complete and accurate JSON object without any extra text or fabricated data, and export it as a JSON object with no whitespace or trailing commas.

#     ### Materials ###
#     A description of a species: {{subject_para}}\n
#     A JSON dictionary of trait codes ("code") and sets of rules ("rules") for encoding trait values:\n
#     {{appendix_2_subject_batch}}
#     Carefully analyse the description and apply the rules systematically before generating the JSON response.
    
#     #### Example 1 ###
#     description: "rachises 36.2(28.5–45.0) cm long, the  apices extended into an elongate cirrus, without reduced or vestigial pinnae, adaxially flat, abaxially with more or  less regularly arranged (at least proximally), distantly spaced clusters of dark–tipped, recurved spines, terminating  in a stub, without a shallow groove adaxially"
#     rules: "Petioles and rachises with long, straight, yellowish or brownish, black-tipped, usually solitary spines abaxially and laterally (0); petioles and rachises without long, straight, spines abaxially and laterally (1)"
#     code: "rachis"
#     rule "0" doesn't apply here, therefore it must be rule "1". output: "{{{{"rachis": "1"}}}}"  
    
#     ### Example 2 ###
#     description: "seeds 1 per fruit"
#     rules: "Seeds 1 per fruit (0); seeds 2-3 per fruit (1)"
#     code: "seeded"
#     The description clearly states that there is 1 seed per fruit, therefore assign rule "0". output: "{{{{"seeded": "0"}}}}" 
    
#     ### Example 3 ###
#     description: "leaf sheaths with numerous spicules borne on short, low, horizontal ridges, easily detached  and leaving the sheaths with ridges only"
#     rules: "Leaf sheath spines slender to stout, triangular, concave at the base proximally, horizontally spreading or downward pointing, scattered to dense, rarely in horizontal rows, yellowish-brown to dark brown (0); leaf sheath spines short to long, triangular, concave at the base proximally, usually horizontally spreading, scattered to dense, yellowish-brown to dark brown, slightly swollen-based or with an adjacent swelling (1); leaf sheath spines not as above (2)"
#     code: "dactyl"
#     The description does not match rules "0" or "1", therefore we must assign rule "2". output: "{{{{"dactyl": "2"}}}}"
                        
#     ### Example 4 ### 
#     description: " "
#     rules: "Staminate sepals as long as the petals, splitting almost to the base (0); staminate sepals usually shorter than the petals, cupular, 3-lobed at the apex (1); staminate sepals as long as petals (splitting not recorded) (2)"
#     code: "sepals"
#     There is no mention of sepals in the description, therefore we must assign "null". output: "{{{{"sepals": null}}}}"
                                
#     ### Example 5 ### where the value is multiple numbers
#     description: "Stems clustered, rarely solitary"
#     rules: "Stems solitary (0); stems clustered (1)"
#     code: "solclu"
#     This description applied to multiple rules, therefore assign both rules. output: "{{{{"solclu": "0,1"}}}}"
# """)

# COT_PROMPT = textwrap.dedent(f"""
#     1. List the questions that you would ask to score a plant according to the "rules" in this rubric. Ensure that each question is atomic and concerns only a single character (shape, structure, etc):\n
#     {{appendix_2_subject_batch}}
#     2. Now apply those questions to this description:\n
#     {{subject_para}}
#     3. Now combine the answers to give me a rubric score. If you cannot give a score, set the value to null.
#     4. Export the answers as a JSON object. Use the code as the key. Ensure no white space or trailing commas.
# """)

# COT_FEWSHOT_PROMPT = textwrap.dedent(f"""
#     ### Instructions ###
#     1. list the questions that you would ask to score a plant according to the "rules" in this rubric. Ensure that each question is atomic and concerns only a single character (shape, structure etc):\n
#     {{appendix_2_subject_batch}}
#     2. Now apply those questions to this description:\n
#     {{subject_para}}
#     3. Now combine the answers to give me a rubric score. If you cannot give a score, set the value to null. 
#     4. Export the answers as a JSON object. Use the code as the key. Ensure no white space or trailing commas. 

#     #### Example 1 ###
#     description: "rachises 36.2(28.5–45.0) cm long, the  apices extended into an elongate cirrus, without reduced or vestigial pinnae, adaxially flat, abaxially with more or  less regularly arranged (at least proximally), distantly spaced clusters of dark–tipped, recurved spines, terminating  in a stub, without a shallow groove adaxially"
#     rules: "Petioles and rachises with long, straight, yellowish or brownish, black-tipped, usually solitary spines abaxially and laterally (0); petioles and rachises without long, straight, spines abaxially and laterally (1)"
#     code: "rachis"
#     rule "0" doesn't apply here, therefore it must be rule "1". output: "{{{{"rachis": "1"}}}}"  
    
#     ### Example 2 ###
#     description: "seeds 1 per fruit"
#     rules: "Seeds 1 per fruit (0); seeds 2-3 per fruit (1)"
#     code: "seeded"
#     The description clearly states that there is 1 seed per fruit, therefore assign rule "0". output: "{{{{"seeded": "0"}}}}" 
    
#     ### Example 3 ###
#     description: "leaf sheaths with numerous spicules borne on short, low, horizontal ridges, easily detached  and leaving the sheaths with ridges only"
#     rules: "Leaf sheath spines slender to stout, triangular, concave at the base proximally, horizontally spreading or downward pointing, scattered to dense, rarely in horizontal rows, yellowish-brown to dark brown (0); leaf sheath spines short to long, triangular, concave at the base proximally, usually horizontally spreading, scattered to dense, yellowish-brown to dark brown, slightly swollen-based or with an adjacent swelling (1); leaf sheath spines not as above (2)"
#     code: "dactyl"
#     The description does not match rules "0" or "1", therefore we must assign rule "2". output: "{{{{"dactyl": "2"}}}}"
                        
#     ### Example 4 ### 
#     description: " "
#     rules: "Staminate sepals as long as the petals, splitting almost to the base (0); staminate sepals usually shorter than the petals, cupular, 3-lobed at the apex (1); staminate sepals as long as petals (splitting not recorded) (2)"
#     code: "sepals"
#     There is no mention of sepals in the description, therefore we must assign "null". output: "{{{{"sepals": null}}}}"
                                
#     ### Example 5 ### where the value is multiple numbers
#     description: "Stems clustered, rarely solitary"
#     rules: "Stems solitary (0); stems clustered (1)"
#     code: "solclu"
#     This description applied to multiple rules, therefore assign both rules. output: "{{{{"solclu": "0,1"}}}}"
# """)


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


# def llm_chat(ollama_client, model_name,system_mesage, prompt):
#     """
#     Function to generate a description using the Ollama model.
#     """
#     chat_completion = ollama_client.chat(
#         model=model_name,
#         messages=[
#             {"role": "system", "content": system_mesage},
#             {"role": "user", "content": prompt}
#         ],
#         options={"temperature": 0}
#     )
#     return chat_completion['message']['content']


# def check_valid_json(output, taxon_dict):
#     try:
#         sentence_dict = json.loads(output)
#         taxon_dict.update(sentence_dict)
#     except Exception as e:
#         logging.error(f"Failed to parse JSON {output} | Error: {e}")
#     return taxon_dict


def main():
    parser = argparse.ArgumentParser(description="Extracts qualitative traits")
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
    # Parse arguments
    args = parser.parse_args()
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
