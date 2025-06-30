import argparse
import numpy as np
import pandas as pd


def parse_args():
    """Function to parse command line arguments."""
    parser = argparse.ArgumentParser(description="Formats the supplementary data matrix")
    parser.add_argument('input_file', help="Path to the input Excel file containing the supplementary data matrix")
    parser.add_argument('output_file_qual_multi', help="Path to the output CSV file for qualitative traits with multiple numbers per code")
    parser.add_argument('output_file', help="Path to the output CSV file where the formatted data will be saved")
    return parser.parse_args()


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
    def get_value(df, func, round_dict=None):
        result = (
            df
            .groupby('taxon_name')
            .agg(func)
            .round(1)
            .replace(to_replace=np.nan, value='')
        )
        if round_dict:
            result = result.round(round_dict)
        return result

    mean_vals = get_value(df, 'mean', {'numpin': 0})
    min_vals = get_value(df, 'min', {'numpin': 0})
    max_vals = get_value(df, 'max', {'numpin': 0})

    return mean_vals, min_vals, max_vals


def format_qualitative_data_numbers(supp_data):
    """Format qualitative data with multiple numbers per code."""
    qualitative_data = (
        supp_data
        .loc[:, ['taxon_name'] + supp_data.loc[:, 'solclu':'embryo'].columns.to_list()]
        .replace(to_replace=np.nan, value='')
        .groupby('taxon_name')
        .agg(lambda x: list(set(filter(lambda v: v != '', x))))
        .map(lambda x: ', '.join(map(str, x)))
    )
    return qualitative_data


def format_quantitative_values(mean, min_val, max_val):
    """Define a function to remove cases where there are no ranges and format ranges as 'mean(min-max)'."""
    if mean == min_val == max_val:
        return str(mean)
    return f"{mean}({min_val}-{max_val})"

def extract_qualitative_multi(supp_data, output_file_qual_multi):
    # Get the list of qualitative trait columns
    qualitative_cols = supp_data.loc[:, 'solclu':'embryo'].columns.to_list()

    # Prepare a list to collect results
    qualitative_results = []

    # Group by taxon_name
    grouped = supp_data.groupby('taxon_name')

    for taxon, group in grouped:
        num_specimens = len(group)
        for code in qualitative_cols:
            # calculate the number of specimens scored for each code
            num_specimens_scored = group[code].notna().sum()
            values = group[code].dropna()
            if values.empty:
                most_common = ''
                freq = 0
                other_values = ''
            else:
                most_common = values.mode().iloc[0]
                freq = (values == most_common).sum()
                # Find other unique values assigned (excluding the most common)
                other_vals = set(values.unique()) - {most_common}
                other_values = ', '.join(map(str, sorted(other_vals))) if other_vals else ''
            qualitative_results.append({
                'taxon_name': taxon,
                'code': code,
                'value': most_common,
                'frequency': freq,
                'num_specimens': num_specimens,
                'num_specimens_scored': num_specimens_scored,
                'other_values': other_values
            })

    qualitative_data_numbers_multi = pd.DataFrame(
        qualitative_results,
        columns=['taxon_name', 'code', 'value', 'frequency', 'num_specimens', 'num_specimens_scored', 'other_values']
    )
    # remove rows where 'other_values' is empty
    qualitative_data_numbers_multi = qualitative_data_numbers_multi[qualitative_data_numbers_multi['other_values'] != '']
    qualitative_data_numbers_multi.to_csv(output_file_qual_multi, index=False)


def format_frucol(supp_data):
    fruit_colour = (
        supp_data
        .loc[:, ['taxon_name', 'frucol']]
        .replace(to_replace=np.nan, value='')
        .groupby('taxon_name')
        .agg(lambda x: list(set(filter(lambda v: v != '', x))))
        .map(lambda x: ', '.join(map(str, x)))
    )
    return fruit_colour


def main():
    # Parse arguments
    args = parse_args()
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
    qualitative_data_numbers = (format_qualitative_data_numbers(supp_data))
    # Oupputput the qualitative data with multiple numbers per code
    extract_qualitative_multi(supp_data, args.output_file_qual_multi)
    # Separate fruit colour as it is not assigned a numerical variable
    fruit_colour = format_frucol(supp_data)
    # Merge the qualitative traits (qualitative_data_numbers) with fruit colour (fruit_colour)
    qualitative_data = pd.merge(qualitative_data_numbers, fruit_colour, on='taxon_name')
    # Merge quantitative_data (quantitative traits) with qualitative_data (qualitative traits)
    formatted_supp_data = pd.merge(quantitative_data, qualitative_data, on='taxon_name')
    # Remove .0 from numpin output
    if 'numpin' in formatted_supp_data.columns:
        formatted_supp_data['numpin'] = formatted_supp_data['numpin'].astype(str).str.replace('.0', '', regex=False)
    formatted_supp_data.to_csv(args.output_file)

if __name__ == "__main__":
    main()

