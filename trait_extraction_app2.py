import os
from groq import Groq
import groq
import pandas as pd
import re
import json
from time import sleep
from transformers import AutoTokenizer
import textwrap

# Define a function to count the number of tokens in the prompt
def count_tokens(prompt, model_name="gpt2"):
    # Load the tokenizer for the specified model
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokens = tokenizer.encode(prompt)
    # Return the number of tokens
    return len(tokens)

# Choose model
model_name = "llama-3.3-70b-versatile"

client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),  # GROQ API key is set as an environment variable
    max_retries=5,  # Specifies the max. number of retries if the request fails
)

# Read the files
with open("data/appendix_2.txt", "r") as appendix_2:
    appendix_2 = appendix_2.read()

with open("data/sentences_cat.txt", "r") as sentences_cat:
    sentences_cat = sentences_cat.read()

# Convert the csv files into a pandas dataframes
df_sentences = pd.read_csv("data/sentences_cat.txt")
df_app2 = pd.read_csv("data/appendix_2.txt")

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
        subject_para = " ".join(df_sentences[(df_sentences.category==subject) & (df_sentences.taxon_name==taxon_name)]['sentence'].to_list())
        print(subject, subject_para)
        # Batch size
        batch_size = 10    # 10 Rows per batch

        # Filter df_app2 to get rows matching current subject, selecting only the 'code' and 'description' columns & rename these columns
        df_app2_subject = df_app2[df_app2.subject==subject][["code", "description"]].rename(columns={'description':'rules'})
        # Split the DataFrame into batches of length batch_size using list comprehension
        batches = [df_app2_subject[i:i + batch_size] for i in range(0, len(df_app2_subject), batch_size)]

        # Iterates through each batch and coverts to markdown table
        for i, batch in enumerate(batches):
            # print(f"Batch {i + 1}:\n{batch}\n")
            appendix_2_subject_batch = batch.to_markdown(index=False)
            # print(appendix_2_subject_batch)

            codes_len = len(batch)
            # textwrap.dedent strips out the indenting spaces in the multline text string
            prompt_outline = textwrap.dedent("""
                Your working materials: 
                a description of a species ("description"), 
                a markdown table containing codes for a trait ("code") and sets of rules ("rules") 
                about the description values used to encode the trait. 
                Your task:
                Make a JSON dictionary with the key code and a numeric value built by applying the rules 
                to the description.
                The JSON dictionary MUST contain every key specified in codes 
                If you cannot score the variable, set the value to none. 
                Do not fabricate data. 
                Ensure the values correspond to the correct code. 
                Your answer must be as complete and accurate as possible. 
                Ensure your output is strictly in valid JSON format (not in a fenced JSON block).
                Do not include any extra text.
                description: {subject_para}\n
                code and rules table:\n
                {appendix_2_subject_batch}
                """)
            prompt = prompt_outline.format(subject_para=subject_para, appendix_2_subject_batch=appendix_2_subject_batch)
            
            try:

                chat_completion = client.chat.completions.create(
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
                    model=model_name,
                )
                output = chat_completion.choices[0].message.content

                sentence_dict = json.loads(output)
                # print(f"Asked for {codes_len} codes")
                # print(f"Received {len(sentence_dict)} codes")
                if codes_len != len(sentence_dict):
                    print("Incomplete extraction" + '*'*60)
                taxon_dict.update(sentence_dict)
                sleep(10)
            except groq.APIConnectionError as e:
                print("The server could not be reached")
                print(e.__cause__)  # an underlying Exception, likely raised within httpx.
            except groq.RateLimitError as e:
                print("A 429 status code was received; we should back off a bit.")
            except groq.APIStatusError as e:
                print("Another non-200-range status code was received")
                print(e.status_code)
                print(e.response)

    df_taxon = pd.DataFrame([taxon_dict])            
    df_output = pd.concat([df_output, df_taxon])

print(df_output)
df_output.to_csv('data/extracted_traits.csv', index=False)
