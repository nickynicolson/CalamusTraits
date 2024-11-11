import argparse
from pypdf import PdfReader
import pandas as pd
pd.set_option('display.max_columns', None)
pd.set_option('display.max_colwidth', None)
import re

species_names = ['Calamus concolor',
            'Calamus disjunctus',
            'Calamus glaucescens',
            'Calamus hallierianus',
            'Calamus pseudoconcolor',
            'Calamus subangulatus']

# Define a function that will help us clean boilerplate text from lines
def cleanLine(s, page_number):
  cleaned = s
  if s.startswith('HENDERSON {page_number}'.format(page_number=page_number)) and '© 2020 Magnolia Press' in s:
    cleaned = s.split('© 2020 Magnolia Press')[1]
  elif s.startswith('A REVISION OF CALAMUS'):
    try:
      cleaned = s.split('•   {page_number}'.format(page_number=page_number))[1]
    except:
      print(s, page_number)
  else:
    cleaned = s
  return cleaned

# Utility functions to extract number and name from the line indicating the
# start of a taxonomic treatment
def extractSpeciesNumberAndName(s):
  speciesNumberAndName = None
  if s is not None:
    patt = r'^(?P<species_id>[0-9]+)\s*\.\s+(?P<species_name>Calamus\s+[a-z]+)\s+.*$'
    m = re.match(patt, s)
    if m is not None:
      speciesNumberAndName = m.groupdict()['species_id'] + ' ' + m.groupdict()['species_name']
  return speciesNumberAndName

def extractInfraSpeciesNumberAndName(s):
  infraspeciesNumberAndName = None
  if s is not None:
    patt = r'^(?P<species_id>[0-9]+[a-z])\s*\.\s+(?P<species_name>Calamus\s+[a-z]+\s+subsp\.\s+[a-z]+).*$'
    m = re.match(patt, s)
    if m is not None:
      infraspeciesNumberAndName = m.groupdict()['species_id'] + ' ' + m.groupdict()['species_name']
  return infraspeciesNumberAndName

def identifySections(df):
    section_mapper={'abstract':'Abstract',
        'introduction':'Introduction',
        'materials_and_methods':'Materials and Methods',
        'distribution':'Distribution',
        'morphology':'Morphology',
        'taxonomic_treatment':'Taxonomic Treatment',
        'acknowledgements':'Acknowledgements',
        'references':'References',
        'appendix_1':'Appendix I. Quantitative variables',
        'appendix_2':'Appendix II. Qualitative Variables',
        'appendix_3':'Appendix III. Excluded and Uncertain Names',
        'appendix_4':'Appendix IV . Species by Region/Island/Country',
        'appendix_6':'Appendix VI. Plates'}

    # Add a column to df_lines so that we can categorise the line
    # into its enclosing section
    df['section']=[None]*len(df)

    # Loop over the section mapper and update the df_lines dataframe with
    # the appropriate section
    for key, value in section_mapper.items():
        mask=(df.line_cleaned.str.match(r'^{}\s*$'.format(value.replace('.','\\.')), case=False, flags=0, na=None))
        df.loc[mask, 'section'] = key

    # Now we have the start lines for each section, we can use the
    # pandas filldown function to categrise each line
    df.section = df.section.ffill()
   
    return df

def identifyTreatments(df):
    # Define regular expression patterns to find the start lines of taxon treatments
    species_treatment_patt = r'^[0-9]+\s*\.\s+Calamus\s+.*$'
    infraspecies_treatment_patt = r'^[0-9]+[a-z]\s*\.\s+Calamus\s+[a-z]+\s+subsp\.\s+.*$'

    # Make a new column to hold the taxon_id_and_name
    df['taxon_id_and_name']=[None]*len(df)
    #  As we're using filldown, we want to set the endpoint after the taxon
    # treatments. This prevents the last taxon treatment being filled down right
    # to the end of the article
    mask=(df.line_cleaned.str.match(r'^Acknowledgements\s*$'))
    df.loc[mask, 'taxon_id_and_name'] = 'na'

    # Find the lines which indicate the start of an infraspecific treatment
    mask=(df.line_cleaned.str.match(infraspecies_treatment_patt, case=True, flags=0, na=None))
    # Use the utility function to extract the taxon name and number fromthe text
    # of the line
    df.loc[mask, 'taxon_id_and_name'] = df[mask].line_cleaned.apply(extractInfraSpeciesNumberAndName)

    # As above - find the lines which indicate the start of an species treatment
    mask=(df.line_cleaned.str.match(species_treatment_patt, case=True, flags=0, na=None))
    # Use the utility function to extract the taxon name and number from the text
    # of the line
    mask = (df.taxon_id_and_name.isnull() & mask)
    df.loc[mask, 'taxon_id_and_name'] = df[mask].line_cleaned.apply(extractSpeciesNumberAndName)

    # Fill down the taxon name and number values
    df.taxon_id_and_name = df.taxon_id_and_name.ffill()

    mask = (df.taxon_id_and_name.notnull() & (df.taxon_id_and_name.isin(['na']) == False))
    df.loc[mask,'taxon_id'] = df[mask].taxon_id_and_name.apply(lambda x: x.split(' ', maxsplit=1)[0])
    df.loc[mask,'taxon_name'] = df[mask].taxon_id_and_name.apply(lambda x: x.split(' ', maxsplit=1)[1])

    return df

