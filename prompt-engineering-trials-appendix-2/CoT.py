import pandas as pd
import json
import textwrap
import ollama

# Ensure that entire descriptions can be printed and used
pd.set_option('display.max_colwidth', None)
pd.set_option('display.max_rows', None) 

# Set up link to model
ollama_client = ollama.Client(host='http://127.0.0.1:18199')

# Convert the csv files into a pandas dataframes, remove unwanted columns, and rename columns
df_sentences = (
    pd.read_csv("data/sentences.txt")
    .drop(
        ['sentence_count', 'sentence_position', 'subject'],
        axis=1
    )
    .rename(columns={'subject_standardised': 'subject'})
)

df_app2 = (
    pd.read_csv("data/appendix_2.txt")
    .drop(
        ['number', 'extra', 'subject'], 
        axis=1
    )
    .rename(columns={
        'description': 'rules',
        'subject_standardised': 'subject'
        }
    )
)

# Create an empty dataframe to store the output
df_output = pd.DataFrame()

# Iterate over each unique species
for taxon_name in df_sentences.taxon_name.unique():
    print(taxon_name)

    taxon_dict = dict()
    taxon_dict['taxon_name'] = taxon_name

    # Iterate over each subject in appendix_2 df
    for subject in df_app2.subject.unique():
        # Sentences about a specific species and subject and joined together into a paragraph
        subject_para = " ".join(df_sentences[(df_sentences.subject==subject) & (df_sentences.taxon_name==taxon_name)]['sentence'].to_list())
        # print(f'{subject}: {subject_para}')

        # Batch size
        batch_size = 8 

        # Filter df_app2 to get rows matching current subject and code, selecting only the 'code' and 'rules' columns
        df_app2_subject = df_app2[df_app2.subject==subject][["code", "rules"]]

            #Split the DataFrame into batches of length batch_size using list comprehension
        batches = [df_app2_subject[i:i + batch_size] for i in range(0, len(df_app2_subject), batch_size)]

        # Iterates through each batch and coverts to json
        for batch in batches:
            appendix_2_subject_batch = batch.to_json(orient="records", indent=4)
            #print(appendix_2_subject_batch)

            codes_len = len(batch)

            # textwrap.dedent strips out the indenting spaces in the multline text string
            prompt = textwrap.dedent(f"""
                1. list the questions that you would ask to score a plant according to the "rules" in this rubric. Ensure that each question is atomic and concerns only a single character (shape, structure etc):\n
                {appendix_2_subject_batch}
                2. Now apply those questions to this description:\n
                {subject_para}
                3. Now combine the answers to give me a rubric score. If you cannot give a score, set the value to null. 
                4. Export the answers as a JSON object. Use the code as the key. Ensure no white space or trailing commas. 
                """
            )

            # print(prompt)

            chat_completion = ollama_client.chat(
                            model="llama3.3", 
                            messages=[
                                {
                                    "role": "system", 
                                    "content": "You are an expert botanist. You can extract and encode data from text to JSON.",
                                },
                                {
                                    "role": "user",
                                    "content": prompt,
                                },
                            ],
                            options={"temperature": 0},
                            format="json"
                        )

            output = chat_completion['message']['content']

            print(output)

            try:
                sentence_dict = json.loads(output)
                if codes_len != len(sentence_dict):
                    print("Incomplete extraction" + '*'*60)
            except json.JSONDecodeError:
                print("Invalid JSON output received", output)
                # print(f"Asked for {codes_len} codes")
                # print(f"Received {len(sentence_dict)} codes")
            taxon_dict.update(sentence_dict)

    print(json.dumps(taxon_dict, indent=4)) # Makes the output easier to read
    print('-'*80)

    df_taxon = pd.DataFrame([taxon_dict])            
    df_output = pd.concat([df_output, df_taxon])

print(df_output)

# Save the output in the data folder 
df_output.to_csv('prompt-engineering-trials-appendix-2/outputs/qualitative_traits_CoT.csv', index=False)
