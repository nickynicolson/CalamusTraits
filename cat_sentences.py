import argparse
import pandas as pd
import llm 
from time import sleep

def categoriseSentence(s, subjects, model):
    category = None
    # Set up system and user prompts
    system = "You are an expert botanist."
    prompt = """Categorise this sentence \"{}\" into one of 
    the following categories {}.
    Respond only with the category name."""
    response = model.prompt(system=system, prompt=prompt.format(s, ','.join(subjects)))
    print(response)
    if response in subjects:
        category = response
    else:
        print('not found')
    return category

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Process an appendix text file to structured (CSV) data file.")
    parser.add_argument('input_file_sentences', help="Path to the sentence input text file")
    parser.add_argument('input_file_appendix', help="Path to the appendix input text file")
    parser.add_argument('output_file', help="Path to the output CSV file")
    
    # Parse arguments
    args = parser.parse_args()

    # Read sentence data
    df = pd.read_csv(args.input_file_sentences)

    # Read appendix subjects, which we are using as metadata (the
    # subjects are used as the potential categories for the sentences) 
    df_meta = pd.read_csv(args.input_file_appendix)
    subjects = df_meta.subject.to_list()

    # Set up model and prompts
    model = llm.get_model("groq-llama3-70b")
    system = "You are an expert botanist."
    prompt = """Categorise this sentence \"{}\" into one of 
    the following categories {}.
    Respond only with the category name. 
    The category name that you return MUST be one of the categories supplied"""

    # Get all the sentences that we want to categorise
    sentences = df.sentence.to_list()
    # Make a dict to hold the mapping
    sentences_mapper = dict()
    # Loop over sentences, sending each to model for categorisation
    for sentence in sentences:
        response = model.prompt(system=system, prompt=prompt.format(sentence, ','.join(subjects)))
        print(response)
        if response.text().lower() in subjects:
            sentences_mapper[sentence] = response.text().lower()
        else:
            print('{} not found in {}'.format(response, subjects))

    df['category'] = df.sentence.map(sentences_mapper)

    df.to_csv(args.output_file)

if __name__ == "__main__":
    main()