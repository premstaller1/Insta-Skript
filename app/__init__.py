from flask import Flask
from app.routes import main_bp, media_bp
import os

# Initialize the Flask app
app = Flask(__name__)
app.secret_key = 'your_generated_secret_key_here'

# Configure directories
OUTPUT_FOLDER = 'app/static/data/newpost'
ARCHIVE_FOLDER = 'app/static/data/submissions'
UPLOAD_FOLDER = "app/static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(ARCHIVE_FOLDER, exist_ok=True)

# Register main blueprint
app.register_blueprint(main_bp)

# Register the media blueprint with the prefix "/publish_instagram"
app.register_blueprint(media_bp, url_prefix='/publish_instagram')
