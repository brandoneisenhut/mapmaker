import geopandas as gpd
import os

# Path to the directory containing all the Illinois shapefiles
shapefile_directory = 'data/COUSUB'

# List to hold all townships and their counties
townships_list = []

# Iterate over each shapefile in the directory
for filename in os.listdir(shapefile_directory):
    if filename.endswith(".shp"):
        # Construct the full file path
        file_path = os.path.join(shapefile_directory, filename)
        # Read the shapefile
        gdf = gpd.read_file(file_path)
        
        # Check if the necessary columns exist
        if 'TOWNSHIP' in gdf.columns and 'COUNTY' in gdf.columns:
            # Iterate through each row in the GeoDataFrame
            for index, row in gdf.iterrows():
                township = row['TOWNSHIP']
                county = row['COUNTY']
                townships_list.append((township, county))

# Remove duplicates if necessary
townships_list = list(set(townships_list))

# Now you have a list of tuples with (Township, County)
# You can print it or save it to a CSV file
for township, county in townships_list:
    print(f"Township: {township}, County: {county}")

# Optionally, save to a CSV file
import pandas as pd

df = pd.DataFrame(townships_list, columns=['Township', 'County'])
df.to_csv('illinois_townships.csv', index=False)