import argparse
import pandas as pd
import json
import textwrap
import ollama

SYSTEM_MESSAGE = """
You are an expert botanist. You can extract and encode data from text to JSON.
"""


def main():
    parser = argparse.ArgumentParser(
        description="Extracts quantitative traits"
    )
    parser.add_argument(
        'input_file_sentences',
        help="Path to the input text file containing the sentences"
    )
    parser.add_argument(
        'input_file_app1',
        help="Path to the input text file containing the appendix1"
    )
    parser.add_argument(
        'output_file',
        help="Path to the output CSV file where the data is saved"
    )
    parser.add_argument(
        '--model_name',
        default='llama3.3',
        help="Name of the model to use for the chat completion "
             "(default: 'llama3.3')"
    )

    # Parse arguments
    args = parser.parse_args()

    # Set up link to model
    ollama_client = ollama.Client(host='http://127.0.0.1:18199')

    # Read the files
    df_sentences = pd.read_csv(args.input_file_sentences)#.drop(columns=['subject'])
    print(df_sentences.columns)
    # If subject_extract is empty, remove those rows
    df_sentences = df_sentences[~df_sentences.subject_extract.isna() & (df_sentences.subject_extract.str.strip() != "")]
    print(f"Number of rows in df_sentences: {len(df_sentences)}")
    df_app1 = pd.read_csv(args.input_file_app1)

    # Set up a dataframe to store the output
    df_output = pd.DataFrame()

    # Iterate over each unique species
    for taxon_name in df_sentences.taxon_name.unique():
        # Set up dictionary to store species names
        taxon_dict = {'taxon_name': taxon_name}

        for subject in df_app1.subject_extract.unique():
            mask = (
                (df_sentences.subject_extract == subject) &
                (df_sentences.taxon_name == taxon_name) &
                (df_sentences.sentence.str.contains("[0-9]"))
            )
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
                        }
                    ],
                    options={"temperature": 0},
                    format="json"
                )

                output = chat_completion['message']['content']

                try:
                    sentence_dict = json.loads(output)
                    taxon_dict.update(sentence_dict)
                except:
                    print(output)
   
        print(json.dumps(taxon_dict, indent=4))
        print('-' * 80)

        # Turn taxon_dict into a pandas dataframe and join it to the output
        df_taxon = pd.DataFrame([taxon_dict])
        df_output = pd.concat([df_output, df_taxon])

    df_output.to_csv(args.output_file, index=False)


if __name__ == "__main__":
    main()
