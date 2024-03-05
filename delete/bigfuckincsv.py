import pandas as pd
import geopandas as gpd

# Load the shapefile
gdf = gpd.read_file('data/COUSUB/tl_2023_17_cousub.shp')

# Concatenate STATEFP and COUNTYFP to form the full FIPS code
gdf['FIPS'] = gdf['STATEFP'] + gdf['COUNTYFP']

# Select the required columns including the newly formed FIPS code
data_df = gdf[['STATEFP', 'COUNTYFP', 'NAMELSAD', 'COUSUBFP', 'FIPS']]

# Load the FIPS state and county CSV
fips_df = pd.read_csv('data/FIPS_state_county.csv')

# Ensure the FIPS Code in fips_df is of type string for matching
fips_df['FIPS Code'] = fips_df['FIPS Code'].astype(str)

# Merge the shapefile data with the FIPS data based on the FIPS code
merged_df = data_df.merge(fips_df, left_on='FIPS', right_on='FIPS Code', how='left')

# Select the desired columns and rename them appropriately
final_df = merged_df[['STATEFP', 'COUNTYFP', 'NAMELSAD', 'COUSUBFP', 'Place Name', 'Place Type']]

# Save the merged data to a new CSV file
final_df.to_csv('state_county_nameslad_cousubfp_place.csv', index=False)