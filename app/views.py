# Can edit based on app's requirements
from flask import Flask, render_template, flash, redirect, url_for, jsonify, request
from app import app, db

# Import models and forms

# Main Page view
@app.route('/')
def main():
    return render_template("main.html")

# Include other views here vv