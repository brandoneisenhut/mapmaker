import geopandas as gpd
import pandas as pd

# Load the shapefile into a GeoDataFrame
gdf = gpd.read_file('data/COUSUB/tl_2023_17_cousub.shp')

# Filter the GeoDataFrame for rows where STATEFP is '17'
gdf_illinois = gdf[gdf['STATEFP'] == '17']

# Select only the 'NAME' and 'NAMELSAD' columns
townships = gdf_illinois[['NAME', 'NAMELSAD']]

# Save the filtered data to a CSV file
townships.to_csv('illinois_townships.csv', index=False)