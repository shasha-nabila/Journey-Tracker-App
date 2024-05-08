import re, gpxpy, csv, os, folium
from .models import StripeCustomer, StripeSubscription
from geopy.distance import geodesic
from config import ConfigClass
from werkzeug.utils import secure_filename
from .models import StripeSubscription,Location,Journey,Filepath,User
from sqlalchemy.orm import aliased
import random
from datetime import datetime
from .extensions import db
from flask_login import current_user
import matplotlib.pyplot as plt
import matplotlib
from flask_sqlalchemy import SQLAlchemy
from flask import flash, redirect, url_for
import gpxpy.gpx

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
    with open(file_path, 'r') as gpx_file:
        gpx = gpxpy.parse(gpx_file)
        points = []
        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    points.append({
                        'latitude': point.latitude,
                        'longitude': point.longitude,
                        'name': point.name if hasattr(point, 'name') else ''
                    })
    start_point = points[0] if points else None
    end_point = points[-1] if points else None
    return points, start_point, end_point

def info_parse_gpx(file_path):
    # open gpx file
    with open(file_path, 'r') as gpx_file:
        gpx = gpxpy.parse(gpx_file)
        # store datas associated with departure, arrival
        info = []
        for point in gpx.waypoints:
            info.append({
                'name': point.name,
                'latitude': point.latitude,
                'longitude': point.longitude,
                'address': point.description
            })
        return info

# create csv file for log
def create_and_append_csv(file_path, header, data, current_id):
    
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
        
        combined_row.append(current_id)

        writer.writerow(combined_row)

def create_map_html(file_path): 
    coordinates, start_point, end_point = parse_gpx(file_path)
    m = folium.Map(location=[start_point['latitude'], start_point['longitude']], zoom_start=15)
    folium.Marker(
        [start_point['latitude'], start_point['longitude']], 
        popup=f"Start point", 
        icon=folium.Icon(color='green')
    ).add_to(m)
    folium.Marker(
        [end_point['latitude'], end_point['longitude']], 
        popup=f"End point", 
        icon=folium.Icon(color='red')
    ).add_to(m)
    folium.PolyLine([(point['latitude'], point['longitude']) for point in coordinates], color='blue').add_to(m)

    # Fit the map to include all markers
    m.fit_bounds([[
        start_point['latitude'], start_point['longitude']],
        [end_point['latitude'], end_point['longitude']]
    ])

    return m._repr_html_()

def create_multiple_route_map_html(gpx_file_paths):

    map_center = [53.8008, -1.5491]  # Center of Leeds, for example
    map = folium.Map(location=map_center, zoom_start=13)
    colors = ['blue', 'green', 'red', 'purple', 'orange']  # Define more colors as needed

    for index, path in enumerate(gpx_file_paths):
        coordinates, start_point, end_point = parse_gpx(path)
        route_color = colors[index % len(colors)]  # Cycle through colors
        folium.PolyLine([(point['latitude'], point['longitude']) for point in coordinates], color=route_color).add_to(map)
        folium.Marker(
            [start_point['latitude'], start_point['longitude']], 
            popup=f"Start point", 
            icon=folium.Icon(color='green')
        ).add_to(map)
        folium.Marker(
            [end_point['latitude'], end_point['longitude']], 
            popup=f"End point", 
            icon=folium.Icon(color='red')
        ).add_to(map)

    # Fit the map to include all markers
    map.fit_bounds([[
        start_point['latitude'], start_point['longitude']],
        [end_point['latitude'], end_point['longitude']]
    ])
    return map._repr_html_()
     
def parse_gpx_and_calculate_distance(gpx_file_path):

    with open(gpx_file_path, 'r') as gpx_file:
        gpx = gpxpy.parse(gpx_file)

    total_distance = 0.0  

    for track in gpx.tracks:
        for segment in track.segments:
 
            total_distance += segment.length_3d() 

    return total_distance

def upload_journey_database(csv_file_path, user_id, total_distance):

    with open(csv_file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if int(row['user_id']) == user_id:
   
                existing_journey = Journey.query.filter_by(
                    upload_time = datetime.strptime(row['upload_date'], '%Y-%m-%d %H:%M:%S')
                
                ).first()
            # Check duplicated data
                if not existing_journey:
                    new_journey = Journey(
                        user_id = user_id,
                        total_distance=total_distance,
                        upload_time = datetime.strptime(row['upload_date'], '%Y-%m-%d %H:%M:%S')
                    )
                    db.session.add(new_journey)
        db.session.commit()
    
    return new_journey

def upload_filepath_database(new_journey, image_file_path, gpx_file_path,user_id):
   
    new_filepath = Filepath(
    user_id = user_id,
    journey_id=new_journey.id,
    image_file_path=image_file_path,
    gpx_file_path=gpx_file_path
        )
    db.session.add(new_filepath)
    db.session.commit()

def upload_location_database(csv_file_path, new_journey, user_id):

    with open(csv_file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if int(row['user_id']) == user_id:
 
                existing_location = Location.query.filter_by(
                    upload_time=datetime.strptime(row['upload_date'], '%Y-%m-%d %H:%M:%S')
                ).first()
         
                if not existing_location:
                    location = Location(
                        user_id = user_id,
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

    latitudes, longitudes = zip(*[(coord['latitude'], coord['longitude']) for coord in coordinates if 'latitude' in coord and 'longitude' in coord])

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