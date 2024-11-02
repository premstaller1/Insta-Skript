from flask import Flask, render_template, request, Response, jsonify, session
import os
import pandas as pd
from werkzeug.utils import secure_filename
import requests
from main import generate_caption
from create_file import sanitize_filename
import json
import time
from datetime import datetime
import shutil
import logging

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

# Global flags to control process
stop_process_flag = False
pause_process_flag = False
logging.basicConfig(level=logging.INFO)


def save_details_to_file(details_path, project_details):
    """Helper function to save project details to a file."""
    try:
        with open(details_path, 'w', encoding='utf-8') as file:
            for key, value in project_details.items():
                file.write(f"{key}: {value}\n")
    except Exception as e:
        logging.error(f"Error saving details to file {details_path}: {e}")


def download_images(project_dir, visuals_links, caption_info):
    """Helper function to download images for a project."""
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
                    image_url = f"{BASE_URL}/static/data/newpost/{os.path.basename(project_dir)}/{image_filename}"
                    caption_info["images"].append(image_url)
                else:
                    logging.warning(f"Image at {url} could not be downloaded (Status code: {response.status_code})")
            except Exception as e:
                logging.error(f"Error downloading image from {url}: {e}")


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/upload_and_process', methods=['POST'])
def upload_and_process():
    global stop_process_flag, pause_process_flag
    stop_process_flag = False  # Reset stop flag when starting a new process
    pause_process_flag = False  # Reset pause flag
    
    file = request.files['file']
    if file and file.filename.endswith('.csv'):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        original_filename = secure_filename(file.filename)
        filename_with_timestamp = f"{timestamp}_{original_filename}"
        archived_file_path = os.path.join(ARCHIVE_FOLDER, filename_with_timestamp)
        file.save(archived_file_path)

        session['file_path'] = archived_file_path  # Save file path in session for streaming
        logging.info(f"File uploaded and saved to {archived_file_path}")
        return jsonify(success=True)

    logging.error("Failed to upload file or invalid file type")
    return jsonify(success=False), 400


@app.route('/stream_process', methods=['GET'])
def stream_process():
    global stop_process_flag, pause_process_flag
    file_path = session.get('file_path')
    if not file_path:
        logging.error("File path not found in session")
        return jsonify(success=False), 400

    def generate():
        logging.info(f"Starting caption generation from file: {file_path}")
        df = pd.read_csv(file_path)
        for index, row in df.iterrows():
            if stop_process_flag:
                logging.info("Process stopped by user")
                break  # Break the loop to stop the generator
            
            while pause_process_flag:
                logging.info("Process paused")
                time.sleep(1)  # Check every second if the process is resumed
            
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
            project_details = {
                "Project Name": project_name,
                "Description": description,
                "Designer": designer,
                "Company": company,
                "Support": support,
                "Caption": caption
            }
            save_details_to_file(details_path, project_details)

            # Download images and update URL paths
            download_images(project_dir, visuals_links, caption_info)

            yield f"data: {json.dumps(caption_info)}\n\n"
            time.sleep(1)

        logging.info("Generator stopped")
    
    return Response(generate(), mimetype='text/event-stream')


@app.route('/update_caption', methods=['POST'])
def update_caption():
    data = request.get_json()
    project_name = data['project_name']
    new_caption = data['caption']
    sanitized_project_name = sanitize_filename(project_name)

    project_dir = next((os.path.join(OUTPUT_FOLDER, folder_name) for folder_name in os.listdir(OUTPUT_FOLDER) if folder_name.startswith(sanitized_project_name)), None)
    if project_dir:
        details_path = os.path.join(project_dir, 'details.txt')
        project_details = {
            "Project Name": project_name,
            "Caption": new_caption,
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        save_details_to_file(details_path, project_details)
        return jsonify(success=True)
    else:
        logging.error(f"Project directory for {project_name} not found.")
        return jsonify(success=False), 404


@app.route('/delete_project', methods=['POST'])
def delete_project():
    data = request.get_json()
    project_name = data['project_name']
    sanitized_project_name = sanitize_filename(project_name)

    deleted = False
    for folder_name in os.listdir(OUTPUT_FOLDER):
        if folder_name.startswith(sanitized_project_name):
            project_dir = os.path.join(OUTPUT_FOLDER, folder_name)
            if os.path.isdir(project_dir):
                shutil.rmtree(project_dir)
                deleted = True
                logging.info(f"Project {project_name} deleted.")
    if deleted:
        return jsonify(success=True)
    else:
        logging.warning(f"Project folder {project_name} not found.")
        return jsonify(success=False, message="Project folder not found"), 404


@app.route('/stop_process', methods=['POST'])
def stop_process():
    global stop_process_flag
    stop_process_flag = True
    session.pop('file_path', None)  # Clear the file_path from session
    logging.info("Process stopped by user.")
    return jsonify(success=True)


@app.route('/pause_process', methods=['POST'])
def pause_process():
    global pause_process_flag
    pause_process_flag = not pause_process_flag  # Toggle pause state
    logging.info(f"Process {'paused' if pause_process_flag else 'resumed'}.")
    return jsonify(success=True, paused=pause_process_flag)


@app.route('/accept_project', methods=['POST'])
def accept_project():
    data = request.get_json()
    project_name = data['project_name']
    sanitized_project_name = sanitize_filename(project_name)

    # Find the project directory
    project_dir = next((os.path.join(OUTPUT_FOLDER, folder_name) for folder_name in os.listdir(OUTPUT_FOLDER) if folder_name.startswith(sanitized_project_name)), None)
    if project_dir:
        try:
            # Create a marker file or update an existing file to denote the project as accepted
            marker_file_path = os.path.join(project_dir, 'accepted.txt')
            with open(marker_file_path, 'w') as marker_file:
                marker_file.write("This project has been accepted and is not visible in the app.")
            logging.info(f"Project {project_name} accepted and marked as such.")
            return jsonify(success=True)
        except Exception as e:
            logging.error(f"Error accepting project {project_name}: {e}")
            return jsonify(success=False, message="Failed to accept the project"), 500
    else:
        logging.warning(f"Project folder {project_name} not found.")
        return jsonify(success=False, message="Project folder not found"), 404

if __name__ == "__main__":
    app.run(debug=True)
