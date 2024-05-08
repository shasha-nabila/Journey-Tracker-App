from app import create_app
# to run the app
app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True) # listen on all public IPs