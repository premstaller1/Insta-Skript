# app.py
from flask import Flask, render_template, request, Response, jsonify, session
import os
import shutil
import pandas as pd
from werkzeug.utils import secure_filename
import requests
from main import generate_caption
from create_file import sanitize_filename
import json
import time
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'supersecretkey'
UPLOAD_FOLDER = 'data/submissions'
OUTPUT_FOLDER = 'static/data/newpost'
ARCHIVE_FOLDER = 'static/data/submissions'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload, output, and archive directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(ARCHIVE_FOLDER, exist_ok=True)

BASE_URL = "http://127.0.0.1:5000"  # Base URL for constructing image paths

# Global flag to control process
stop_process = False

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/upload_and_process', methods=['POST'])
def upload_and_process():
    global stop_process
    stop_process = False  # Reset the stop flag when a new process starts
    
    file = request.files['file']
    if file and file.filename.endswith('.csv'):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        original_filename = secure_filename(file.filename)
        filename_with_timestamp = f"{timestamp}_{original_filename}"
        archived_file_path = os.path.join(ARCHIVE_FOLDER, filename_with_timestamp)
        file.save(archived_file_path)

        session['file_path'] = archived_file_path  # Save file path in session for streaming
        return jsonify(success=True)

    return jsonify(success=False), 400

@app.route('/stream_process', methods=['GET'])
def stream_process():
    global stop_process
    file_path = session.get('file_path')
    if not file_path:
        return jsonify(success=False), 400

    def generate():
        df = pd.read_csv(file_path)
        for index, row in df.iterrows():
            # Check if stop_process flag is set to True
            if stop_process:
                break  # Exit the loop if the stop flag is set

            project_name = row['Project Name']
            description = row['Project Description']
            designer = row['Instagram @']
            visuals_links = row['Upload your Visuals (max. 10!)']
            support = row.get("Support Frabiché", "")
            company = row.get("Company Name", "")

            # Generate caption
            caption = generate_caption(project_name, description, designer)
            sanitized_project_name = sanitize_filename(project_name)
            project_dir = os.path.join(OUTPUT_FOLDER, f"{sanitized_project_name}_{index+1}")
            os.makedirs(project_dir, exist_ok=True)

            # Caption and image info for the current project
            caption_info = {
                "project_name": project_name,
                "caption": caption,
                "images": []
            }

            # Save project details to a text file
            details_path = os.path.join(project_dir, 'details.txt')
            with open(details_path, 'w', encoding='utf-8') as file:
                file.write(f"Project Name: {project_name}\n")
                file.write(f"Description: {description}\n")
                file.write(f"Designer: {designer}\n")
                file.write(f"Company: {company}\n")
                file.write(f"Support: {support}\n")
                file.write(f"Caption: {caption}\n")

            # Download images and update URL paths
            if pd.notna(visuals_links):
                urls = visuals_links.split(';')
                for i, url in enumerate(urls):
                    try:
                        response = requests.get(url.strip())
                        if response.status_code == 200:
                            image_filename = f'image_{i+1}.jpg'
                            image_path = os.path.join(project_dir, image_filename)
                            with open(image_path, 'wb') as img_file:
                                img_file.write(response.content)
                            image_url = f"{BASE_URL}/static/data/newpost/{sanitized_project_name}_{index+1}/{image_filename}"
                            caption_info["images"].append(image_url)
                    except Exception as e:
                        print(f"Error downloading image from {url}: {e}")

            yield f"data: {json.dumps(caption_info)}\n\n"
            time.sleep(1)  # Optional delay for pacing

    return Response(generate(), mimetype='text/event-stream')

@app.route('/stop_process', methods=['POST'])
def stop_process_route():
    global stop_process
    stop_process = True  # Set the stop flag to True
    return jsonify(success=True)
