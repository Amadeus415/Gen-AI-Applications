# faceranking - Rating faces based on beauty and age using Face++ API

import requests
import os

def call_faceplusplus_api(image_stream):
    """Call Face++ API and return beauty score and age"""
    url = 'https://api-us.faceplusplus.com/facepp/v3/detect'
    
    files = {'image_file': image_stream}
    data = {
        'api_key': os.getenv('FACEPLUS_API_KEY'),
        'api_secret': os.getenv('FACEPLUS_API_SECRET'),
        'return_attributes': 'beauty,age'  # Added age attribute
    }
    
    try:
        response = requests.post(url, files=files, data=data)
        response.raise_for_status()
        result = response.json()
        
        if 'faces' not in result or not result['faces']:
            return {'error': 'No face detected in the image'}
            
        face = result['faces'][0]
        attributes = face['attributes']
        
        return {
            'beauty_score': (attributes['beauty']['male_score'] + attributes['beauty']['female_score']) / 2,
            'age': attributes['age']['value']
        }
        
    except requests.exceptions.RequestException as e:
        return {'error': f'API request failed: {str(e)}'}
    except KeyError as e:
        return {'error': f'Unexpected API response format: {str(e)}'}
    except Exception as e:
        return {'error': f'An error occurred: {str(e)}'}


