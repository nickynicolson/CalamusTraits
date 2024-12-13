import llm
import pandas as pd
import re
import json
from time import sleep

# Choose model
model = llm.get_model("groq-llama3.1-70b")

# Read the files and enter the prompt
with open("data/appendix_2.txt", "r") as appendix_2:
    appendix_2 = appendix_2.read()

with open("data/sentences_cat.txt", "r") as sentences_cat:
    sentences_cat = sentences_cat.read()

df_sentences = pd.read_csv("data/sentences_cat.txt")
df_app2 = pd.read_csv("data/appendix_2.txt")

for taxon_name in df_sentences.taxon_name.unique():
    print(taxon_name)

    taxon_dict = dict()

    for subject in df_app2.subject.unique():
        subject_para = " ".join(df_sentences[(df_sentences.category==subject) & (df_sentences.taxon_name==taxon_name)]['sentence'].to_list())
        print(subject, subject_para)

    
        appendix_2_subject = df_app2[df_app2.subject==subject][["description", "code"]]
        for i, row_outer in appendix_2_subject.iterrows():

            prompt = f"""
                You are an expert botanist. You can extract and encode data from text. 
                You are supplied with the description of a species ("description"), a code for a trait ("code") and a set of rules ("rules") about the values used to encode the trait. 
                Make a JSON dictionary with the key code and a numeric value built by applying the rules to the description.
                Do not fabricate data and ensure the values correspond to the correct code. If you cannot score the variable, set the value to none. Your answer must be as complete and accurate as possible. Ensure your output is strictly in valid JSON format, and do not include any extra text.
                description: {subject_para}\n
                code: {row_outer["code"]}\n
                rules: {row_outer["description"]}\n
                """

            print(prompt)

            response = model.prompt(prompt, temperature=0)
            output = response.text()
            print(output)

            try:
                sentence_dict = json.loads(output)
                taxon_dict.update(sentence_dict)
            except:
                print(output)
            
            sleep(2)
            
    print(taxon_dict)
