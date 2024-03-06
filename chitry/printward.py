import geopandas as gpd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from config import DATABASE_CONFIG

def extract_ward_info(shapefile_path):
    # Load the shapefile
    gdf = gpd.read_file(shapefile_path)
    
    # Assuming the ward numbers are stored in a column named 'ward'
    ward_info = [{'id': 14000 + int(ward), 'township_name': 'Ward ' + ward, 'county_name': 'Chicago City', 'label': ''}
                 for ward in gdf['ward'].unique()]
    
    # Print the GeoDataFrame for verification
    print("GeoDataFrame head (first few rows):")
    print(gdf.head())
    
    # Print the extracted ward information
    print("\nExtracted ward information:")
    for info in ward_info:
        print(info)
    
    return ward_info

def generate_connection_url():
    """Generates a PostgreSQL connection URL from the database configuration."""
    user = DATABASE_CONFIG['user']
    password = DATABASE_CONFIG['password']
    host = DATABASE_CONFIG['host']
    port = DATABASE_CONFIG['port']
    database = DATABASE_CONFIG['database']
    connection_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    return connection_url

def insert_ward_info_to_db(ward_info):
    connection_url = generate_connection_url()
    engine = create_engine(connection_url)
    
    insert_query = text("""
    INSERT INTO townships (id, township_name, county_name, label)
    VALUES (:id, :township_name, :county_name, :label)
    ON CONFLICT (id) DO NOTHING;
    """)

    with engine.connect() as connection:
        try:
            connection.execute(insert_query, ward_info)
            print("Ward information inserted successfully.")
        except SQLAlchemyError as e:
            print(f"Error inserting ward information: {e}")

if __name__ == '__main__':
    shapefile_path = 'data/Chicago/Wards Boundaries 2015-202/geo_export_92477838-e7f7-48da-9f27-543dbb2ec8cc.shp'
    ward_info = extract_ward_info(shapefile_path)
    # Optionally, comment out the next line if you don't want to insert into the database yet
    # insert_ward_info_to_db(ward_info)