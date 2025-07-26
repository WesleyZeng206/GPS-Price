"""
Location-based services using Yelp and Google Maps APIs
"""

import requests
import os
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

load_dotenv()

YELP_API_KEY = os.getenv('YELP_API_KEY')
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

# Yelp API endpoints
YELP_SEARCH_URL = 'https://api.yelp.com/v3/businesses/search'
YELP_HEADERS = {
    'Authorization': f'Bearer {YELP_API_KEY}',
    'accept': 'application/json'
}

# Google Maps API endpoints
GOOGLE_PLACES_URL = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json'

def filter_by_budget(places: List[Dict], budget: str) -> List[Dict]:
    """
    Filter places based on budget level
    
    Args:
        places: List of place dictionaries
        budget: Budget level ('low', 'medium', 'high')
        
    Returns:
        Filtered list of places
    """
    budget_mapping = {
        'low': [1, 2],      # $ and $$
        'medium': [2, 3],   # $$ and $$$
        'high': [3, 4]      # $$$ and $$$$
    }
    
    allowed_prices = budget_mapping.get(budget.lower(), [1, 2, 3, 4])
    
    filtered_places = []
    for place in places:
        price_level = place.get('price_level', 1)
        if price_level in allowed_prices:
            filtered_places.append(place)
    
    return filtered_places

def search_yelp_restaurants(latitude: float, longitude: float, budget: str, radius: int = 5000) -> List[Dict[str, Any]]:
    """
    Search for restaurants using Yelp API
    
    Args:
        latitude: GPS latitude
        longitude: GPS longitude
        budget: Budget level ('low', 'medium', 'high')
        radius: Search radius in meters (max 40000)
        
    Returns:
        List of restaurant data
    """
    if not YELP_API_KEY:
        return []
    
    # Map budget to Yelp price levels
    price_map = {
        'low': '1,2',
        'medium': '2,3', 
        'high': '3,4'
    }
    price_filter = price_map.get(budget.lower(), '1,2,3,4')
    
    params = {
        'latitude': latitude,
        'longitude': longitude,
        'radius': min(radius, 40000),  # Yelp max radius
        'categories': 'restaurants,food',
        'price': price_filter,
        'limit': 20,
        'sort_by': 'rating'
    }
    
    try:
        response = requests.get(YELP_SEARCH_URL, headers=YELP_HEADERS, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        restaurants = []
        for business in data.get('businesses', []):
            restaurant = {
                'id': business.get('id'),
                'name': business.get('name'),
                'rating': business.get('rating'),
                'price_level': len(business.get('price', '$')),  # Convert $ to 1, $$ to 2, etc.
                'address': business.get('location', {}).get('display_address', []),
                'phone': business.get('phone'),
                'url': business.get('url'),
                'image_url': business.get('image_url'),
                'categories': [cat.get('title') for cat in business.get('categories', [])],
                'distance': business.get('distance'),
                'coordinates': business.get('coordinates', {}),
                'is_closed': business.get('is_closed', False),
                'source': 'yelp'
            }
            restaurants.append(restaurant)
        
        return restaurants
        
    except requests.RequestException as e:
        print(f"Error calling Yelp API: {e}")
        return []

def search_google_places(latitude: float, longitude: float, place_type: str, budget: str, radius: int = 5000) -> List[Dict[str, Any]]:
    """
    Search for places using Google Places API
    
    Args:
        latitude: GPS latitude
        longitude: GPS longitude
        place_type: Type of place to search for
        budget: Budget level ('low', 'medium', 'high')
        radius: Search radius in meters
        
    Returns:
        List of place data
    """
    if not GOOGLE_MAPS_API_KEY:
        return []
    
    params = {
        'location': f'{latitude},{longitude}',
        'radius': radius,
        'type': place_type,
        'key': GOOGLE_MAPS_API_KEY
    }
    
    try:
        response = requests.get(GOOGLE_PLACES_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        places = []
        for place in data.get('results', []):
            place_data = {
                'id': place.get('place_id'),
                'name': place.get('name'),
                'rating': place.get('rating'),
                'price_level': place.get('price_level', 1),
                'address': place.get('vicinity'),
                'types': place.get('types', []),
                'coordinates': {
                    'latitude': place.get('geometry', {}).get('location', {}).get('lat'),
                    'longitude': place.get('geometry', {}).get('location', {}).get('lng')
                },
                'is_open': place.get('opening_hours', {}).get('open_now'),
                'photos': place.get('photos', []),
                'source': 'google_places'
            }
            places.append(place_data)
        
        # Filter by budget
        filtered_places = filter_by_budget(places, budget)
        return filtered_places
        
    except requests.RequestException as e:
        print(f"Error calling Google Places API: {e}")
        return []

def get_nearby_recommendations(latitude: float, longitude: float, budget: str, radius: int = 5000) -> Dict[str, Any]:
    """
    Get comprehensive recommendations for restaurants and activities
    
    Args:
        latitude: GPS latitude
        longitude: GPS longitude
        budget: Budget level ('low', 'medium', 'high')
        radius: Search radius in meters
        
    Returns:
        Dictionary containing restaurants and activities
    """
    
    # Get restaurants from Yelp
    restaurants = search_yelp_restaurants(latitude, longitude, budget, radius)
    
    # Get activities from Google Places
    activities = []
    activity_types = ['tourist_attraction', 'amusement_park', 'museum', 'park', 'zoo', 'shopping_mall']
    
    for activity_type in activity_types:
        places = search_google_places(latitude, longitude, activity_type, budget, radius)
        activities.extend(places)
    
    # Remove duplicates and sort by rating
    unique_activities = []
    seen_ids = set()
    for activity in activities:
        if activity['id'] not in seen_ids:
            unique_activities.append(activity)
            seen_ids.add(activity['id'])
    
    # Sort by rating (descending)
    restaurants.sort(key=lambda x: x.get('rating', 0), reverse=True)
    unique_activities.sort(key=lambda x: x.get('rating', 0), reverse=True)
    
    return {
        'location': {
            'latitude': latitude,
            'longitude': longitude,
            'radius_meters': radius
        },
        'budget': budget,
        'restaurants': restaurants[:15],  # Limit to top 15
        'activities': unique_activities[:15],  # Limit to top 15
        'total_results': {
            'restaurants': len(restaurants),
            'activities': len(unique_activities)
        }
    }