# Use an official Python runtime as a parent image
FROM python:3.8-slim-buster

# Set the working directory in the container
WORKDIR /puppypilot

# Copy the current directory contents into the container at /app
COPY . /puppypilot

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Run database migrations
RUN flask db init
RUN flask db migrate
RUN flask db upgrade

# Run app.py when the container launches
CMD ["python", "run.py"]