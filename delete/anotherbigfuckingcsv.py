import pandas as pd

# Load the datasets
state_df = pd.read_csv('state_county_nameslad_cousubfp_place.csv')
surus_df = pd.read_csv('processed_Surus_Illinois_Mapping.csv')

# Normalize the names in state_df
state_df['NormalizedCounty'] = state_df['Place Name'].str.replace(' County', '')
state_df['NormalizedTownship'] = state_df['NAMELSAD'].str.replace(' township', '', case=False)

# Create a matching key in state_df
state_df['MatchKey'] = state_df['NormalizedCounty'] + state_df['NormalizedTownship']

# Normalize the names in surus_df (assuming it's already normalized based on your description)
surus_df['MatchKey'] = surus_df['County'] + surus_df['Township']

# Merge the dataframes on the MatchKey
merged_df = pd.merge(state_df, surus_df[['MatchKey', 'Label']], on='MatchKey', how='left')

# Fill missing labels with 'None'
merged_df['Label'].fillna('None', inplace=True)

# Select and rename columns as needed, dropping the intermediate columns used for matching
final_df = merged_df.drop(columns=['NormalizedCounty', 'NormalizedTownship', 'MatchKey'])

# Save the merged data to a new CSV file
final_df.to_csv('combined_state_surus_mapping.csv', index=False)

# Print out the combined dataframe for verification
print(final_df.head())

# Assuming the merged_df is already created and contains all necessary data

# Select only the required columns
final_columns_df = merged_df[['COUSUBFP', 'NAMELSAD', 'Place Name', 'Label']]

# Save the selected columns to a new CSV file
final_columns_df.to_csv('final_cousubfp_nameslad_place_label.csv', index=False)

# Print out the dataframe for verification
print(final_columns_df.head())