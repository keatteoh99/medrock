import os
from dotenv import load_dotenv
import boto3
import json

load_dotenv()

# AWS credentials from .env
aws_access_key = os.environ.get("AWS_ACCESS_KEY_ID")
aws_secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
aws_region     = os.environ.get("AWS_DEFAULT_REGION")
aws_location_service_key = os.environ.get("AWS_LOCATION_SERVICE_KEY")

print(f"AWS Region: {aws_region}")

client = boto3.client(
    "geo-places",
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key,
    region_name="us-east-1"   # AWS Location currently in us-east-1
)

def search_nearby_places(longitude: float, latitude: float, category: str = 'hospital', radius: int = 5000):
    category_map = {
        'hospital': [
            'hospital',
            'hospital_emergency_room',
            'hospital_or_health_care_facility'
        ],
        'clinics': [
            'medical_services-clinics'
        ],
        'pharmacy': [
            'pharmacy',
            'drugstore_or_pharmacy'
        ],
        'dentist': [
            'dentist-dental_office'
        ]
    }
    response = client.search_nearby(
        Key=aws_location_service_key,
        QueryPosition=[longitude, latitude],
        QueryRadius=radius,
        MaxResults=10,
        Filter={
            'IncludeCategories': category_map.get(category, ['hospital'])
        },
        Language='en',
        AdditionalFeatures=['Contact'],
    )
    return response.get("ResultItems", [])


def normalize_places(raw_places):
    clean_list = []
    for item in raw_places:
        clean_list.append({
            'id': item.get('PlaceId'),
            'name': item.get('Title'),
            'address': item.get('Address', {}).get('Label', 'N/A'),
            "lat": item.get("Position", [None, None])[1],
            "lon": item.get("Position", [None, None])[0],
            "distance_m": item.get("Distance", "N/A"),
            "phone": (
                item.get("Contacts", {}).get("Phones", [{}])[0].get("Value", "N/A")
                if "Contacts" in item else "N/A"
            ),
            "website": (
                item.get("Contacts", {}).get("Websites", [{}])[0].get("Value", "N/A")
                if "Contacts" in item else "N/A"
            ),
            "category": (
                item.get("Categories", [{}])[0].get("Name", "N/A")
                if "Categories" in item else "N/A"
            ),
            "open_now": (
                item.get("OpeningHours", [{}])[0].get("OpenNow", False)
                if "OpeningHours" in item else None
            )
        })
    return clean_list


# Example test run
lon, lat = 101.6869, 3.1390   # Kuala Lumpur
raw = search_nearby_places(lon, lat, category="clinics", radius=3000)
cleaned = normalize_places(raw)

print(json.dumps(cleaned, indent=2))
