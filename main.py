import geopandas as gpd
import pandas as pd
import folium
import glob
import os

# Assuming 'Import' directory is in the same directory as your script
import_dir = 'Import'
file_list = os.listdir(import_dir)

# Assuming you want to process the first CSV file found
csv_file = next((f for f in file_list if f.endswith('.csv')), None)
if csv_file:
    test_df = pd.read_csv(os.path.join(import_dir, csv_file))
else:
    print("No CSV files found in the Import directory.")

# Load the reference FIPS codes and trim spaces from column names
fips_df = pd.read_csv('data/FIPS_state_county.csv')
fips_df.columns = fips_df.columns.str.strip()

# Split the FIPS DataFrame into states and counties
states_df = fips_df[fips_df['Place Type'] == 'State']
counties_df = fips_df[fips_df['Place Type'] == 'County']

# Load the test data and trim spaces from column names
test_df.columns = test_df.columns.str.strip()

# Merge to get the state FIPS codes
test_df = test_df.merge(states_df[['FIPS Code', 'Place Name']], how='left', left_on='State', right_on='Place Name')

# Rename columns for clarity
test_df.rename(columns={'FIPS Code': 'State FIPS'}, inplace=True)
test_df.drop(['Place Name'], axis=1, inplace=True)

# Function to find county FIPS based on state FIPS and county name
def find_county_fips(row):
    state_fips_str = str(row['State FIPS'])
    # Filter counties_df for counties in the same state
    state_counties = counties_df[counties_df['FIPS Code'].astype(str).str.startswith(state_fips_str)]
    
    # Append " County" to the county name from test_df for matching, ensuring proper capitalization
    county_name = (row['County'] + " County")
    county_row = state_counties[state_counties['Place Name'] == county_name]
    
    if not county_row.empty:
        # Ensure FIPS Code is returned as a string without trailing '.0'
        return str(county_row.iloc[0]['FIPS Code']).split('.')[0]  # Split and take the first part to remove '.0'
    else:
        # Debugging: Print when a match is not found
        print(f"No match found for {county_name} in state FIPS {state_fips_str}")
    return None

# Apply the function to each row in test_df to get the 'County FIPS' code
test_df['CountyFIPS'] = test_df.apply(find_county_fips, axis=1)

# Ensure 'County FIPS' codes are strings without trailing '.0'
test_df['CountyFIPS'] = test_df['CountyFIPS'].astype(str).str.split('.').str[0]

# Drop the now unnecessary 'State FIPS' column
final_df = test_df.drop(['State FIPS'], axis=1)

# Save the result to a new CSV file
final_df.to_csv('test_with_fips.csv', index=False)

def create_folium_map(shapefile_directory, output_file):
    shapefile_paths = glob.glob(f"{shapefile_directory}/**/*.shp", recursive=True)
    gdfs = [gpd.read_file(shp) for shp in shapefile_paths]
    gdf = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True))
    gdf['FIPS'] = gdf['STATEFP'].str.zfill(2) + gdf['COUNTYFP'].str.zfill(3)

    gdf_illinois = gdf[gdf['STATEFP'] == '17']

    township_df = pd.read_csv('test_with_fips.csv')
    township_df['CountyFIPS'] = township_df['CountyFIPS'].apply(lambda x: '{:.0f}'.format(x).zfill(5))
    township_df['Township'] = township_df['Township'].astype(str)

    # Perform an inner join to keep only townships present in your CSV
    merged_gdf = gdf_illinois.merge(township_df[['CountyFIPS', 'Township', 'Label']], left_on=['FIPS', 'NAME'], right_on=['CountyFIPS', 'Township'], how='inner')

    if not merged_gdf.empty:
        first_township = merged_gdf.iloc[0]
        centroid = first_township.geometry.centroid
        m = folium.Map(location=[centroid.y, centroid.x], zoom_start=10)
        
        folium.GeoJson(
            merged_gdf,
            style_function=lambda feature: {
                'fillColor': '#FF0000' if feature['properties']['Label'] == 'Current Clients' else '#929292' if feature['properties']['Label'] == 'In the Pipeline' else '#000000',
                'color': 'black',
                'fillOpacity': 0.75
            },
            tooltip=folium.GeoJsonTooltip(
                fields=['NAME', 'FIPS', 'Label'],
                aliases=['Township Name:', 'FIPS Code:', 'Label:'],
                localize=True
            )
        ).add_to(m)

        m.save(output_file)
        print(f"Map with highlighted townships saved to {output_file}")
    else:
        print("No matching townships found or they contain no data.")

pass

if __name__ == "__main__":
    shapefile_directory = 'data/COUSUB'
    output_file = 'output_map.html'
    create_folium_map(shapefile_directory, output_file)