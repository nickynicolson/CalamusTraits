import llm
import pandas as pd
import re
import json
from time import sleep

# Choose model
model = llm.get_model("groq-llama3.1-70b")

# Read the files
df_sentences = pd.read_csv("data/sentences_cat.txt")
df_app1 = pd.read_csv("data/appendix_1.txt")

# print(df_app1)

print("Taxon names:", df_sentences.taxon_name.unique()) 
print("Subjects:", df_app1.subject.to_list())

df_output = pd.DataFrame()

for taxon_name in df_sentences.taxon_name.unique():
    print(taxon_name)

    taxon_dict = dict()
    taxon_dict['taxon_name'] = taxon_name

    for subject in df_app1.subject.unique():
        mask = (df_sentences.category==subject) & (df_sentences.taxon_name==taxon_name) & (df_sentences.sentence.str.contains("[0-9]"))
        subject_para = " ".join(df_sentences[mask]['sentence'].to_list())
        #print(subject, subject_para)

        appendix_1_subject = df_app1[df_app1.subject==subject][["description", "abbreviation"]]
        for i, row in appendix_1_subject.iterrows():
            
            prompt = f"""
                You are an expert botanist. You can extract and encode data from text. 
                You are supplied with the description of a species ("description"), a code for a trait ("abbreviation").
                Make a JSON dictionary with the key code and the corresponding value from the description.
                Do not fabricate data and ensure the values correspond to the correct code. If you cannot score the variable, set the value to null. Your answer must be as complete and accurate as possible. Ensure your output is strictly in valid JSON format, and do not include any extra text. Follow the format of the following examples.

                ### Example 1:
                description: "Stems clustered, climbing, 3.0 m long."
                code: "stemlength"
                response: {{"stemlength": "3.0 m"}}
                
                ### Example 2:
                description: "pinnae 5(5–6) per side of rachis."
                code: "numpin"
                response: {{"numpin": "5(5-6)"}}

                ### Example 3:
                description: "pistillate rachillae 0.8 cm long."
                code: "psraclen"
                response: {{"psraclen": "0.8 cm"}}

                Generate the JSON for the following:
                description: {subject_para}\n
                code: {row['abbreviation']}\n
            """

            # print(f"Prompt: {prompt}")

            response = model.prompt(prompt, temperature=0)
            output = response.text()

            try:
                sentence_dict = json.loads(output)
                taxon_dict.update(sentence_dict)
            except:
                print(output)

            sleep(3)
            
    print(json.dumps(taxon_dict, indent=4)) # Makes the output easier to read
    print('-'*80)

    # Turn taxon_dict into a pandas dataframe and join it to the output dataframe
    df_taxon = pd.DataFrame([taxon_dict])            
    df_output = pd.concat([df_output, df_taxon])

print(df_output)
df_output.to_csv('data/extracted_traits_app1.csv', index=False)