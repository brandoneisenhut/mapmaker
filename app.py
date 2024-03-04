from flask import Flask, request, send_file, jsonify, render_template, redirect, url_for
import os
from werkzeug.utils import secure_filename
from fips_conversion import process_file as process_with_fips
from fuck import create_folium_map

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

from flask import send_from_directory

@app.route('/map')
def serve_map():
    return send_from_directory('.', 'output_map.html')

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    try:
        if request.method == 'POST':
            # Check if the post request has the file part
            if 'file' not in request.files:
                return 'No file part'
            file = request.files['file']
            if file.filename == '':
                return 'No selected file'
            if file:
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                # Process the file through fips_conversion.py
                processed_csv_path = process_with_fips(filepath)
                
                # Assuming the shapefiles are stored in a directory named 'data/COUSUB'
                shapefile_directory = 'data/COUSUB'
                output_html = 'output_map.html'
                
                # Process the output of fips_conversion.py through fuck.py
                final_output_path = create_folium_map(shapefile_directory, processed_csv_path, output_html)
                
                # Redirect to GET request to display the form and the updated map
                return redirect(url_for('upload_file'))
        
        # Assuming 'output_map.html' is located in 'static/maps/output_map.html'
        map_url = os.path.join(app.static_url_path, 'maps', 'output_map.html')
        return render_template('display_map_with_upload.html', map_url='output_map.html')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
