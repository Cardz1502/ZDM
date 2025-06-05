import pandas as pd
import numpy as np

# Load the CSV file
input_file = "printer_data2.csv"  # Replace with your actual CSV file name
df = pd.read_csv(input_file)

# Convert timestamp to datetime
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Sort by filename and timestamp to ensure chronological order
df = df.sort_values(['filename', 'timestamp'])

# Initialize a list to store the data for each group
data_20min = []

# Function to process a group of data and split by 15-minute gaps
def process_group(group):
    # Get the start time of the group
    start_time = group['timestamp'].iloc[0]
    
    # Initialize variables for splitting into subgroups based on 15-minute gaps
    current_start = start_time
    subgroup_data = []
    current_subgroup = []
    
    for index, row in group.iterrows():
        current_time = row['timestamp']
        
        # Check if there's a gap of 15 minutes or more
        if (current_time - current_start).total_seconds() >= 15 * 60:  # 15 minutes in seconds
            # If there's a gap, start a new subgroup
            if current_subgroup:
                subgroup_df = pd.DataFrame(current_subgroup)
                # Select only the first 20 minutes of this subgroup
                cutoff_time = current_start + pd.Timedelta(minutes=20)
                subgroup_df = subgroup_df[subgroup_df['timestamp'] <= cutoff_time]
                subgroup_data.append(subgroup_df)
            # Reset for the new subgroup
            current_subgroup = [row]
            current_start = current_time
        else:
            # Add row to the current subgroup
            current_subgroup.append(row)
            
    # Process the last subgroup if it exists
    if current_subgroup:
        subgroup_df = pd.DataFrame(current_subgroup)
        cutoff_time = current_start + pd.Timedelta(minutes=20)
        subgroup_df = subgroup_df[subgroup_df['timestamp'] <= cutoff_time]
        subgroup_data.append(subgroup_df)
    
    return subgroup_data

# Group by filename and process each group
grouped = df.groupby('filename')
for filename, group in grouped:
    # Process the group to split into subgroups based on 15-minute gaps
    subgroups = process_group(group)
    # Extend the list with all subgroups
    data_20min.extend(subgroups)

# Concatenate all subgroups into a single DataFrame
if data_20min:
    final_df = pd.concat(data_20min, ignore_index=True)
else:
    final_df = pd.DataFrame(columns=df.columns)

# Save to a new CSV file
output_file = "10percent.csv"
final_df.to_csv(output_file, index=False)

print(f"Data for the first 20 minutes of each impression, split by 15-minute gaps, has been saved to {output_file}")