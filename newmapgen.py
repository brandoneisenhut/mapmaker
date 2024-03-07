import geopandas as gpd
import pandas as pd
from sqlalchemy.orm import sessionmaker
import folium
from folium import FeatureGroup
import logging
from sqlalchemy import create_engine, text
from config import DATABASE_CONFIG
from flask import Flask, request, jsonify, render_template_string


def generate_connection_url():
    """Generates a PostgreSQL connection URL from the database configuration."""
    user = DATABASE_CONFIG['user']
    password = DATABASE_CONFIG['password']
    host = DATABASE_CONFIG['host']
    port = DATABASE_CONFIG['port']
    database = DATABASE_CONFIG['database']
    connection_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    return connection_url

app = Flask(__name__)

def save_map_to_database(name, html_content):
    """Saves the HTML content of a map to the database using SQLAlchemy, 
    ensuring only the latest map is stored."""
    connection_url = generate_connection_url()
    engine = create_engine(connection_url)
    with engine.connect() as conn:
        # Start a transaction
        trans = conn.begin()
        try:
            # Delete all existing records
            conn.execute(text("DELETE FROM html_maps;"))
            
            # Insert the new map
            result = conn.execute(text("INSERT INTO html_maps (name, html_content) VALUES (:name, :html_content) RETURNING id;"), {'name': name, 'html_content': html_content})
            map_id = result.fetchone()[0]
            
            # Commit the transaction
            trans.commit()
            print(f"Map with ID {map_id} saved successfully.")  # Debug statement
            return map_id
        except Exception as e:
            # Rollback the transaction in case of error
            trans.rollback()
            print(f"An error occurred while saving the map: {e}")
            return None

def fetch_data_from_database():
    """Fetches township data from the database using SQLAlchemy."""
    try:
        database_uri = generate_connection_url()
        engine = create_engine(database_uri)
        Session = sessionmaker(bind=engine)
        session = Session()

        query = text("SELECT id, township_name, label, county_name FROM townships;")
        result = session.execute(query)
        township_df = pd.DataFrame(result.fetchall(), columns=['id', 'township_name', 'label','county_name'])

        session.close()
        return township_df
    except Exception as error:
        logging.error(f"Error fetching data from database: {error}")
        return pd.DataFrame()  # Return an empty DataFrame on error

def create_folium_map_from_db():
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

    # Directly load the specific shapefile for Illinois
    shapefile_path = 'data/COUSUB/tl_2023_17_cousub.shp'
    gdf = gpd.read_file(shapefile_path)

    # Load the Chicago wards shapefile
    chicago_shapefile_path = 'data/Chicago/Wards Boundaries 2015-202/geo_export_92477838-e7f7-48da-9f27-543dbb2ec8cc.shp'
    chicago_gdf = gpd.read_file(chicago_shapefile_path)

    # Fetch data from the database
    township_df = fetch_data_from_database()
    if township_df.empty:
        logging.warning("No data fetched from the database or an error occurred.")
        return

    # Ensure the column used for matching is correctly formatted
    township_df['id'] = township_df['id'].astype(str).apply(lambda x: x.zfill(5))
    # Format the 'ward' column in the Chicago shapefile to match the 'township_name' format in the database
    chicago_gdf['ward'] = chicago_gdf['ward'].apply(lambda x: f"Ward {x}")
    # Merge the GeoDataFrame with the database data using 'township_name' for Chicago wards
    chicago_gdf = chicago_gdf.merge(township_df, left_on='ward', right_on='township_name', how='left')

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

    # Add Illinois townships to the map
    feature_group_illinois = FeatureGroup(name='Illinois Townships').add_to(m)
    folium.GeoJson(
        gdf.merge(township_df, left_on='COUSUBFP', right_on='id', how='inner'),
        style_function=lambda feature: {
            'fillColor': '#FF0000' if feature['properties']['label'] == 'Current Clients' else '#929292' if feature['properties']['label'] == 'In the Pipeline' else '#000000',
            'color': 'black',
            'fillOpacity': 0.75,
            'weight': 1
        },
        tooltip=folium.GeoJsonTooltip(
            fields=['township_name', 'county_name', 'label'],
            aliases=['Township Name:', 'County:', 'Label:'],
        localize=True
        )
    ).add_to(feature_group_illinois)

    # Add Chicago wards to the map
    feature_group_chicago = FeatureGroup(name='Chicago Wards').add_to(m)
    folium.GeoJson(
        chicago_gdf,
        style_function=lambda feature: {
            'fillColor': '#FF0000' if feature['properties']['label'] == 'Current Clients' else '#929292' if feature['properties']['label'] == 'In the Pipeline' else '#000000',
            'color': 'black',
            'fillOpacity': 0.75,
            'weight': 1
        },
        tooltip=folium.GeoJsonTooltip(
            fields=['ward', 'label'],
            aliases=['Ward:', 'Label:'],
            localize=True
        )
    ).add_to(feature_group_chicago)

    # Optionally, add layer control to toggle between layers
    folium.LayerControl().add_to(m)

    html_string = m._repr_html_()
    custom_html = f"""
    <div style="height: 900px; width: 600px; overflow: hidden;">
        {html_string}
    </div>
    """

    # Now, call save_map_to_database with the map name and HTML content
    map_name = "My Generated Map"  # Choose an appropriate name for your map
    save_map_to_database(map_name, custom_html)
   # logging.info(f"Map with highlighted Illinois townships and Chicago wards saved to {output_html}")

if __name__ == '__main__':
    create_folium_map_from_db()