def identifyTreatmentSubsections(df):
    treatment_subsection_mapper={'nomenclatural_details':r'^[0-9]+[a-z]?\s*\.\s+Calamus',
        'description':r'^\s*(Stems|Pinnae)',
        'distribution':r'^\s*Distribution',
        'taxonomic_notes':r'^\s*Taxonomic notes',
        'subspecific_variation':r'^\s*Subspecific variation',
        'key_to_subspecies':r'^\s*Key to the subspecies of'}
   
    # Add a column to df_lines so that we can categorise the taxonomic treatment line
    # into its enclosing treatment_subsection
    df['treatment_subsection']=[None]*len(df)

    # Loop over the treatment_subsection_mapper mapper and update the df_lines dataframe with
    # the appropriate treatment_subsection
    for key, value in treatment_subsection_mapper.items():
        # make a mask with the regular expression in "value"
        mask=(df.line_cleaned.str.match(value, case=True, flags=0, na=None) & (df.section == "taxonomic_treatment"))
        # Use the mask to find the matching lines and write the key into treatment_subsection
        df.loc[mask, 'treatment_subsection'] = key

    # Filldown the treatment_subsection column to fill missing values
    df.treatment_subsection = df.treatment_subsection.ffill()

    return df

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Process the text format Calamus monograph to get treatments")
    parser.add_argument('input_file', help="Path to the input PDF file")
    parser.add_argument('output_file', help="Path to the output file")
    
    # Parse arguments
    args = parser.parse_args()


    # Open the PDF file for reading
    reader = PdfReader(args.input_file)

    # Extract pages and store with their page number in a dictionary
    pages = dict()
    for i, page in enumerate(reader.pages):
        page_number = page.page_number + 1
        page_text = page.extract_text()
        pages[page_number] = page_text

    # Make a dataframe from the pages dictionary
    df_pages = pd.DataFrame(data={'page_number':pages.keys(),'page_text':pages.values()})

    # Make a new column which holds the individual lines in each page
    # First as a list of lines
    df_pages['line'] = df_pages['page_text'].apply(lambda x: x.split('\n'))
    # Now "explode" the list of lines so that each line is in its own row
    # in the dataframe
    df_lines = df_pages.explode('line')
    # page text can be dropped as no longer needed
    df_lines.drop(columns=['page_text'],inplace=True)
    # Clean any boilerplate footer text from the lines
    df_lines['line_cleaned'] = df_lines.apply(lambda row: cleanLine(row['line'], row['page_number']), axis=1)

    df_lines = identifySections(df_lines)

    df_lines = identifyTreatments(df_lines)

    # Group to show how many lines were allocated to each taxonomic treatment
    pd.set_option('display.max_rows',500)
    print(df_lines.groupby(df_lines.taxon_id_and_name).size())

    for species_name in species_names:
        mask = (df_lines.taxon_id_and_name.str.contains(species_name,na=False))
        print(df_lines[mask][['line_cleaned']])
     
    df_lines = identifyTreatmentSubsections(df_lines)
 
    # Iterate over each species name in species_names
    # For each species, create a mask to select rows where the taxon_id_and_name column contains the species name, and the treatment_subsection column = 'description'
    for species_name in species_names:
        mask = (df_lines.taxon_id_and_name.str.contains(species_name, na=False) & (df_lines.treatment_subsection == 'description'))
        print(df_lines[mask][['line_cleaned']])

    mask = (df_lines.taxon_name.isin(species_names) 
            & (df_lines.treatment_subsection == 'description')
            & (df_lines.line_cleaned.str.endswith('Magnolia Press') == False)
            )
    df_treatments = df_lines[mask].groupby('taxon_name')['line_cleaned'].agg(' '.join).reset_index()

    # Display the result
    print(df_treatments)

    df_treatments.to_csv(args.output_file, index=False)

if __name__ == "__main__":
    main()      