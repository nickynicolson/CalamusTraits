import llm
import pandas as pd
import re
import json

# Choose model
model = llm.get_model("groq-llama3.1-70b")

# Read the files and enter the prompt
with open("data/appendix_1.txt", "r") as appendix_1:
    appendix_1 = appendix_1.read()

with open("data/sentences_cat.txt", "r") as sentences_cat:
    sentences_cat = sentences_cat.read()

df_sentences = pd.read_csv("data/sentences_cat.txt")
#print(df_sentences[df_sentences.sentence.str.contains("pistillate rachillae")])
df_app1 = pd.read_csv("data/appendix_1.txt")

for taxon_name in df_sentences.taxon_name.unique():
    print(taxon_name)

    taxon_dict = dict()
    
    for subject in df_app1.subject.to_list():
        # Print just the relevant columns
        #print(df_app1[df_app1.subject==subject][["description", "unit", "abbreviation"]])
        # Make a markdown table using those column headers and print
        appendix_1_subject = df_app1[df_app1.subject==subject][["description", "unit", "abbreviation"]].to_markdown(index=False)
        #print(appendix_1_subject)
        # Iterate through the rows in df_sentences that match the current subject and taxon_name
        for i, row in df_sentences[(df_sentences.category==subject) & (df_sentences.taxon_name==taxon_name)].iterrows():
            sentence_subject = row["sentence"]

            print(f"Current subject: {subject}")

            # Only use the sentences that contain numbers
            if re.match('.*[0-9].*', sentence_subject):

                prompt = f"""
                You are an expert botanist. We're interested in measurements about {subject} we want to extract JSON format data as defined in the table below
                {appendix_1_subject}. Use abbreviation as your key. Your input sentence is "{sentence_subject}". 
                Do not fabricate data and ensure the values correspond to the correct abbreviation, if values for traits are not recored, leave blank. Respond only with JSON.
                """

                print(f"Prompt: {prompt}")

                response = model.prompt(prompt, temperature=0)
                output = response.text()
                # transform output (a string) into json
                sentence_dict = json.loads(output)
                taxon_dict.update(sentence_dict)
                #print(output)
            
    print(taxon_dict)
    print('-'*80)
