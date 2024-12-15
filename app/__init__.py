from flask import Flask
from app.routes import main_bp, media_bp
import os

# Initialize the Flask app
app = Flask(__name__)
app.secret_key = 'your_generated_secret_key_here'

# Register main blueprint
app.register_blueprint(main_bp)

# Register the media blueprint with the prefix "/publish_instagram"
app.register_blueprint(media_bp, url_prefix='/publish_instagram')
