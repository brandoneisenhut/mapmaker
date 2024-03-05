import geopandas as gpd
import pandas as pd
import folium
from folium import FeatureGroup  # Add this import
import glob
import logging
import os

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def create_folium_map(shapefile_directory, processed_csv_path, output_html='static/maps/output_map.html'):
    logging.debug("Starting map generation.")
    shapefile_paths = glob.glob(f"{shapefile_directory}/**/*.shp", recursive=True)
    gdfs = [gpd.read_file(shp) for shp in shapefile_paths]
    gdf = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True))
    gdf['FIPS'] = gdf['STATEFP'].str.zfill(2) + gdf['COUNTYFP'].str.zfill(3)

    gdf_illinois = gdf[gdf['STATEFP'] == '17']

    township_df = pd.read_csv(processed_csv_path)
    township_df['CountyFIPS'] = township_df['CountyFIPS'].apply(lambda x: '{:.0f}'.format(x).zfill(5))
    township_df['Township'] = township_df['Township'].astype(str)

    # Perform an inner join to keep only townships present in your CSV
    merged_gdf = gdf_illinois.merge(township_df[['CountyFIPS', 'Township', 'Label']], left_on=['FIPS', 'NAME'], right_on=['CountyFIPS', 'Township'], how='inner')

    if not merged_gdf.empty:
        logging.debug("Merged GeoDataFrame is not empty. Proceeding with map generation.")
        first_township = merged_gdf.iloc[0]
        initial_zoom_level = 7
        initial_location = [40.0, -89.0]  # Latitude, Longitude
        m = folium.Map(location=initial_location, zoom_start=initial_zoom_level)
        feature_group = FeatureGroup(name='Illinois').add_to(m)
        
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
        ).add_to(feature_group)

        # Automatically adjust the map to fit the bounds of the feature group
        m.fit_bounds(feature_group.get_bounds())

        m.save(output_html)
        logging.info(f"Map with highlighted townships saved to {output_html}")
    else:
        logging.warning("No matching townships found or they contain no data.")
    
    return output_html