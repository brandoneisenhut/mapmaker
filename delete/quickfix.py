import pandas as pd

# Load the datasets
df_main = pd.read_csv('data/final_cousubfp_nameslad_place_label.csv', dtype={'COUSUBFP': str})
df_merged = pd.read_csv('delete/final_merged_with_labels.csv', dtype={'COUSUBFP': str, 'Label': str})

# Ensure COUSUBFP values are strings and zero-padded if necessary
df_main['COUSUBFP'] = df_main['COUSUBFP'].apply(lambda x: x.zfill(5))
df_merged['COUSUBFP'] = df_merged['COUSUBFP'].apply(lambda x: x.zfill(5))

# Create a dictionary from df_merged for COUSUBFP to Label mapping
label_dict = pd.Series(df_merged.Label.values, index=df_merged.COUSUBFP).to_dict()

# Define a function to update the label if it's missing in df_main but present in df_merged
def update_label(row):
    if pd.isna(row['Label']) or row['Label'].strip() == '':
        return label_dict.get(row['COUSUBFP'], row['Label'])
    return row['Label']

# Apply the function to update labels in df_main
df_main['Label'] = df_main.apply(update_label, axis=1)

# Save the updated dataframe back to a new file to preserve the original
df_main.to_csv('data/final_cousubfp_nameslad_place_label.csv', index=False)

print("Updated labels have been saved to final_cousubfp_nameslad_place_label_updated.csv")