import geopandas as gpd
import pandas as pd
import folium
from folium import FeatureGroup
import logging
import psycopg2
from config import DATABASE_CONFIG
from sqlalchemy import create_engine

def generate_connection_url():
    """Generates a PostgreSQL connection URL from the database configuration."""
    user = DATABASE_CONFIG['user']
    password = DATABASE_CONFIG['password']
    host = DATABASE_CONFIG['host']
    port = DATABASE_CONFIG['port']
    database = DATABASE_CONFIG['database']
    connection_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    return connection_url

def fetch_data_from_database():
    """Fetches township data from the database using SQLAlchemy."""
    try:
        # Construct the database URI
        database_uri = generate_connection_url()
        # Create an SQLAlchemy engine
        engine = create_engine(database_uri)
        query = "SELECT id, township_name, label FROM townships;"
        township_df = pd.read_sql_query(query, engine)
        return township_df
    except Exception as error:
        logging.error(f"Error fetching data from database: {error}")
        return pd.DataFrame()  # Return an empty DataFrame on error


def create_folium_map_from_db(output_html='static/output_map.html'):
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

    # Directly load the specific shapefile for Illinois
    shapefile_path = 'data/COUSUB/tl_2023_17_cousub.shp'
    gdf = gpd.read_file(shapefile_path)

    # Fetch data from the database
    township_df = fetch_data_from_database()
    if township_df.empty:
        logging.warning("No data fetched from the database or an error occurred.")
        return

    # Ensure the column used for matching is correctly formatted
    township_df['id'] = township_df['id'].astype(str).apply(lambda x: x.zfill(5))
    # Merge the GeoDataFrame with the database data using cousubfp
    merged_gdf = gdf.merge(township_df, left_on='COUSUBFP', right_on='id', how='inner')

    if not merged_gdf.empty:
        logging.debug("Merged GeoDataFrame is not empty. Proceeding with map generation.")
        initial_zoom_level = 7
        initial_location = [40.0, -89.0]  # Latitude, Longitude for Illinois
        m = folium.Map(location=initial_location, zoom_start=initial_zoom_level)

        # Define the geographical bounds of Illinois
        illinois_bounds = [[36.970298, -91.513079], [42.508338, -87.019935]]

        # Apply the bounds to the map
        m.fit_bounds(illinois_bounds)
        m.options['minZoom'] = 7
        m.options['maxBounds'] = illinois_bounds
        m.options['maxBoundsViscosity'] = 1.0

        feature_group = FeatureGroup(name='Illinois').add_to(m)
        
        folium.GeoJson(
            merged_gdf,
            style_function=lambda feature: {
                'fillColor': '#FF0000' if feature['properties']['label'] == 'Current Clients' else '#929292' if feature['properties']['label'] == 'In the Pipeline' else '#000000',
                'color': 'black',
                'fillOpacity': 0.75,
                'weight': 1
            },
            tooltip=folium.GeoJsonTooltip(
                fields=['township_name', 'id', 'label'],
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
    output_html = 'static/output_map.html'  # Update this path to where you want to save the output HTML
    create_folium_map_from_db(output_html=output_html)