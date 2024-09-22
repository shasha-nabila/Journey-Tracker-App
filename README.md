# PuppyPilot: A Journey Tracker App
This repository was cloned from my university account, which was a group project developed with five other people. We created an application named PuppyPilot, designed to allow users to view and manage their travel journeys on a map. Users can register, upload GPS data, view their journeys, and access journey statistics. Admins can estimate revenue and review data related to registered customers.

## Features
### User Capabilities
- **Register and Pay:** Users can register and choose from weekly, monthly, or yearly payment plans to access all features.
- **Upload GPS Data:** Upload GPS data trails of their journeys.
- **Friend Other Users:** Users can be friends with other users and let each other see their journeys.
- **View Journeys:** Display one or more journeys of their own and friends on a map.
- **Journey Statistics:** Access statistics about their journeys.

### Admin Capabilities
- **Revenue Estimation:** Generate estimates of revenue based on subscribed customers.
- **Data Review:** Access data related to all registered customers.

## Technical Details
- **Framework:** Flask
- **Database:** SQLAlchemy
- **Payment System:** Stripe API
- **GPS Data Format:** GPX
- **Map Visualisation:** Folium library, Google Maps API
- **Testings:** Pytest

## User View

![image](https://github.com/user-attachments/assets/68102a30-b6be-40a4-ab2e-6e326ac3dada)
![image](https://github.com/user-attachments/assets/1fe2a37d-eceb-459f-93c2-5aabcfc199be)
![image](https://github.com/user-attachments/assets/ea5eae27-afa3-4298-9883-b44ed33122da)
![image](https://github.com/user-attachments/assets/17dea1a5-2948-444c-93cb-cf49fbe75dba)
![image](https://github.com/user-attachments/assets/df3a13ab-3164-4df1-adc5-822269acc2e1)
![image](https://github.com/user-attachments/assets/8d54cae6-a885-4c47-9cf8-820f7602004a)
![image](https://github.com/user-attachments/assets/5f283f47-5efa-413b-923d-b6853b1b3184)
![image](https://github.com/user-attachments/assets/4ad0f217-89f5-4189-bf75-303b69007622)

## Admin View
![image](https://github.com/user-attachments/assets/4519b341-7786-44ee-8e0a-c9d6a4e3c00e)
![image](https://github.com/user-attachments/assets/44d71e5e-6fac-483d-bd3e-e26945e52b89)

## Installation and Deployment Guide
### Prerequisites
Before you begin the installation, ensure your system meets the following requirements:
- Python 3.8 or newer
- Docker (if you prefer to use a containerized environment)
- Git installed on your machine

### Cloning the Repository & Setting it Up
1. First, you need to clone this repository containing PuppyPilot.
```
git clone <repo-url>
```
2. After cloning the repository, you need to create a `.env` file in the root directory of the project to include your own Stripe keys.
```
STRIPE_SECRET_KEY=your-stripe-secret-key-here
STRIPE_PUBLISHABLE_KEY=your-stripe-publishable-key-here
```
### Running the App
There are two options: Running it locally or using Docker. Both options are guided below:

#### 1. Running Locally
To run it locally, you would need to install all the required Python packages using:
```
pip install -r requirements.txt
```
Then, to set up the database for the app, you'll need to run several commands to initialize and migrate the database schema.
```
flask db init
flask db migrate -m "Initial migration."
flask db upgrade
```
Now, you can run the app locally by using:
```
flask run
```
This command will start a local server, typically accessible at http://127.0.0.1:5000 in your web browser.

#### 2. Using Docker
Ensure Docker Desktop is installed. You can download it from the official Docker website.
Then, open your terminal or command prompt and navigate to the project root directory.
Build the Docker image by running:
```
docker build -t puppypilot .
```
Run the Docker container with:
```
docker run -p 5000:5000 puppypilot
```
This will build a Docker image named puppypilot and run it, mapping port 5000 of the container to port 5000 on your host. This setup allows you to access the app in your web browser similarly to running it locally.

### Troubleshooting
If you encounter any issues during the installation of Python packages, make sure your pip is up to date.
For Docker, ensure Docker Desktop or your Docker environment is correctly set up and running.
For additional help or issues, please raise an issue in the repository or consult the Flask and Docker documentation.
