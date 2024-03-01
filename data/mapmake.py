import geopandas as gpd
import pandas as pd
import folium
import glob
import os

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