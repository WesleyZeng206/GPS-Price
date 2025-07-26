"""
Flask Backend for GPS Coordinate Processing
Handles GPS data from frontend, calls external APIs, and provides data storage/retrieval
"""

from flask import Flask, request, jsonify
import requests
import json
import os
from datetime import datetime
from typing import Dict, List, Any

# Initialize Flask application
app = Flask(__name__)

# In-memory storage for API responses and data
stored_data: List[Dict[str, Any]] = []

# Configuration
DATA_FILE = 'data.json'
EXTERNAL_API_URL = 'https://jsonplaceholder.typicode.com/posts'  # Placeholder API for simulation


def save_to_file(data: Dict[str, Any]) -> None:
    """
    Save data to JSON file for persistent storage
    
    Args:
        data: Dictionary containing the data to save
    """
    try:
        # Load existing data if file exists
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                existing_data = json.load(f)
        else:
            existing_data = []
        
        # Append new data
        existing_data.append(data)
        
        # Write back to file
        with open(DATA_FILE, 'w') as f:
            json.dump(existing_data, f, indent=2)
    except Exception as e:
        print(f"Error saving to file: {e}")


def call_external_api(gps_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulate calling an external API with GPS data
    In a real application, this would be your actual external API
    
    Args:
        gps_data: Dictionary containing GPS coordinates and other user data
        
    Returns:
        Dictionary containing the API response
    """
    try:
        # Simulate API call with user data
        payload = {
            'title': f"GPS Request from {gps_data.get('latitude', 'unknown')}, {gps_data.get('longitude', 'unknown')}",
            'body': f"Processing GPS data: {json.dumps(gps_data)}",
            'userId': 1
        }
        
        response = requests.post(EXTERNAL_API_URL, json=payload, timeout=10)
        response.raise_for_status()
        
        # Return the API response
        return {
            'status': 'success',
            'external_api_response': response.json(),
            'original_data': gps_data,
            'timestamp': datetime.now().isoformat()
        }
    except requests.RequestException as e:
        # Handle API errors gracefully
        return {
            'status': 'error',
            'error': str(e),
            'original_data': gps_data,
            'timestamp': datetime.now().isoformat()
        }


@app.route('/api/process-gps', methods=['POST'])
def process_gps_data():
    """
    Main endpoint to receive GPS coordinates or other user inputs
    Calls external API and stores the response both in memory and file
    
    Expected JSON payload:
    {
        "latitude": float,
        "longitude": float,
        "additional_data": any
    }
    
    Returns:
        JSON response with processing results
    """
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Validate required GPS coordinates (optional validation)
        if 'latitude' not in data or 'longitude' not in data:
            return jsonify({'error': 'GPS coordinates (latitude, longitude) are required'}), 400
        
        # Call external API with the GPS data
        api_result = call_external_api(data)
        
        # Store in memory
        stored_data.append(api_result)
        
        # Save to file for persistence
        save_to_file(api_result)
        
        return jsonify({
            'message': 'GPS data processed successfully',
            'result': api_result
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/api/data', methods=['GET'])
def get_stored_data():
    """
    GET endpoint to retrieve all stored data
    Returns both in-memory data and optionally data from file
    
    Query parameters:
        - source: 'memory' (default) or 'file' to specify data source
        - limit: number of records to return (optional)
    
    Returns:
        JSON array of stored data records
    """
    try:
        source = request.args.get('source', 'memory')
        limit = request.args.get('limit', type=int)
        
        if source == 'file' and os.path.exists(DATA_FILE):
            # Return data from file
            with open(DATA_FILE, 'r') as f:
                file_data = json.load(f)
            data_to_return = file_data
        else:
            # Return in-memory data (default)
            data_to_return = stored_data
        
        # Apply limit if specified
        if limit:
            data_to_return = data_to_return[-limit:]
        
        return jsonify({
            'data': data_to_return,
            'count': len(data_to_return),
            'source': source
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error retrieving data: {str(e)}'}), 500


@app.route('/api/test-connection', methods=['POST'])
def test_connection():
    """
    Simple test endpoint for frontend/backend connection verification
    Accepts any JSON data and returns it back with additional metadata
    
    Returns:
        JSON response containing the original data plus metadata
    """
    try:
        # Get any data sent from frontend
        data = request.get_json()
        
        # Create response with original data plus metadata
        response = {
            'message': 'Connection successful!',
            'received_data': data,
            'timestamp': datetime.now().isoformat(),
            'method': request.method,
            'content_type': request.content_type
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({'error': f'Test connection failed: {str(e)}'}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint to verify server is running
    
    Returns:
        JSON response with server status
    """
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'stored_records': len(stored_data)
    }), 200


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    # Create data directory if it doesn't exist
    os.makedirs(os.path.dirname(DATA_FILE) if os.path.dirname(DATA_FILE) else '.', exist_ok=True)
    
    # Run the Flask development server
    print("Starting Flask server...")
    print("Available endpoints:")
    print("  POST /api/process-gps    - Process GPS data and call external API")
    print("  GET  /api/data          - Retrieve stored data")
    print("  POST /api/test-connection - Test frontend/backend connection")
    print("  GET  /api/health        - Health check")
    
    app.run(debug=True, host='0.0.0.0', port=5001)