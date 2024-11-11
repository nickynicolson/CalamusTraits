import argparse
import re
import pandas as pd

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Process an appendix text file to structured (CSV) data file.")
    parser.add_argument('input_file', help="Path to the input text file")
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
        pattern = r"^(?P<number>\d+)\.\s*(?P<description>.+?)\.\s*\((?P<code>[a-z]+)\)(?P<extra>\. .*)?$"
        # Apply the regex
        match = re.match(pattern, corrected_line)
        # Save the data extracted from the regex in dict form to the traitdata list 
        traitdata.append(match.groupdict())

    # Make a pandas dataframe and save to file
    df = pd.DataFrame(traitdata)
    df.to_csv(args.output_file, index=False)

if __name__ == "__main__":
    main()