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
from database import db
from auth import generate_token, token_required, get_current_user
from location_services import get_nearby_recommendations

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
@token_required
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
@token_required
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


@app.route('/api/register', methods=['POST'])
def register_user():
    """
    Create a new user in the database
    
    Expected JSON payload:
    {
        "username": str,
        "name": str,
        "email": str,
        "password": str
    }
    
    Returns:
        JSON response with creation result
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        required_fields = ['username', 'name', 'email', 'password']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        success = db.create_user(
            username=data['username'],
            name=data['name'],
            email=data['email'],
            password=data['password']
        )
        
        if success:
            return jsonify({'message': 'User created successfully'}), 201
        else:
            return jsonify({'error': 'Failed to create user'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/api/users', methods=['GET'])
@token_required
def get_users():
    """
    Retrieve all users from database
    
    Returns:
        JSON response with list of users
    """
    try:
        users = db.get_all_users()
        return jsonify({
            'users': users,
            'count': len(users)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Error retrieving users: {str(e)}'}), 500


@app.route('/api/users/<username>', methods=['GET'])
@token_required
def get_user(username):
    """
    Get user by username
    
    Returns:
        JSON response with user data
    """
    try:
        user = db.get_user_by_username(username)
        
        if user:
            # Remove password from response
            user.pop('password', None)
            return jsonify({'user': user}), 200
        else:
            return jsonify({'error': 'User not found'}), 404
            
    except Exception as e:
        return jsonify({'error': f'Error retrieving user: {str(e)}'}), 500


@app.route('/api/recommendations', methods=['POST'])
@token_required
def get_recommendations():
    """
    Get nearby restaurants and activities based on GPS coordinates and budget
    
    Expected JSON payload:
    {
        "latitude": float,
        "longitude": float,
        "budget": str ("low", "medium", "high"),
        "radius": int (optional, default 5000 meters)
    }
    
    Returns:
        JSON response with restaurants and activities
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        # Validate required fields
        required_fields = ['latitude', 'longitude', 'budget']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate coordinates
        try:
            latitude = float(data['latitude'])
            longitude = float(data['longitude'])
        except ValueError:
            return jsonify({'error': 'Invalid latitude or longitude format'}), 400
        
        # Validate coordinate ranges
        if not (-90 <= latitude <= 90):
            return jsonify({'error': 'Latitude must be between -90 and 90'}), 400
        if not (-180 <= longitude <= 180):
            return jsonify({'error': 'Longitude must be between -180 and 180'}), 400
        
        # Validate budget
        budget = data['budget'].lower()
        if budget not in ['low', 'medium', 'high']:
            return jsonify({'error': 'Budget must be "low", "medium", or "high"'}), 400
        
        # Get radius (optional, default 5000m)
        radius = data.get('radius', 5000)
        try:
            radius = int(radius)
            if radius <= 0 or radius > 50000:  # Max 50km
                return jsonify({'error': 'Radius must be between 1 and 50000 meters'}), 400
        except ValueError:
            return jsonify({'error': 'Invalid radius format'}), 400
        
        # Get current user info
        current_user = get_current_user()
        
        # Get recommendations
        recommendations = get_nearby_recommendations(latitude, longitude, budget, radius)
        
        # Add user context and timestamp
        response_data = {
            'message': 'Recommendations retrieved successfully',
            'user': current_user['username'],
            'timestamp': datetime.now().isoformat(),
            'recommendations': recommendations
        }
        
        # Store the request for analytics (optional)
        analytics_data = {
            'user_id': current_user['user_id'],
            'username': current_user['username'],
            'request_type': 'recommendations',
            'location': {'latitude': latitude, 'longitude': longitude},
            'budget': budget,
            'radius': radius,
            'results_count': recommendations['total_results'],
            'timestamp': datetime.now().isoformat()
        }
        stored_data.append(analytics_data)
        save_to_file(analytics_data)
        
        return jsonify(response_data), 200
        
    except Exception as e:
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500


@app.route('/api/login', methods=['POST'])
def login():
    """
    User login endpoint
    
    Expected JSON payload:
    {
        "username": str,
        "password": str
    }
    
    Returns:
        JSON response with login result
    """
    try:
        data = request.get_json()
        
        if not data or 'username' not in data or 'password' not in data:
            return jsonify({'error': 'Username and password required'}), 400
        
        if db.verify_password(data['username'], data['password']):
            user = db.get_user_by_username(data['username'])
            user.pop('password', None)  # Remove password from response
            
            # Generate JWT token
            token = generate_token(user)
            
            return jsonify({
                'message': 'Login successful',
                'user': user,
                'token': token
            }), 200
        else:
            return jsonify({'error': 'Invalid username or password'}), 401
            
    except Exception as e:
        return jsonify({'error': f'Login error: {str(e)}'}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint to verify server is running
    
    Returns:
        JSON response with server status
    """
    db_status = 'connected' if db.connection and db.connection.is_connected() else 'disconnected'
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'stored_records': len(stored_data),
        'database_status': db_status
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
    
    # Initialize database connection and create tables
    print("Initializing database...")
    if db.initialize_database():
        print("Database initialized successfully")
    else:
        print("Warning: Database initialization failed. Check your .env configuration.")
    
    # Run the Flask development server
    print("Starting Flask server...")
    print("Available endpoints:")
    print("  POST /api/process-gps     - Process GPS data and call external API [AUTH REQUIRED]")
    print("  GET  /api/data           - Retrieve stored data [AUTH REQUIRED]")
    print("  POST /api/recommendations - Get nearby restaurants & activities [AUTH REQUIRED]")
    print("  POST /api/test-connection - Test frontend/backend connection")
    print("  POST /api/register       - Create new user account [PUBLIC]")
    print("  POST /api/login          - User login [PUBLIC]")
    print("  GET  /api/users          - Get all users [AUTH REQUIRED]")
    print("  GET  /api/users/<username> - Get user by username [AUTH REQUIRED]")
    print("  GET  /api/health         - Health check")
    
    app.run(debug=True, host='0.0.0.0', port=5001)