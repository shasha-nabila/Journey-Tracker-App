import re, gpxpy, csv, os, folium
from .models import StripeSubscription
from geopy.distance import geodesic
from config import ConfigClass
from werkzeug.utils import secure_filename
from .models import StripeSubscription,Location,Journey
import random
from datetime import datetime
from .extensions import db
from flask_login import current_user

def is_valid_password(password_hash):
    # Password must have at least 1 capital letter, 1 numeric, and be at least 8 characters long
    return bool(re.match(r'^(?=.*[A-Z])(?=.*\d).{8,}$', password_hash))

def calculate_projected_revenue(db):
    # Initial subscription counts for each plan
    weekly_subs = db.session.query(StripeSubscription).filter_by(plan='Weekly', active=True).count()
    monthly_subs = db.session.query(StripeSubscription).filter_by(plan='Monthly', active=True).count()
    yearly_subs = db.session.query(StripeSubscription).filter_by(plan='Yearly', active=True).count()

    # Subscription rates
    rates = {'Weekly': 3, 'Monthly': 10, 'Yearly': 100}

    projected_revenue = []
    for week in range(52):  # Predict revenue for each week up to a year
        # Apply a larger variability in churn and growth rates because of small subscriber base
        churn_rate = random.choice([0, 0.25])  # 0 or 25% chance to lose a subscriber
        growth_rate = random.choice([0, 0.25])  # 0 or 25% chance to gain a subscriber

        # Randomly decide if a subscriber is gained or lost
        if random.random() < churn_rate:
            if weekly_subs > 0:
                weekly_subs -= 1
            elif monthly_subs > 0:
                monthly_subs -= 1
            elif yearly_subs > 0:
                yearly_subs -= 1

        if random.random() < growth_rate:
            plan_choice = random.choice(['Weekly', 'Monthly', 'Yearly'])
            if plan_choice == 'Weekly':
                weekly_subs += 1
            elif plan_choice == 'Monthly':
                monthly_subs += 1
            elif plan_choice == 'Yearly':
                yearly_subs += 1

        # Calculate weekly revenue from all subscriptions
        revenue = (weekly_subs * rates['Weekly']) + (monthly_subs * rates['Monthly'] / 4) + (yearly_subs * rates['Yearly'] / 52)
        projected_revenue.append(revenue)

    return projected_revenue

def save_uploaded_file(file, upload_folder):
    # test
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
    
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    file_exists = os.path.exists(file_path)
    
    with open(file_path, 'a', newline='') as csvfile:  
        writer = csv.writer(csvfile)
        
        if not file_exists:
            writer.writerow(header)
        
        combined_row = []
        for row in data:
            combined_row.extend(row)  
        
        combined_row.append(current_time)

    
        writer.writerow(combined_row)

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

def uplaod_journey_database(user_id, total_distance, upload_time):
       
    new_journey = Journey(
        user_id=user_id,
        total_distance=total_distance,
        upload_time=upload_time
        )
        
    db.session.add(new_journey)
        
    db.session.commit()
        
    return new_journey

def add_locations_from_csv(csv_file_path_1,csv_file_path_2, user_id):

    with open(csv_file_path_1, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        first_row = next(reader)  
        total_distance = float(first_row['distance'])  
        upload_time = datetime.strptime(first_row['upload_time'], '%Y-%m-%d %H:%M:%S')  # upload_time 값을 얻습니다.

    new_journey = uplaod_journey_database(user_id, total_distance, upload_time)

    with open(csv_file_path_2, 'r') as csvfile:
        reader = csv.DictReader(csvfile)  
        for row in reader:
            
            location = Location(
                journey_id=new_journey.id,  
                init_latitude=float(row['latitude_init']),
                init_longitude=float(row['longitude_init']),
                goal_latitude=float(row['latitude_goal']),
                goal_longitude=float(row['longitude_goal'])
            )
            db.session.add(location)  
        db.session.commit()  
