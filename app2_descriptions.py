import argparse
import json
import numpy as np
import ollama
import pandas as pd
import re
import textwrap


def process_supp_data(file_path):
    """
    Function to read and tidy the supplementary data.
    """
    # Read in the formatted supplementary data
    supp_data = (
        pd.read_csv(file_path)
        .replace(to_replace=np.nan, value='')
        .drop('frucol', axis=1)
    )

    supp_data = supp_data.loc[:, ['taxon_name'] + list(supp_data.loc[:, 'solclu':'embryo'].columns)]

    # Tidy the supplementary data
    tidy_supp_data = (
        supp_data
        .melt(id_vars=["taxon_name"], var_name="code", value_name="value")
        .astype(str)
        .replace(r'\.0', '', regex=True)
    )

    return supp_data, tidy_supp_data


def process_appendix2(file_path):
    """
    Function to read and process the appendix 2 data.
    """
    df_app2 = (
        pd.read_csv(file_path)
        .drop(
            ['number', 'extra', 'subject_extract'],
            axis=1
        )
        .rename(columns={
            'description': 'rules',
            'subject_gen': 'subject'
            }
        )
        .iloc[:157, :]
    )
    return df_app2


def process_frucol(file_path):
    """
    Function to read and process the frucol data.
    """
    df_frucol = pd.read_csv(file_path)
    df_frucol = df_frucol[['taxon_name', 'frucol']].rename(columns={'frucol': 'output_sentence'}).dropna()
    df_frucol['subject'] = 'Fruit'
    return df_frucol


def clean_output(output):
    """
    Function to clean the output.
    """
    # Remove sentences containing the phrases 'not as above' or 'empty string'
    # because they indicate that the LLM did not find a matching rule or
    # returned an invalid response
    if re.search(r'not as above|empty string', output):
        output = ''

    # Ensures output is the rule only
    if re.search(r'\'.*?\'', output):
        output = re.search(r'\'(.*?)\'', output).group(1)

    if re.search(r'\d"\}\s*(.*)', output):
        output = re.search(r'\d"\}\s*(.*)', output).group(1)

    # Removes (0), (1), (2) etc. from the output to ensure the final sentence
    # is clean and readable
    if re.search(r'\(\d\)', output):
        output = re.sub(r'\(\d\)', "", output)

    # Check if the JSON object has a "value" field that is an empty string
    if re.search(r'"value": ""}', output):
        output = ""

    return output


def main():
    parser = argparse.ArgumentParser(
    description="Generates descriptions based on the appendix 2 data"
    )
    parser.add_argument(
        'input_file_app2', 
        help="Path to the input text file containing the appendix 2"
    )
    parser.add_argument(
        'input_file_supp_data', 
        help="Path to the input text file containing the supplementary data"
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

    # Ensure that entire descriptions can be printed and used
    pd.set_option('display.max_colwidth', None)

    # Set up connection to ollama
    ollama_client = ollama.Client(host='http://127.0.0.1:18199')

    # Read in the appendix
    df_app2 = process_appendix2(args.input_file_app2)

    # Use the function to read and tidy the supplementary data
    supp_data, tidy_supp_data = process_supp_data(args.input_file_supp_data)

    output_list = []

    # Iterate over each taxon_name and create a dictionary to store them
    for taxon_name in supp_data.taxon_name.unique():

        for code in df_app2.code.unique():

            subject = df_app2.loc[df_app2["code"] == code, "subject"].iloc[0]

            supp_codes = tidy_supp_data[
                (tidy_supp_data.code == code) &
                (tidy_supp_data.taxon_name == taxon_name)
            ][["code", "value"]].to_json(orient='records')
            supp_codes = json.loads(supp_codes)

            app2_rules = df_app2[df_app2.code == code][["code", "rules"]].to_json(
                orient='records')

            # if the value == '' then the output is an empty string. If the value contains
            # multiple values, then the output is a list of rules that match the values.
            # if the value contains a single value, then the output is the rule that matches
            if all(item['value'] == '' for item in supp_codes):
                output = ""
            elif any(',' in item['value'] for item in supp_codes):
                multi_val_prompt = textwrap.dedent(f"""
                    Using the "rules" in {app2_rules} and the corresponding "value"
                    in {supp_codes} output the rules that match the values.
                    Return these rules as a list, NO EXTRA TEXT.

                    ### Example ###
                    Using {{"code":"solclu","rules":"Stems solitary (0); stems
                    clustered (1)"}} and {{"code":"solclu","value":"0,1"}}, the
                    output would be ['Stems solitary', 'stems clustered'].
                    """)
                print(multi_val_prompt)
                chat_completion = ollama_client.chat(
                    model=args.model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert botanist.",
                        },
                        {
                            "role": "user",
                            "content": multi_val_prompt,
                        },
                    ],
                    options={"temperature": 0}
                )
                multi_val_output = chat_completion['message']['content']

                combine_multi_prompt = textwrap.dedent(f"""
                    ### Instructions ###
                    Combine the following sentences / clauses as concisely as 
                    possible: {multi_val_output}
                    Return the combination with NO EXTRA TEXT.

                    ### Example 1 ###
                    Using ['Stems solitary', 'stems clustered'], the output would 
                    be 'Stems clustered, sometimes solitary.'.

                    ### Example 2 ###
                    Using ['Proximalmost pinnae swept back across the sheath (on 
                    adult plants only)', 'proximalmost pinnae not swept back across 
                    the sheath'], the output would be 'Proximalmost pinnae 
                    sometimes swept back across the sheath.'.
                    """)
                print(combine_multi_prompt)
                chat_completion = ollama_client.chat(
                    model=args.model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert botanist.",
                        },
                        {
                            "role": "user",
                            "content": combine_multi_prompt,
                        },
                    ],
                    options={"temperature": 0}
                )
                output = chat_completion['message']['content']
            else:
                single_val_prompt = textwrap.dedent(f"""
                    ### Instructions ###
                    Using the "rules" in {app2_rules} and the corresponding "value"
                    in {supp_codes} output the rule that matches the value.
                    Return only an output sentence, NO EXTRA TEXT.

                    ### Example ###
                    Using {{"code":"rachil","rules":"Petioles and rachises with at
                    least some long, straight, flat, usually grouped spines
                    abaxially (0); petioles and rachises with whorls of long,
                    straight, flat spines (1); rachises without long, straight,
                    flat spines abaxially (2)"}} and {{"code":"rachil","value":"2"}},
                    the output would be 'rachises without long, straight, flat
                    spines abaxially' only.
                """)
                print(single_val_prompt)
                chat_completion = ollama_client.chat(
                    model=args.model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an expert botanist.",
                        },
                        {
                            "role": "user",
                            "content": single_val_prompt,
                        },
                    ],
                    options={"temperature": 0}
                )

                output = chat_completion['message']['content']

                # Clean the output
                output = clean_output(output)

            # Store the output in a dictionary
            loop_dict = {
                "taxon_name": taxon_name,
                "output_sentence": output,
                "subject": subject
            }
            print(loop_dict)
            output_list.append(loop_dict)

    df_output = pd.DataFrame(output_list)
    df_frucol = process_frucol(args.input_file_supp_data)
    df_output = pd.concat([df_output, df_frucol], ignore_index=True)

    df_output = df_output[df_output["output_sentence"].str.strip() != ""]

    # Save output DataFrame as a csv file
    df_output.to_csv(args.output_file, index=False)

if __name__ == "__main__":
    main()