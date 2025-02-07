import argparse
import re
import pandas as pd

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Process an appendix text file to structured (CSV) data file.")
    parser.add_argument('input_file', help="Path to the input text file")
    parser.add_argument('--quantitative',action='store_true', help='Process quantitative traits')
    parser.add_argument('output_file', help="Path to the output CSV file")
    
    # Parse arguments
    args = parser.parse_args()

    # List to hold the corrected lines
    corrected_lines = []

    # Variable to keep track of the current line
    current_line = ""

    with open(args.input_file, 'r', encoding='utf-8') as file_in:
        for line in file_in.readlines():
            # If the line starts with a number, it's a new entry
            if re.match(r'^\d+\.', line.strip()):
                    # If there is a current line being built, add it to corrected_lines
                    if current_line:
                        corrected_lines.append(current_line)
                    # Start a new entry with the current line
                    current_line = line.strip()
            else:
                # If it doesn't start with a number, append it to the current line
                current_line += " " + line.strip()            
        # Append the last processed line
        if current_line:
            corrected_lines.append(current_line)

    traitdata = list()
    # Each line consists of a number, description and column header
    for corrected_line in corrected_lines:
        # Define pattern
        if args.quantitative:
            pattern = r"(?P<number>\d+)\.\s+(?P<description>[\w\s,\-]+)(?:\s+\((?P<unit>\w+)\))?;\s+data taken from\s+(?P<source>[\w\s,]+)\.\s+\((?P<abbreviation>\w+)\)"
        else:
            pattern = r"^(?P<number>\d+)\.\s*(?P<description>.+?)\.\s*\((?P<code>[a-z]+)\)(?P<extra>\. .*)?$"
        # Apply the regex
        match = re.match(pattern, corrected_line)
        # Save the data extracted from the regex in dict form to the traitdata list 
        this_traitdata = match.groupdict()
        # Convert the number key from a str to an int
        this_traitdata['number'] = int(this_traitdata['number']) 
        traitdata.append(this_traitdata)

    # Make a pandas dataframe and save to file
    df_appendices = pd.DataFrame(traitdata)


    df_appendices['subject'] = [None]*len(df_appendices)

    pinna_filter = (df_appendices['description'].str.contains('pinna'))
    df_appendices.loc[pinna_filter, 'subject'] = 'Pinnae'

    rachis_apices_filter = (df_appendices['description'].str.contains('rachis apices', case=False))
    df_appendices.loc[rachis_apices_filter, 'subject'] = 'Rachis'
    
    multi_word_starts = []
    if args.quantitative:
        multi_word_starts = ['Staminate','Pistillate']

    else:
        seed_filter = (df_appendices['description'].str.contains('dorsal seed surfaces'))
        df_appendices.loc[seed_filter, 'subject'] = 'Seeds'
        multi_word_starts = ['Pistillate partial','Pistillate', 'Partial', 'Staminate', 'Neuter','Rachilla-subtending','Proximalmost','Distalmost','Fruiting']

    for multi_word_start in multi_word_starts:
        multi_word_start_len = len(multi_word_start.split(' '))
        multi_word_filter = (df_appendices['description'].str.startswith(multi_word_start) & df_appendices.subject.isnull())
        df_appendices.loc[multi_word_filter, 'subject'] = df_appendices[multi_word_filter].description.apply(lambda s: ' '.join(s.split(' ')[0:multi_word_start_len+1]))

    filter = (df_appendices.subject.isnull())
    df_appendices.loc[filter, 'subject'] = df_appendices[filter].description.apply(lambda s: s.split(' ')[0])

    print(df_appendices.groupby('subject').size())

    # Now standardise the subjects
    from term_mapper import term_mapping
    df_appendices['subject_standardised'] = df_appendices.subject.map(term_mapping)
    print(df_appendices.groupby('subject_standardised').size())

    # Output as a csv file
    df_appendices.to_csv(args.output_file, index=False)

if __name__ == "__main__":
    main()