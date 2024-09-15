import pandas as pd
import requests
from datetime import datetime

# Your TomTom API key (replace 'YOUR_API_KEY' with your actual key)
API_KEY = '3RYXhqecMzcXKzUnrI3N7dgUWGIruEoc'

# File paths for the two CSV files
stop_details_file = 'stops.csv'  # The CSV with stop_code, stop_lat, stop_lon, stop_name, etc.
trip_data_file = 'dtc_bus.csv'  # The CSV with trip_id, arrival_time, departure_time, stop_id, stop_sequence

# Read the CSV files into pandas DataFrames
stop_details_df = pd.read_csv(stop_details_file)
trip_data_df = pd.read_csv(trip_data_file)

# Merge the stop details and trip data on 'stop_id'
merged_df = pd.merge(trip_data_df, stop_details_df, on='stop_id', how='left')

# TomTom API endpoint for Traffic Flow
TOMTOM_TRAFFIC_API_URL = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"

# Function to query TomTom API for traffic data
def get_traffic_info(lat, lon, time):
    # TomTom API parameters
    params = {
        'point': f'{lat},{lon}',
        'key': API_KEY
    }

    # Send a GET request to TomTom Traffic API
    response = requests.get(TOMTOM_TRAFFIC_API_URL, params=params)
    if response.status_code == 200:
        data = response.json()
        return {
            "traffic_speed": data['flowSegmentData']['currentSpeed'],
            "free_flow_speed": data['flowSegmentData']['freeFlowSpeed'],
            "traffic_confidence": data['flowSegmentData']['confidence'],
            "traffic_jam_level": data['flowSegmentData']['frc']
        }
    else:
        return {
            "traffic_speed": None,
            "free_flow_speed": None,
            "traffic_confidence": None,
            "traffic_jam_level": None
        }

# Helper function to calculate time delta in minutes
def calculate_time_delta(arrival, departure):
    try:
        arrival_time = datetime.strptime(arrival, '%H:%M:%S')
        departure_time = datetime.strptime(departure, '%H:%M:%S')
        time_delta = (departure_time - arrival_time).total_seconds() / 60.0  # Convert to minutes
        return round(time_delta, 2)
    except Exception as e:
        print(f"Error in time parsing: {e}")
        return None

# Create lists to store the traffic data and delays
traffic_speeds = []
free_flow_speeds = []
traffic_confidences = []
traffic_jam_levels = []
time_delays = []
print('...')
# Loop through the merged DataFrame and query traffic data for each stop and arrival time
for index, row in merged_df.iterrows():
    lat = row['stop_lat']
    lon = row['stop_lon']
    arrival_time = row['arrival_time']  # In HH:MM:SS format
    departure_time = row['departure_time']  # In HH:MM:SS format
    
    # Fetch traffic information using the lat, lon, and arrival time
    traffic_info = get_traffic_info(lat, lon, arrival_time)
    
    # Append traffic info to the lists
    traffic_speeds.append(traffic_info['traffic_speed'])
    free_flow_speeds.append(traffic_info['free_flow_speed'])
    traffic_confidences.append(traffic_info['traffic_confidence'])
    traffic_jam_levels.append(traffic_info['traffic_jam_level'])

    # Calculate time delay (delta) between arrival and departure
    time_delay = calculate_time_delta(arrival_time, departure_time)
    time_delays.append(time_delay)
    print(index)

# Add the traffic data and time delay to the merged DataFrame
merged_df['traffic_speed'] = traffic_speeds
merged_df['free_flow_speed'] = free_flow_speeds
merged_df['traffic_confidence'] = traffic_confidences
merged_df['traffic_jam_level'] = traffic_jam_levels
merged_df['time_delay_minutes'] = time_delays

# Save the new merged DataFrame with traffic information and time delays to a new CSV file
output_file = 'merged_trip_stop_traffic_time_delay_data.csv'
merged_df.to_csv(output_file, index=False)

print(f"Merged data with traffic info and time delays saved to {output_file}")
