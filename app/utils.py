import re, gpxpy, csv
from geopy.distance import geodesic
from config import ConfigClass

def is_valid_password(password_hash):
    # Password must have at least 1 capital letter, 1 numeric, and be at least 8 characters long
    return bool(re.match(r'^(?=.*[A-Z])(?=.*\d).{8,}$', password_hash))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ConfigClass.ALLOWED_EXTENSIONS

def parse_gpx(file_path):
    # open filename.gpx 
    gpx_file = open(file_path, 'r')
    gpx = gpxpy.parse(gpx_file)
    points = []
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                points.append((point.latitude, point.longitude))
       
    return points


def info_parse_gpx(file_path):
    with open(file_path, 'r') as gpx_file:
        gpx = gpxpy.parse(gpx_file)
        info = []
        for point in gpx.waypoints:
            info.append({
                'name': point.name,
                'latitude': point.latitude,
                'longitude': point.longitude,
                'address': point.description
            })
        return info

def append_to_csv(filename, data):
    with open(filename, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(data)

def create_csv_file(filename, header):
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(header)

def calculate_distance(point1, point2):
    coords_1 = (point1['latitude'], point1['longitude'])
    coords_2 = (point2['latitude'], point2['longitude'])
    return geodesic(coords_1, coords_2).meters

