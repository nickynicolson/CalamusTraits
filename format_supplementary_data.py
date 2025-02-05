import pandas as pd
import numpy as np
import argparse

def main():

    # Set up argument parser
    parser = argparse.ArgumentParser(description="Formats the supplementary data")
    parser.add_argument('input_file', help="Path to the input excel file")
    parser.add_argument('output_file', help="Path to the output CSV file")
    
    # Parse arguments
    args = parser.parse_args()

    # Read in the supplementary data matrix and adjust as needed
    supp_data = (
        pd.read_excel(args.input_file)
        .drop(
            [
                'Subspecies', 'Preliminary', 'Collector', 'Colnumber', 'Herbarium', 
                'Group', 'Country', 'Area', 'Status', 'Latitude', 'Dlatitude', 
                'Longitude', 'Dlongitude', 'Elevation'
            ], 
            axis=1
        )
        .rename(columns={'Species': 'taxon_name'})
        .replace(
            {
                "C. concolor": "Calamus concolor",
                "C. disjunctus": "Calamus disjunctus",
                "C. glaucescens": "Calamus glaucescens",
                "C. hallierianus": "Calamus hallierianus",
                "C. pseudoconcolor": "Calamus pseudoconcolor",
                "C. subangulatus": "Calamus subangulatus",
            }
        )
    )

    # All column headings should be lowercase
    supp_data.columns = supp_data.columns.str.lower()

    # Split supp_data into quan and qual data
    mean_vals = supp_data.iloc[:, 0:15].groupby('taxon_name').mean().round(1).round({'Numpin':0}).replace(to_replace = np.nan, value = '')
    min_vals = supp_data.iloc[:, 0:15].groupby('taxon_name').min().round(1).round({'Numpin':0}).replace(to_replace = np.nan, value = '')
    max_vals = supp_data.iloc[:, 0:15].groupby('taxon_name').max().round(1).round({'Numpin':0}).replace(to_replace = np.nan, value = '')

    # Define a function to remove cases where there are no ranges and format ranges as 'mean(min-max)'
    def format_quantitative_values(mean, min_val, max_val):
        if mean == min_val == max_val:
            return str(mean)
        return f"{mean}({min_val}-{max_val})"

    # Apply the function element-wise to the DataFrame
    quantitative_data = pd.DataFrame(np.vectorize(format_quantitative_values)(mean_vals, min_vals, max_vals), 
                                index=mean_vals.index, columns=mean_vals.columns)

    # Select the qualitative traits and format when there are multiple numbers per code
    qualitative_data_numbers = (
        supp_data
        .iloc[:, [0] + list(range(15, 172))]
        .replace(to_replace = np.nan, value='')
        .groupby('taxon_name')
        .agg(lambda x: list(set(filter(lambda v: v != '', x))))
        .map(lambda x: ', '.join(map(str, x)))
    )

    # Separate fruit colour as it is not assigned a numerical variable
    fruitcolour = (
        supp_data.iloc[:, [0, 172]]
        .replace(to_replace = np.nan, value='')
        .groupby('taxon_name')
        .agg(lambda x: list(set(filter(lambda v: v != '', x))))
        .map(lambda x: ', '.join(map(str, x)))
    )

    # Merge the numerically assigned traits with fruit colour
    qualitative_data = pd.merge(qualitative_data_numbers, fruitcolour, on='taxon_name')

    # Merge quantitative traits with qualitative traits
    formatted_supp_data = pd.merge(quantitative_data, qualitative_data, on='taxon_name')

    # Output as a csv
    formatted_supp_data.to_csv(args.output_file)

if __name__ == "__main__":
    main()