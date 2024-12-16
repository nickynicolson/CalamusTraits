import llm
import pandas as pd
import re
import json
from time import sleep
from transformers import AutoTokenizer
import textwrap

def count_tokens(prompt, model_name="gpt2"):
    # Load the tokenizer for the specified model
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    tokens = tokenizer.encode(prompt)
    return len(tokens)

# Choose model


# model_name = "llama3.1-70b"
model_name = "llama-3.3-70b"
groq_model_name = f"groq-{model_name}"

model = llm.get_model(groq_model_name)

# Read the files and enter the prompt
with open("data/appendix_2.txt", "r") as appendix_2:
    appendix_2 = appendix_2.read()

with open("data/sentences_cat.txt", "r") as sentences_cat:
    sentences_cat = sentences_cat.read()

df_sentences = pd.read_csv("data/sentences_cat.txt")
df_app2 = pd.read_csv("data/appendix_2.txt")

df_output = pd.DataFrame()

for taxon_name in df_sentences.taxon_name.unique():
    print(taxon_name)

    taxon_dict = dict()
    taxon_dict['taxon_name'] = taxon_name

    for subject in df_app2.subject.unique():
        subject_para = " ".join(df_sentences[(df_sentences.category==subject) & (df_sentences.taxon_name==taxon_name)]['sentence'].to_list())
        # print(subject, subject_para)

        # Batch size
        batch_size = 10

        df_app2_subject = df_app2[df_app2.subject==subject][["code", "description"]].rename(columns={'description':'rules'})
        # Split the DataFrame into batches of length batch_size using list comprehension
        batches = [df_app2_subject[i:i + batch_size] for i in range(0, len(df_app2_subject), batch_size)]

        for i, batch in enumerate(batches):
            print(f"Batch {i + 1}:\n{batch}\n")
            appendix_2_subject_batch = batch.to_markdown(index=False)
            # print(appendix_2_subject_batch)

            codes_len = len(batch)
            prompt_outline = textwrap.dedent("""
                You are an expert botanist. You can extract and encode data from text to JSON. 
                Your supplies: 
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
            print(prompt)
            print(count_tokens(prompt))

            response = model.prompt(prompt, temperature=0)
            output = response.text()
            print(output)

            try:
                sentence_dict = json.loads(output)
                print(f"Asked for {codes_len} codes")
                print(f"Received {len(sentence_dict)} codes")
                if codes_len != len(sentence_dict):
                    print("Incomplete extraction" + '*'*60)
                taxon_dict.update(sentence_dict)
            except:
                print(output)
            
            sleep(2)

    df_taxon = pd.DataFrame([taxon_dict])            
    df_output = pd.concat([df_output, df_taxon])

print(df_output)
df_output.to_csv('data/etxracted_traits.csv', index=False)
