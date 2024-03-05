from flask import Flask, request, send_file, jsonify, render_template, redirect, url_for, send_from_directory
import os
import pandas as pd
from werkzeug.utils import secure_filename
from fips_conversion import process_file as process_with_fips
from newmapgen import create_folium_map_new_csv
import os
from datetime import datetime
import subprocess

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    # Initialize data variable outside of the try block
    data = []
    search_query = request.args.get('search', '')  # Get the search query from request arguments
    page = request.args.get('page', 1, type=int)
    rows_per_page = 20

    if request.method == 'POST':
        # Handle file upload
        if 'file' not in request.files:
            return 'No file part'
        file = request.files['file']
        if file.filename == '':
            return 'No selected file'
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Process the file
            processed_csv_path = process_with_fips(filepath)
            shapefile_directory = 'data/COUSUB'
            output_html = 'output_map.html'
            final_output_path = create_folium_map_new_csv(processed_csv_path, output_html)
            
            # Redirect to refresh the page and show the updated map
            return redirect(url_for('upload_file'))

    # Attempt to load the CSV file for the table data
    try:
        df = pd.read_csv('data/final_cousubfp_nameslad_place_label.csv')
        if search_query:
            # Assuming you want to search across multiple columns, adjust as necessary
            df = df[df.apply(lambda row: row.astype(str).str.contains(search_query, case=False, regex=False).any(), axis=1)]
        data = df.to_dict(orient='records')
        total_rows = len(data)
        total_pages = (total_rows + rows_per_page - 1) // rows_per_page  # Ceiling division
        start = (page - 1) * rows_per_page
        end = start + rows_per_page
        data = data[start:end]  # Slice the data for the current page
        
        # Calculate counts
        pipeline_count = (df['Label'] == 'In the Pipeline').sum()
        client_count = (df['Label'] == 'Current Clients').sum()
        nan_count = df['Label'].isna().sum()  # Correct way to count NaN values
        
        # Get last updated time of the CSV file
        last_updated_timestamp = os.path.getmtime('data/final_cousubfp_nameslad_place_label.csv')
        last_updated = datetime.fromtimestamp(last_updated_timestamp).strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        # Handle the case where the CSV file cannot be loaded
        print(f"Error loading CSV: {e}")

    print(data)  # Add this line before returning render_template in your Flask route
    return render_template('display_map_with_upload.html', map_url='output_map.html', data=data, page=page, total_pages=total_pages, search_query=search_query, pipeline_count=pipeline_count, client_count=client_count, nan_count=nan_count, last_updated=last_updated)

@app.route('/map')
def serve_map():
    return send_from_directory('.', 'output_map.html')

@app.route('/data')
def get_data():
    df = pd.read_csv('data/final_cousubfp_nameslad_place_label.csv')
    data = df.to_dict(orient='records')
    return jsonify(data)

@app.route('/save-label', methods=['POST'])
def save_label():
    data = request.json
    cousubfp = data['cousubfp']  # Use COUSUBFP to identify the row
    new_label = data['label']
    
    # Load your CSV
    df = pd.read_csv('data/final_cousubfp_nameslad_place_label.csv')
    
    # Update the label for the row identified by COUSUBFP
    df.loc[df['COUSUBFP'] == cousubfp, 'Label'] = new_label
    
    # Save the updated CSV
    df.to_csv('data/final_cousubfp_nameslad_place_label.csv', index=False)
    
    return jsonify({'message': 'Label updated successfully'})

@app.route('/regenerate-map')
def regenerate_map():
    csv_file_path = 'data/final_cousubfp_nameslad_place_label.csv'
    # Adjust the command to include the path to the CSV file as an argument
    result = subprocess.run(['python', 'newmapgen.py', csv_file_path], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("Map regenerated successfully.")
    else:
        print("Error regenerating map:", result.stderr)
    
    return redirect(url_for('upload_file'))

if __name__ == '__main__':
    app.run(debug=True)