import pandas as pd
import os

def process_file(input_csv_path):
    # Load the reference FIPS codes and trim spaces from column names
    fips_df = pd.read_csv('data/FIPS_state_county.csv')
    fips_df.columns = fips_df.columns.str.strip()

    # Split the FIPS DataFrame into states and counties
    states_df = fips_df[fips_df['Place Type'] == 'State']
    counties_df = fips_df[fips_df['Place Type'] == 'County']

    # Load the test data and trim spaces from column names
    test_df = pd.read_csv(input_csv_path)
    test_df.columns = test_df.columns.str.strip()

    # Merge to get the state FIPS codes
    test_df = test_df.merge(states_df[['FIPS Code', 'Place Name']], how='left', left_on='State', right_on='Place Name')

    # Rename columns for clarity
    test_df.rename(columns={'FIPS Code': 'State FIPS'}, inplace=True)
    test_df.drop(['Place Name'], axis=1, inplace=True)

    # Apply the function to each row in test_df to get the 'County FIPS' code
    test_df['CountyFIPS'] = test_df.apply(lambda row: find_county_fips(row, counties_df), axis=1)

    # Ensure 'County FIPS' codes are strings without trailing '.0'
    test_df['CountyFIPS'] = test_df['CountyFIPS'].astype(str).str.split('.').str[0]

    # Drop the now unnecessary 'State FIPS' column
    final_df = test_df.drop(['State FIPS'], axis=1)

    # Save the result to a new CSV file
    output_csv_path = 'processed_' + os.path.basename(input_csv_path)
    final_df.to_csv(output_csv_path, index=False)

    return output_csv_path

def find_county_fips(row, counties_df):
    # Check if 'County' is NaN (a float value) and handle it by returning None
    if pd.isna(row['County']):
        return None
    
    # Ensure state_fips_str is an integer string without trailing '.0'
    state_fips_str = str(int(row['State FIPS']))
    
    # Filter counties_df for counties in the same state
    state_counties = counties_df[counties_df['FIPS Code'].astype(str).str.startswith(state_fips_str)]
    
    # Since 'County' is not NaN here, convert it to string and append " County" for matching
    county_name = str(row['County']) + " County"
    county_row = state_counties[state_counties['Place Name'].str.strip() == county_name.strip()]
    
    if not county_row.empty:
        # Ensure FIPS Code is returned as a string without trailing '.0'
        return str(county_row.iloc[0]['FIPS Code']).split('.')[0]  # Split and take the first part to remove '.0'
    else:
        # Debugging: Print when a match is not found
        print(f"No match found for {county_name} in state FIPS {state_fips_str}")
    return None