import argparse
import numpy as np
import pandas as pd


def read_supp_data(input_file):
    """Read in the supplementary data matrix and adjust as needed."""
    supp_data = (
        pd.read_excel(input_file)
        .drop(
            [
                'Subspecies', 'Preliminary', 'Collector', 'Colnumber', 'Herbarium',
                'Group', 'Country', 'Area', 'Status', 'Latitude', 'Dlatitude',
                'Longitude', 'Dlongitude', 'Elevation'
            ],
            axis=1
        )
        .rename(columns={'Species': 'taxon_name'})
        .replace(regex={r"^C\. ": "Calamus "})
    )
    return supp_data


def extract_values(df):
    """Function to extract mean, min, and max values from the supplementary data matrix."""
    mean_vals = (
        df
        .groupby('taxon_name')
        .mean()
        .round(1)
        .round({'numpin': 0})
        .replace(to_replace=np.nan, value='')
    )

    min_vals = (
        df
        .groupby('taxon_name')
        .min()
        .round(1)
        .round({'numpin': 0})
        .replace(to_replace=np.nan, value='')
    )

    max_vals = (
        df
        .groupby('taxon_name')
        .max()
        .round(1)
        .round({'numpin': 0})
        .replace(to_replace=np.nan, value='')
    )

    return mean_vals, min_vals, max_vals


def format_quantitative_values(mean, min_val, max_val):
    """Define a function to remove cases where there are no ranges and format ranges as 'mean(min-max)'."""
    if mean == min_val == max_val:
        return str(mean)
    return f"{mean}({min_val}-{max_val})"
    

def main():
    """Reads an input Excel file, processes the supplementary data matrix by removing unnecessary columns, and outputs a CSV file with the formatted data."""
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Formats the supplementary data matrix"
    )
    parser.add_argument(
        'input_file', 
        help="Path to the input Excel file containing the supplementary data matrix"
    )
    parser.add_argument(
        'output_file', 
        help="Path to the output CSV file where the formatted data will be saved"
    )

    # Parse arguments
    args = parser.parse_args()

    # Call the function to read the supplementary data
    supp_data = read_supp_data(args.input_file)

    # Convert all column headings to lowercase for consistency
    supp_data.columns = supp_data.columns.str.lower()

    # Extract the mean, min, and max values
    mean_vals, min_vals, max_vals = extract_values(supp_data.loc[:, 'taxon_name':'fruitdiam'])

    # Apply the function element-wise to the DataFrame
    quantitative_data = pd.DataFrame(
        np.vectorize(format_quantitative_values)(mean_vals, min_vals, max_vals),
        index=mean_vals.index, columns=mean_vals.columns
    )

    # Select the qualitative traits and format when there are multiple numbers per code
    qualitative_data_numbers = (
        supp_data
        .loc[:, ['taxon_name'] + supp_data.loc[:, 'solclu':'embryo'].columns.to_list()]
        .replace(to_replace=np.nan, value='')
        .groupby('taxon_name')
        .agg(lambda x: list(set(filter(lambda v: v != '', x))))
        .map(lambda x: ', '.join(map(str, x)))
    )

    # Separate fruit colour as it is not assigned a numerical variable
    fruit_colour = (
        supp_data
        .loc[:, ['taxon_name', 'frucol']]
        .replace(to_replace=np.nan, value='')
        .groupby('taxon_name')
        .agg(lambda x: list(set(filter(lambda v: v != '', x))))
        .map(lambda x: ', '.join(map(str, x)))
    )

    # Merge the numerically assigned traits (qualitative_data_numbers) with fruit colour (fruit_colour)
    qualitative_data = pd.merge(qualitative_data_numbers, fruit_colour, on='taxon_name')
    # Merge quantitative_data (quantitative traits) with qualitative_data (qualitative traits)
    formatted_supp_data = pd.merge(quantitative_data, qualitative_data, on='taxon_name')

    # Remove .0 from numpin output
    if 'numpin' in formatted_supp_data.columns:
        formatted_supp_data['numpin'] = formatted_supp_data['numpin'].astype(str).str.replace('.0', '', regex=False)

    # Output as a csv
    formatted_supp_data.to_csv(args.output_file)


if __name__ == "__main__":
    main()
