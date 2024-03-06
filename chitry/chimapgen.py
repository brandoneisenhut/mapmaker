import folium
import geopandas as gpd

def map_chicago_wards(shapefile_path):
    """
    Creates an interactive map of Chicago wards using a shapefile.

    Parameters:
    - shapefile_path: Path to the shapefile containing the ward boundaries and identifiers.
    """
    # Load the shapefile using Geopandas
    geo_df = gpd.read_file(shapefile_path)

    # Create a map centered around Chicago
    chicago_map = folium.Map(location=[41.8781, -87.6298], zoom_start=11)

    # Add the ward boundaries to the map
    folium.GeoJson(
        geo_df,
        style_function=lambda feature: {
            'color': 'blue',  # Boundary color
            'weight': 2,      # Boundary width
            'fillColor': 'grey',  # Fill color
            'fillOpacity': 0.5    # Fill opacity
        },
        tooltip=folium.GeoJsonTooltip(
            fields=['ward'],
            aliases=['Ward:'],
            localize=True
        )
    ).add_to(chicago_map)

    # Save the map to an HTML file
    chicago_map.save('chicago_wards_map.html')
    print("Map saved as chicago_wards_map.html")

if __name__ == '__main__':
    # Path to your shapefile
    shapefile_path = 'data/Chicago/Wards Boundaries 2015-202/geo_export_92477838-e7f7-48da-9f27-543dbb2ec8cc.shp'

    # Generate the map
    map_chicago_wards(shapefile_path)