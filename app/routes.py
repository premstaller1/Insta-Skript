from flask import Blueprint, render_template, request, Response, session, jsonify, url_for
from app.utils import save_details_to_file, download_images, create_media_container, publish_media_container
from app.services import generate_caption, sanitize_filename
from app.config import get_creds
import os
import pandas as pd
import json
import time
from datetime import datetime
import logging
import shutil
from werkzeug.utils import secure_filename

main_bp = Blueprint('main', __name__)
media_bp = Blueprint("media", __name__)

BASE_URL = "http://127.0.0.1:5000"
OUTPUT_FOLDER = 'app/static/data/newpost'
ARCHIVE_FOLDER = 'app/static/data/submissions'
UPLOAD_FOLDER = "static/uploads"

stop_process_flag = False
pause_process_flag = False

logging.basicConfig(level=logging.INFO)

@main_bp.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@main_bp.route('/caption_generator', methods=['GET'])
def caption_generator():
    return render_template('caption_generator.html')

@media_bp.route("/", methods=["GET"])
def index():
    return render_template('publish_instagram.html')

#################################################################################

@main_bp.route('/upload_and_process', methods=['POST'])
def upload_and_process():
    global stop_process_flag, pause_process_flag
    stop_process_flag = False
    pause_process_flag = False

    try:
        logging.info("Upload process started.")
        file = request.files['file']
        if file and file.filename.endswith('.csv'):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            original_filename = secure_filename(file.filename)
            filename_with_timestamp = f"{timestamp}_{original_filename}"
            archived_file_path = os.path.join(ARCHIVE_FOLDER, filename_with_timestamp)
            logging.info(f"Saving file: {archived_file_path}")
            file.save(archived_file_path)

            session['file_path'] = archived_file_path
            logging.info(f"File uploaded and saved to {archived_file_path}")
            return jsonify(success=True)
        else:
            logging.error("Failed to upload file: Invalid file type or no file provided.")
            return jsonify(success=False), 400
    except Exception as e:
        logging.exception("Error occurred during file upload and process.")
        return jsonify(success=False, message=str(e)), 500


@main_bp.route('/stream_process', methods=['GET'])
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
                break

            while pause_process_flag:
                logging.info("Process paused")
                time.sleep(1)

            project_name = row['Project Name']
            description = row['Project Description']
            designer = row['Instagram @']
            visuals_links = row['Upload your Visuals (max. 10!)']

            caption = generate_caption(project_name, description, designer)
            sanitized_project_name = sanitize_filename(project_name)
            project_dir = os.path.join(OUTPUT_FOLDER, f"{sanitized_project_name}_{index+1}")
            os.makedirs(project_dir, exist_ok=True)

            caption_info = {
                "project_name": project_name,
                "caption": caption,
                "images": [],
                "videos": []
            }

            details_path = os.path.join(project_dir, 'details.txt')
            project_details = {
                "Project Name": project_name,
                "Description": description,
                "Designer": designer,
                "Caption": caption
            }
            save_details_to_file(details_path, project_details)
            download_images(project_dir, visuals_links, caption_info)

            yield f"data: {json.dumps(caption_info)}\n\n"
            time.sleep(1)

        logging.info("Generator stopped")

    return Response(generate(), mimetype='text/event-stream')

@main_bp.route('/update_caption', methods=['POST'])
def update_caption():
    data = request.get_json()
    project_name = data['project_name']
    description = data['Project Description']
    designer = data['Instagram @']
    new_caption = data['caption']
    sanitized_project_name = sanitize_filename(project_name)

    project_dir = next((os.path.join(OUTPUT_FOLDER, folder_name) for folder_name in os.listdir(OUTPUT_FOLDER) if folder_name.startswith(sanitized_project_name)), None)
    if project_dir:
        details_path = os.path.join(project_dir, 'details.txt')
        project_details = {
            "Project Name": project_name,
            "Description": description,
            "Designer": designer,
            "Caption": new_caption,
            "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        save_details_to_file(details_path, project_details)
        return jsonify(success=True)
    else:
        logging.error(f"Project directory for {project_name} not found.")
        return jsonify(success=False), 404

@main_bp.route('/delete_project', methods=['POST'])
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

@main_bp.route('/stop_process', methods=['POST'])
def stop_process():
    global stop_process_flag
    stop_process_flag = True
    session.pop('file_path', None)
    logging.info("Process stopped by user.")
    return jsonify(success=True)

@main_bp.route('/pause_process', methods=['POST'])
def pause_process():
    global pause_process_flag
    pause_process_flag = not pause_process_flag
    logging.info(f"Process {'paused' if pause_process_flag else 'resumed'}.")
    return jsonify(success=True, paused=pause_process_flag)

@main_bp.route('/accept_project', methods=['POST'])
def accept_project():
    data = request.get_json()
    project_name = data['project_name']
    sanitized_project_name = sanitize_filename(project_name)

    project_dir = next((os.path.join(OUTPUT_FOLDER, folder_name) for folder_name in os.listdir(OUTPUT_FOLDER) if folder_name.startswith(sanitized_project_name)), None)
    if project_dir:
        try:
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


#######################################################################

MAX_MEDIA_COUNT = 10
uploaded_files = []

@media_bp.route("/upload", methods=["POST"])
def upload_media():
    if len(uploaded_files) >= MAX_MEDIA_COUNT:
        return jsonify(success=False, message="You can upload a maximum of 10 files."), 400

    file = request.files.get("file")
    if not file:
        return jsonify(success=False, message="No file uploaded."), 400

    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in [".jpg", ".jpeg", ".mp4"]:
        return jsonify(success=False, message="Only JPG and MP4 files are allowed."), 400

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)
    uploaded_files.append({"filename": file.filename, "path": file_path})

    return jsonify(success=True, files=uploaded_files)

@media_bp.route("/delete", methods=["POST"])
def delete_media():
    file_name = request.json.get("filename")
    for file in uploaded_files:
        if file["filename"] == file_name:
            uploaded_files.remove(file)
            os.remove(file["path"])
            return jsonify(success=True, files=uploaded_files)

    return jsonify(success=False, message="File not found."), 404

@media_bp.route("/publish", methods=["POST"])
def publish_media():
    profile = request.json.get("profile")
    caption = request.json.get("caption", "")

    if not profile:
        return jsonify(success=False, message="No profile selected."), 400

    if not uploaded_files:
        return jsonify(success=False, message="No media to publish."), 400

    creds = get_creds(profile)
    container_ids = []

    # Create individual media containers
    try:
        for file in uploaded_files:
            media_url = request.host_url + f"static/uploads/{file['filename']}"
            container_id = create_media_container(
                creds["access_token"],
                creds["instagram_account_id"],
                image_url=media_url,
                caption=caption
            )
            container_ids.append(container_id)

        # Create carousel container if more than one file
        if len(container_ids) > 1:
            carousel_container_id = create_media_container(
                creds["access_token"],
                creds["instagram_account_id"],
                is_carousel=True,
                children=container_ids,
                caption=caption
            )
            publish_media_container(
                creds["access_token"],
                creds["instagram_account_id"],
                carousel_container_id
            )
        else:
            publish_media_container(
                creds["access_token"],
                creds["instagram_account_id"],
                container_ids[0]
            )

        return jsonify(success=True, message="Media published successfully!")
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500