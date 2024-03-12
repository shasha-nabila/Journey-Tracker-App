import re, gpxpy, csv, os, folium
from .models import StripeSubscription
from geopy.distance import geodesic
from config import ConfigClass
from werkzeug.utils import secure_filename

def is_valid_password(password_hash):
    # Password must have at least 1 capital letter, 1 numeric, and be at least 8 characters long
    return bool(re.match(r'^(?=.*[A-Z])(?=.*\d).{8,}$', password_hash))

def calculate_projected_revenue(db):
    # Assuming `db` is your SQLAlchemy session

    # Calculate the number of active subscriptions for each plan
    weekly_subs = db.session.query(StripeSubscription).filter_by(plan='Weekly', active=True).count()
    monthly_subs = db.session.query(StripeSubscription).filter_by(plan='Monthly', active=True).count()
    yearly_subs = db.session.query(StripeSubscription).filter_by(plan='Yearly', active=True).count()

    # Subscription rates
    rates = {'Weekly': 3, 'Monthly': 10, 'Yearly': 100}

    # Project revenue for 52 weeks
    projected_revenue = []
    for week in range(52):
        revenue = weekly_subs * rates['Weekly'] + (monthly_subs * rates['Monthly'] / 4) + (yearly_subs * rates['Yearly'] / 52)
        projected_revenue.append(revenue)
        weekly_subs += 0  # Update this if you expect changes in subscription numbers over time
        monthly_subs += 0  # Update this if you expect changes in subscription numbers over time
        yearly_subs += 0  # Update this if you expect changes in subscription numbers over time

    return projected_revenue

def save_uploaded_file(file, upload_folder):

    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    filename = secure_filename(file.filename)
    file_path = os.path.join(upload_folder, filename)
    file.save(file_path)

    return file_path

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

def create_and_append_csv(file_path, header, data):
 
    with open(file_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(header)
        writer.writerows(data)

def create_map_html(coordinates):
 
    m = folium.Map(location=coordinates[0], zoom_start=17)
    initial_coordinate = coordinates[0]
    goal_coordinate = coordinates[-1]
    initial_marker = folium.Marker(initial_coordinate, tooltip='Departure', icon=folium.Icon(color='green')).add_to(m)
    goal_marker = folium.Marker(goal_coordinate, tooltip='Arrival', icon=folium.Icon(color='green')).add_to(m)
    folium.PolyLine(coordinates).add_to(m)
    
    return m._repr_html_()

def calculate_distance(point1, point2):
    coords_1 = (point1['latitude'], point1['longitude'])
    coords_2 = (point2['latitude'], point2['longitude'])
    return geodesic(coords_1, coords_2).meters
