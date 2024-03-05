import geopandas as gpd
import pandas as pd
import folium
from folium import FeatureGroup
import logging

def create_folium_map_new_csv(processed_csv_path, output_html='static/maps/output_map_new.html'):
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

    # Directly load the specific shapefile for Illinois
    shapefile_path = 'data/COUSUB/tl_2023_17_cousub.shp'
    gdf = gpd.read_file(shapefile_path)

    # Load the new CSV
    township_df = pd.read_csv(processed_csv_path)
    # Ensure the column used for matching is correctly formatted
    # This step assumes your CSV has a matching column for COUSUBFP. Adjust as necessary.
    township_df['COUSUBFP'] = township_df['COUSUBFP'].astype(str).apply(lambda x: x.zfill(5))
    # Merge the GeoDataFrame with the new CSV data using COUSUBFP
    merged_gdf = gdf.merge(township_df, left_on='COUSUBFP', right_on='COUSUBFP', how='inner')

    if not merged_gdf.empty:
        logging.debug("Merged GeoDataFrame is not empty. Proceeding with map generation.")
        initial_zoom_level = 7
        initial_location = [40.0, -89.0]  # Latitude, Longitude for Illinois
        m = folium.Map(location=initial_location, zoom_start=initial_zoom_level)

        # Define the geographical bounds of Illinois
        illinois_bounds = [[36.970298, -91.513079], [42.508338, -87.019935]]  # These are approximate and may need adjustment

        # Apply the bounds to the map
        m.fit_bounds(illinois_bounds)
        m.options['minZoom'] = 7  # Adjust as needed to prevent zooming out too far
        m.options['maxBounds'] = illinois_bounds
        m.options['maxBoundsViscosity'] = 1.0  # Makes it harder to pan outside the bounds

        feature_group = FeatureGroup(name='Illinois').add_to(m)
        
        folium.GeoJson(
            merged_gdf,
            style_function=lambda feature: {
                'fillColor': '#FF0000' if feature['properties']['Label'] == 'Current Clients' else '#929292' if feature['properties']['Label'] == 'In the Pipeline' else '#000000',
                'color': 'black',
                'fillOpacity': 0.75,
                'weight': 1
            },
            tooltip=folium.GeoJsonTooltip(
                fields=['NAME', 'COUSUBFP', 'Label'],
                aliases=['Township Name:', 'COUSUBFP:', 'Label:'],
                localize=True
            )
        ).add_to(feature_group)

        m.save(output_html)
        logging.info(f"Map with highlighted townships saved to {output_html}")
    else:
        logging.warning("No matching townships found or they contain no data.")

if __name__ == '__main__':
    # Example usage
    processed_csv_path = 'data/final_cousubfp_nameslad_place_label.csv'  # Update this path to your new CSV file
    output_html = 'output_map.html'  # Update this path to where you want to save the output HTML
    create_folium_map_new_csv(processed_csv_path, output_html)