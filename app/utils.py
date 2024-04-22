import re, gpxpy, csv, os, folium
from .models import StripeCustomer, StripeSubscription
from geopy.distance import geodesic
from config import ConfigClass
from werkzeug.utils import secure_filename
from .models import StripeSubscription,Location,Journey,Filepath
from sqlalchemy.orm import aliased
import random
from datetime import datetime
from .extensions import db
from flask_login import current_user
import matplotlib.pyplot as plt
import matplotlib
from flask_sqlalchemy import SQLAlchemy
matplotlib.use('Agg') 


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

def create_multiple_route_map_html(gpx_file):

    map = folium.Map(Location =[0, 0], zoom_start = 2)

    for gpx_file in gpx_file:
        coordinates = parse_gpx(gpx_file)
        if coordinates:
            folium.PolyLine(coordinates).add_to(map)
    
    return map._repr_html_()
     

def calculate_distance(point1, point2):
    coords_1 = (point1['latitude'], point1['longitude'])
    coords_2 = (point2['latitude'], point2['longitude'])
    return geodesic(coords_1, coords_2).meters

def upload_journey_database(csv_file_path, user_id):

    with open(csv_file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:

            existing_journey = Journey.query.filter_by(
                user_id = user_id,
                total_distance=float(row['distance']),
                upload_time = datetime.strptime(row['upload_time'], '%Y-%m-%d %H:%M:%S')
                
            ).first()

            if not existing_journey:
                new_journey = Journey(
                    user_id = user_id,
                    total_distance=float(row['distance']),
                    upload_time = datetime.strptime(row['upload_time'], '%Y-%m-%d %H:%M:%S')
                )
                db.session.add(new_journey)
        db.session.commit()
    
    return new_journey

def upload_filepath_database(new_journey, image_file_path, gpx_file_path):
   
    new_filepath = Filepath(
    journey_id=new_journey.id,
    image_file_path=image_file_path,
    gpx_file_path=gpx_file_path
        )
    db.session.add(new_filepath)
    db.session.commit()

def upload_location_database(csv_file_path, new_journey):

    with open(csv_file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:

            existing_location = Location.query.filter_by(
                upload_time=datetime.strptime(row['upload_date'], '%Y-%m-%d %H:%M:%S')
            ).first()
         
            if not existing_location:
                location = Location(
                    journey_id=new_journey.id,  
                    init_latitude=float(row['latitude_init']),
                    init_longitude=float(row['longitude_init']),
                    goal_latitude=float(row['latitude_goal']),
                    goal_longitude=float(row['longitude_goal']),
                    departure=row['name_init'],
                    arrival=row['name_goal'],
                    upload_time = datetime.strptime(row['upload_date'], '%Y-%m-%d %H:%M:%S')
                )
                db.session.add(location)
        db.session.commit()
 
def create_route_image(coordinates, output_dir):

    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = f"{output_dir}/{current_time}_route.png"

    latitudes, longitudes = zip(*coordinates)

    plt.figure(figsize=(8, 6))
    plt.plot(longitudes, latitudes, color='white', linewidth=3)  
    plt.gca().set_facecolor('black') 


    plt.gca().axes.get_xaxis().set_visible(False)
    plt.gca().axes.get_yaxis().set_visible(False)


    plt.subplots_adjust(top=1, bottom=0, right=1, left=0, 
                        hspace=0, wspace=0)
    plt.margins(0,0)


    plt.savefig(file_path, format='png', dpi=300, bbox_inches='tight', pad_inches=0)
    plt.close()

    return file_path 

def find_active_subscription(user):
    # Alias for StripeCustomer to use in our subquery
    stripe_customer_alias = aliased(StripeCustomer)
    
    # Find the active subscription for this user
    active_subscription = StripeSubscription.query.join(
        stripe_customer_alias, 
        stripe_customer_alias.id == StripeSubscription.stripe_customer_id
    ).filter(
        stripe_customer_alias.user_id == user.id,
        StripeSubscription.active == True
    ).order_by(StripeSubscription.start_date.desc()).first()  # Assuming you want the latest subscription
    
    return active_subscription.plan if active_subscription else 'No Subscription'