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
                ### Task ###
                Create a JSON object where the key is the "code" and its corresponding value is a numeric score derived by applying the given rules to the respective descriptions. 
                Ensure the JSON object includes all specified codes, with scores accurately matching their respective codes. 
                If a score cannot be determined for a code, assign a value of null. 
                Provide a complete and accurate JSON object without any extra text or fabricated data, and export it as a JSON object with no whitespace or trailing commas.

                ### Materials ###
                A description of a species: {subject_para}\n
                A JSON dictionary of trait codes ("code") and sets of rules ("rules") for encoding trait values:\n
                {appendix_2_subject_batch}
                Carefully analyse the description and apply the rules systematically before generating the JSON response.
                
                #### Example 1 ###
                description: "rachises 36.2(28.5–45.0) cm long, the  apices extended into an elongate cirrus, without reduced or vestigial pinnae, adaxially flat, abaxially with more or  less regularly arranged (at least proximally), distantly spaced clusters of dark–tipped, recurved spines, terminating  in a stub, without a shallow groove adaxially"
                rules: "Petioles and rachises with long, straight, yellowish or brownish, black-tipped, usually solitary spines abaxially and laterally (0); petioles and rachises without long, straight, spines abaxially and laterally (1)"
                code: "rachis"
                rule "0" doesn't apply here, therefore it must be rule "1". output: "{{"rachis": "1"}}"  
                
                ### Example 2 ###
                description: "seeds 1 per fruit"
                rules: "Seeds 1 per fruit (0); seeds 2-3 per fruit (1)"
                code: "seeded"
                The description clearly states that there is 1 seed per fruit, therefore assign rule "0". output: "{{"seeded": "0"}}" 
                
                ### Example 3 ###
                description: "leaf sheaths with numerous spicules borne on short, low, horizontal ridges, easily detached  and leaving the sheaths with ridges only"
                rules: "Leaf sheath spines slender to stout, triangular, concave at the base proximally, horizontally spreading or downward pointing, scattered to dense, rarely in horizontal rows, yellowish-brown to dark brown (0); leaf sheath spines short to long, triangular, concave at the base proximally, usually horizontally spreading, scattered to dense, yellowish-brown to dark brown, slightly swollen-based or with an adjacent swelling (1); leaf sheath spines not as above (2)"
                code: "dactyl"
                The description does not match rules "0" or "1", therefore we must assign rule "2". output: "{{"dactyl": "2"}}"
                                     
                ### Example 4 ### 
                description: " "
                rules: "Staminate sepals as long as the petals, splitting almost to the base (0); staminate sepals usually shorter than the petals, cupular, 3-lobed at the apex (1); staminate sepals as long as petals (splitting not recorded) (2)"
                code: "sepals"
                There is no mention of sepals in the description, therefore we must assign "null". output: "{{"sepals": null}}"
                                             
                ### Example 5 ### where the value is multiple numbers
                description: "Stems clustered, rarely solitary"
                rules: "Stems solitary (0); stems clustered (1)"
                code: "solclu"
                This description applied to multiple rules, therefore assign both rules. output: "{{"solclu", "0,1"}}"
                """)

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
df_output.to_csv('prompt-engineering-trials-appendix-2/outputs/qualitative_traits_few-shot.csv', index=False)
