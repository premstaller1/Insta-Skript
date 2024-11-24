from flask import Flask, render_template, request, Response, jsonify, session
import os
import pandas as pd
from werkzeug.utils import secure_filename
import requests
from archive.langchain import generate_caption
from archive.create_file import sanitize_filename
import json
import time
from datetime import datetime
import shutil
import logging

app = Flask(__name__)
app.secret_key = 'supersecretkey'
OUTPUT_FOLDER = 'static/data/newpost'
ARCHIVE_FOLDER = 'static/data/submissions'

# Ensure upload, output, and archive directories exist
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(ARCHIVE_FOLDER, exist_ok=True)

BASE_URL = "http://127.0.0.1:5000"  # Base URL for constructing image paths

# Global flags to control process
stop_process_flag = False
pause_process_flag = False
logging.basicConfig(level=logging.INFO)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/caption_generator')
def caption_generator():
    return render_template('caption_generator.html')

@app.route('/publish_instagram')
def publish_instagram():
    return render_template('publish_instagram.html')  # Replace with the Instagram publish HTML file.


def save_details_to_file(details_path, project_details):
    """Helper function to save project details to a file."""
    try:
        with open(details_path, 'w', encoding='utf-8') as file:
            for key, value in project_details.items():
                file.write(f"{key}: {value}\n")
    except Exception as e:
        logging.error(f"Error saving details to file {details_path}: {e}")


def download_images(project_dir, visuals_links, caption_info):
    """Helper function to download images and videos for a project."""
    if pd.notna(visuals_links):
        urls = visuals_links.split(';')
        for i, url in enumerate(urls):
            try:
                url = url.strip()
                if "video.wixstatic.com/video/" in url:
                    filename = f'video_{i+1}.mp4'  # Assume videos are MP4
                    category = "videos"
                elif "static.wixstatic.com/media/" in url:
                    # Extract the file extension for images
                    file_extension = os.path.splitext(url.split('?')[0])[1]
                    if file_extension.lower() not in ['.jpg', '.jpeg', '.png', '.gif']:
                        logging.warning(f"Unrecognized file extension for URL {url}: {file_extension}")
                        continue
                    filename = f'image_{i+1}{file_extension}'
                    category = "images"
                else:
                    logging.warning(f"Unrecognized URL pattern for URL {url}")
                    continue

                # Download and save the file
                response = requests.get(url, stream=True)
                if response.status_code == 200:
                    file_path = os.path.join(project_dir, filename)
                    with open(file_path, 'wb') as file:
                        shutil.copyfileobj(response.raw, file)

                    # Add the file URL to the appropriate category
                    file_url = f"{BASE_URL}/static/data/newpost/{os.path.basename(project_dir)}/{filename}"
                    logging.info(f"File saved to: {file_path}")
                    caption_info[category].append(file_url)
                else:
                    logging.warning(f"File at {url} could not be downloaded (Status code: {response.status_code})")
            except Exception as e:
                logging.error(f"Error downloading file from {url}: {e}")


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

            # Caption and media info for the current project
            caption_info = {
                "project_name": project_name,
                "caption": caption,
                "images": [],
                "videos": []
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

            # Download images and videos and update URL paths
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
