import argparse
import numpy as np
import ollama
import pandas as pd
import re
import textwrap


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


def process_output(output):
    # Check if the output contains any digits
    if not re.search(r'\d', output):
        output = ''

    # Remove .0 from numpin
    if re.search(r'Number of pinnae', output):
        output = re.sub(r'\.0', '', output)
    
    return output


def main():
    parser = argparse.ArgumentParser(
    description="Generates descriptions based on the appendix 1 data"
    )
    parser.add_argument(
        'input_file_app1', 
        help="Path to the input text file containing the appendix1"
    )
    parser.add_argument(
        'input_file_supp_data', 
        help="Path to the input CSV file containing the supplementary data"
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

    # Set up ollama connection
    ollama_client = ollama.Client(host='http://127.0.0.1:18199')

    # Read in the appendix 1 data
    df_app1 = process_appendix1(args.input_file_app1)

    # Read in the supplementary data and tidy it 
    supp_data, tidy_supp_data = process_supp_data(args.input_file_supp_data)

    # Create an empty list to store the output
    output_list = []

    # Iterate over each taxon_name and create a dictionary to store them
    for taxon_name in supp_data.taxon_name.unique():

        # Iterate over each code in the app1 DataFrame
        for code in df_app1.code.unique():
            # Look up subject that relates to code
            subject = df_app1.loc[df_app1["code"] == code, "subject"].iloc[0]

            # Filter the supplementary data for the specific code and taxon_name 
            # And convert to json
            supp_codes = tidy_supp_data[
                (tidy_supp_data.code == code) & 
                (tidy_supp_data.taxon_name == taxon_name)
            ][["code", "value"]].to_json(orient='records')

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
            chat_completion = ollama_client.chat(
                model=args.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert botanist.",
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                options={"temperature": 0}
            )
            print(prompt)
            # Get the output from the chat completion
            output = chat_completion['message']['content']

            # Process the output
            output = process_output(output)

            # Store the output in a dictionary
            loop_dict = {
                "taxon_name": taxon_name,
                "output_sentence": output,
                "subject": subject
            }
            print(loop_dict)
            # Append the dictionary to the output list
            output_list.append(loop_dict)

    # Create a DataFrame from the output list
    df_output = pd.DataFrame(output_list)

    # Remove any rows where the output_sentence is an empty string
    df_output = df_output[df_output["output_sentence"].str.strip() != ""]

    # Save output DataFrame as a csv file
    df_output.to_csv(args.output_file, index=False)

if __name__ == "__main__":
    main()