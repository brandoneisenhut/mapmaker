import geopandas as gpd

def extract_and_list_wards(shapefile_path):
    """
    Reads a shapefile, lists all unique wards, column names, and displays a sample of the data.

    Parameters:
    - shapefile_path: The file path to the shapefile.
    """
    # Load the shapefile
    gdf = gpd.read_file(shapefile_path)

    # Print column names
    print("Column names:")
    print(gdf.crs)

    # Assuming the column that identifies wards is named 'ward'. Adjust if necessary.
    ward_column_name = 'ward'

    if ward_column_name in gdf.columns:
        # Extract unique wards
        unique_wards = gdf[ward_column_name].unique()
        
        # Print the list of unique wards
        print("\nList of unique wards:")
        for ward in unique_wards:
            print(ward)
    else:
        print(f"\nThe column '{ward_column_name}' does not exist in the shapefile.")

    # Display a sample of the data (first 5 rows)
    print("\nSample data (first 5 rows):")
    print(gdf.head())
    print("Column names:")
    print(gdf.columns.tolist())

if __name__ == '__main__':
    # Path to your shapefile
    shapefile_path = 'data/Chicago/Wards Boundaries 2015-202/geo_export_92477838-e7f7-48da-9f27-543dbb2ec8cc.shp'
    
    # Call the function
    extract_and_list_wards(shapefile_path)