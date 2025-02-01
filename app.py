from flask import Flask
from flask_cors import CORS
from routes import init_app

# Initialize Flask application
app = Flask(__name__)

# Enable CORS
CORS(app)

# Initialize routes
app = init_app(app)

if __name__ == '__main__':

    # Set port
    port = 5002

    # Start Flask application
    app.run(host='0.0.0.0', debug=True, port=port)
