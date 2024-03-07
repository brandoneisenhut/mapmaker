from flask import Flask, request, jsonify, render_template, make_response, redirect, url_for, render_template_string, Response
from flask_sqlalchemy import SQLAlchemy
import subprocess
from datetime import datetime
from sqlalchemy import create_engine, text
import pandas as pd
import os
from config import DATABASE_CONFIG
import logging
from newmapgen import create_folium_map_from_db, generate_connection_url, save_map_to_database


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

@app.route('/', methods=['GET'])
def display_data():
    search_query = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    rows_per_page = 10

    # Fetch data from the database
    df = fetch_data_from_database(search_query=search_query, page=page, rows_per_page=rows_per_page)
    data = df.to_dict('records')

    pipeline_count, client_count, nan_count, unique_counties, unique_townships, unique_labels = calculate_counts_and_last_updated()

    # Get the total number of records matching the search query
    total_data_count = get_total_records_count(search_query=search_query)
    total_pages = (total_data_count + rows_per_page - 1) // rows_per_page

    return render_template('display_map_with_upload.html',  
                           pipeline_count=pipeline_count, 
                           client_count=client_count, 
                           nan_count=nan_count, 
                           unique_counties=unique_counties, 
                           unique_townships=unique_townships, 
                           unique_labels=unique_labels)

@app.route('/get-data', methods=['GET'])
def get_data():
    page = request.args.get('page', 1, type=int)
    rows_per_page = 10  # Define how many rows per page you want
    search_query = request.args.get('search', '')  # Optional: if you have a search feature

    # Fetch paginated data from the database
    paginated_data = fetch_data_from_database(search_query=search_query, page=page, rows_per_page=rows_per_page)
    data = paginated_data.to_dict('records')  # Convert the DataFrame to a list of dictionaries

    return jsonify(data)

@app.route('/save-label', methods=['POST'])
def save_label():
    data = request.json
    cousubfp = data['id']
    new_label = data['label']
    
    # Assuming update_label_in_database() is defined elsewhere in your codebase
    update_label_in_database(cousubfp, new_label)
    
    return jsonify({'message': 'Label updated successfully'})

@app.route('/regenerate-map', methods=['GET'])
def regenerate_map():
    try:
        # Call the function from newmapgen.py that generates the map
        create_folium_map_from_db()
        return jsonify({'message': 'Map regenerated successfully'}), 200
    except Exception as e:
        print(f"Error regenerating map: {e}")
        return jsonify({'message': 'Failed to regenerate the map'}), 500


def calculate_counts_and_last_updated():
    # Count of 'In the Pipeline' labels
    pipeline_count_query = text("SELECT COUNT(*) FROM townships WHERE label = 'In the Pipeline';")
    pipeline_count = db.session.execute(pipeline_count_query).scalar()
    
    # Count of 'Current Clients' labels
    client_count_query = text("SELECT COUNT(*) FROM townships WHERE label = 'Current Clients';")
    client_count = db.session.execute(client_count_query).scalar()
    
    # Count of labels not in ['In the Pipeline', 'Current Clients']
    nan_count_query = text("SELECT COUNT(*) FROM townships WHERE label NOT IN ('In the Pipeline', 'Current Clients');")
    nan_count = db.session.execute(nan_count_query).scalar()
    
    # Count of unique county names
    unique_counties_query = text("SELECT COUNT(DISTINCT county_name) FROM townships;")
    unique_counties = db.session.execute(unique_counties_query).scalar()
    
    # Count of unique township names
    unique_townships_query = text("SELECT COUNT(DISTINCT township_name) FROM townships;")
    unique_townships = db.session.execute(unique_townships_query).scalar()
    
    # Count of unique labels
    unique_labels_query = text("SELECT COUNT(DISTINCT label) FROM townships;")
    unique_labels = db.session.execute(unique_labels_query).scalar()

    return pipeline_count, client_count, nan_count, unique_counties, unique_townships, unique_labels

def update_label_in_database(id, new_label):
    try:
        # Use the primary key 'id' in your WHERE clause to identify the correct row to update
        update_query = text("UPDATE townships SET label = :new_label WHERE id = :id;")
        db.session.execute(update_query, {'new_label': new_label, 'id': id})
        db.session.commit()
        return True
    except Exception as e:
        print(f"Error updating database: {e}")
        db.session.rollback()
        return False
    
def get_total_records_count(search_query=''):
    query = text("SELECT COUNT(*) FROM townships WHERE township_name ILIKE :search_query;")
    result = db.session.execute(query, {'search_query': f'%{search_query}%'})
    total_count = result.scalar()
    return total_count


def fetch_data_from_database(search_query='', page=1, rows_per_page=10):
    offset = (page - 1) * rows_per_page
    search_filter = f"%{search_query}%" if search_query else "%"
    query = text("""
        SELECT * FROM townships
        WHERE township_name ILIKE :search_filter
        ORDER BY id
        LIMIT :rows_per_page OFFSET :offset;
    """)
    result = db.session.execute(query, {
        'search_filter': search_filter,
        'rows_per_page': rows_per_page,
        'offset': offset
    })
    df = pd.DataFrame(result.fetchall())
    df.columns = result.keys()
    return df

def generate_connection_url():
    """Generates a PostgreSQL connection URL from the database configuration."""
    user = DATABASE_CONFIG['user']
    password = DATABASE_CONFIG['password']
    host = DATABASE_CONFIG['host']
    port = DATABASE_CONFIG['port']
    database = DATABASE_CONFIG['database']
    connection_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    return connection_url

@app.route('/output-map')
def output_map():
    return app.send_static_file('output_map.html')

from flask import Response
from sqlalchemy import create_engine, text

@app.route('/map-content/latest')
def latest_map_content():
    connection_url = generate_connection_url()
    engine = create_engine(connection_url)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT html_content FROM html_maps ORDER BY id DESC LIMIT 1"))
        row = result.fetchone()
        if row:
            return Response(row[0], mimetype='text/html')
        else:
            return "Map not found", 404
        
@app.route('/map-content/latest/download')
def latest_map_content_download():
    connection_url = generate_connection_url()
    engine = create_engine(connection_url)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT html_content FROM html_maps ORDER BY id DESC LIMIT 1"))
        row = result.fetchone()
        if row:
            response = make_response(row[0])
            response.headers['Content-Type'] = 'text/html'
            response.headers['Content-Disposition'] = 'attachment; filename=map.html'
            return response
        else:
            return "Map not found", 404


 
if __name__ == '__main__':
    app.run(debug=False)