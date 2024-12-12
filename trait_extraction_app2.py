import llm
import pandas as pd
import re
import json

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

    for subject in df_app2.subject.to_list():
        # Print each sentence and the corresponding code for each taxon
        # print(df_app2[df_app2.subject==subject][["description", "code"]])
        # Make a markdown table using those column headers and print
        appendix_2_subject = df_app2[df_app2.subject==subject][["description", "code"]].to_markdown(index=False)
        #print(appendix_2_subject)
        # Iterate through the rows in df_sentences that match the current subject and taxon_name
        for i, row in df_sentences[(df_sentences.category==subject) & (df_sentences.taxon_name==taxon_name)].iterrows():
            sentence_subject = row["sentence"]

            if re.match('stems', subject):

                prompt = f"""
                    You are an expert botanist. We're interested in characteristics about {subject} we want to extract JSON format data as defined in the table below
                    {appendix_2_subject}. Use abbreviation as your key. Your input sentence is "{sentence_subject}". Abbreviations in parentheses at the end of each variable are the values to be assigned to the subjects. The states of the variables here are scored as ‘(0)’ or ‘(1)’ etc.
                    Do not fabricate data and ensure the values correspond to the correct abbreviation, if values for traits are not recored, leave blank. Your answer must be as complete and accurate as possible. Ensure your output is strictly in valid JSON format, and do not include any extra text.
                    """

                response = model.prompt(prompt, temperature=0)
                output = response.text()
                #print(output)

                sentence_dict = json.loads(output)
                taxon_dict.update(sentence_dict)
            
    print(taxon_dict)
