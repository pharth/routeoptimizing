from flask import Flask, request, jsonify
import pandas as pd
import networkx as nx
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
import pickle
import joblib

app = Flask(__name__)

# Load data
data = pd.read_csv('data_sorted.csv')
le = LabelEncoder()
data['traffic_jam_level'] = le.fit_transform(data['traffic_jam_level'])
data.dropna(inplace=True)

# Define features for ML model
features = [
    'distance_to_next_stop_km',
    'traffic_speed',
    'free_flow_speed',
    'traffic_jam_level',
    'traffic_confidence',
    'time_delay_minutes'
]

# Load the trained ML model 
model = joblib.load('random_forest_model.sav')


# Create graph
G = nx.DiGraph()

# Function to predict travel time using the trained ML model
# def predict_travel_time(row):
#     features_data = [[
#         row['distance_to_next_stop_km'],
#         row['traffic_speed'],
#         row['free_flow_speed'],
#         row['traffic_jam_level'],
#         row['traffic_confidence'],
#         row['time_delay_minutes']
#     ]]
#     return model.predict(features_data)[0]



def predict_travel_time(row):
    features_data = pd.DataFrame([[
        row['distance_to_next_stop_km'],
        row['traffic_speed'],
        row['free_flow_speed'],
        row['traffic_jam_level'],
        row['traffic_confidence'],
        row['time_delay_minutes']
    ]], columns=features)  # Specify column names matching training data
    return model.predict(features_data)[0]

# Add edges to the graph based on predicted travel times
def build_graph():
    data_sorted = data.sort_values(by=['trip_id', 'stop_sequence'])
    for i in range(1, len(data_sorted)):
        prev_row = data_sorted.iloc[i - 1]
        current_row = data_sorted.iloc[i]
        
        if current_row['trip_id'] == prev_row['trip_id']:
            source = prev_row['stop_id']
            destination = current_row['stop_id']
            travel_time = predict_travel_time(current_row)
            G.add_edge(source, destination, weight=travel_time)

# Build the graph
build_graph()

# Flask route to find the optimized path
@app.route('/optimized_route', methods=['GET'])
def get_optimized_route():
    # Get source and destination from query parameters
    source_stop = request.args.get('source')
    destination_stop = request.args.get('destination')
    
    # Check if the source and destination are provided
    if not source_stop or not destination_stop:
        return jsonify({'error': 'Please provide both source and destination stop IDs'}), 400

    try:
        # Find the shortest path using Dijkstra's algorithm
        optimal_route = nx.dijkstra_path(G, source=source_stop, target=destination_stop, weight='weight')
        return jsonify({
            'source': source_stop,
            'destination': destination_stop,
            'optimal_route': optimal_route
        }), 200
    except nx.NetworkXNoPath:
        return jsonify({'error': 'No path found between the provided stops'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Start the Flask app
if __name__ == '__main__':
    app.run(debug=True)
