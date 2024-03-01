from flask import Flask, request, send_file, render_template
import pandas as pd
import os

app = Flask(__name__)

# Ensure there's a folder for uploads and processed files
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            return 'No file part'
        file = request.files['file']
        if file.filename == '':
            return 'No selected file'
        if file:
            filename = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filename)
            # Process the file (example function call)
            processed_filename = process_file(filename)
            return send_file(processed_filename, as_attachment=True)
    return '''
    <!doctype html>
    <title>Upload CSV</title>
    <h1>Upload CSV file</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''

def process_file(filepath):
    # Load the uploaded CSV file
    test_df = pd.read_csv(filepath)
    
    # Assuming FIPS_state_county.csv is in the 'data' directory
    fips_df = pd.read_csv('data/FIPS_state_county.csv')
    fips_df.columns = fips_df.columns.str.strip()

    # Split the FIPS DataFrame into states and counties
    states_df = fips_df[fips_df['Place Type'] == 'State']
    counties_df = fips_df[fips_df['Place Type'] == 'County']

    # Trim spaces from column names of the uploaded CSV
    test_df.columns = test_df.columns.str.strip()

    # Merge to get the state FIPS codes
    test_df = test_df.merge(states_df[['FIPS Code', 'Place Name']], how='left', left_on='State', right_on='Place Name')

    # Rename columns for clarity and drop unnecessary columns
    test_df.rename(columns={'FIPS Code': 'State FIPS'}, inplace=True)
    test_df.drop(['Place Name'], axis=1, inplace=True)

    # Function to find county FIPS based on state FIPS and county name
    def find_county_fips(row):
        state_fips_str = str(row['State FIPS'])
        state_counties = counties_df[counties_df['FIPS Code'].astype(str).str.startswith(state_fips_str)]
        county_name = (row['County'] + " County")
        county_row = state_counties[state_counties['Place Name'] == county_name]
        if not county_row.empty:
            return str(county_row.iloc[0]['FIPS Code']).split('.')[0]
        else:
            print(f"No match found for {county_name} in state FIPS {state_fips_str}")
        return None

    # Apply the function to each row in test_df to get the 'County FIPS' code
    test_df['CountyFIPS'] = test_df.apply(find_county_fips, axis=1)

    # Ensure 'County FIPS' codes are strings without trailing '.0'
    test_df['CountyFIPS'] = test_df['CountyFIPS'].astype(str).str.split('.').str[0]

    # Drop the now unnecessary 'State FIPS' column
    final_df = test_df.drop(['State FIPS'], axis=1)

    # Save the result to a new CSV file in the PROCESSED_FOLDER
    processed_filepath = os.path.join(PROCESSED_FOLDER, 'processed_' + os.path.basename(filepath))
    final_df.to_csv(processed_filepath, index=False)

    return processed_filepath

if __name__ == '__main__':
    app.run(debug=True)