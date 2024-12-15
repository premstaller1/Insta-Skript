from flask import Blueprint, render_template, request, Response, session, jsonify, current_app
from app.utils import save_details_to_file, download_images, create_carousel_item, create_carousel_container, publish_carousel
from app.services import generate_caption, sanitize_filename
from app.config import get_creds
from datetime import datetime
import vercel_blob
import os
import pandas as pd
import json
import time
import logging
import shutil

main_bp = Blueprint('main', __name__)
media_bp = Blueprint("media", __name__)

OUTPUT_FOLDER = '/tmp/newpost'
ARCHIVE_FOLDER = '/tmp/submissions'
UPLOAD_FOLDER = '/tmp/uploads'

stop_process_flag = False
pause_process_flag = False

logging.basicConfig(level=logging.INFO)

# Ensure necessary directories exist locally (still using local directories for temp storage)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(ARCHIVE_FOLDER, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@main_bp.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@main_bp.route('/caption_generator', methods=['GET'])
def caption_generator():
    return render_template('caption_generator.html')


@media_bp.route("/", methods=["GET"])
def publish_instagram():
    return render_template('publish_instagram.html')


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
            
            # Use vercel_blob to upload the file
            file_content = file.read()
            blob_response = vercel_blob.put(filename_with_timestamp, file_content)
            archived_file_url = blob_response['url']

            logging.info(f"File uploaded to Vercel Blob: {archived_file_url}")
            session['file_url'] = archived_file_url
            return jsonify(success=True)
        else:
            logging.error("Failed to upload file: Invalid file type or no file provided.")
            return jsonify(success=False, message="Invalid file type."), 400
    except Exception as e:
        logging.exception("Error occurred during file upload and process.")
        return jsonify(success=False, message=str(e)), 500


@main_bp.route('/stream_process', methods=['GET'])
def stream_process():
    file_url = session.get('file_url')
    if not file_url:
        logging.error("File URL not found in session")
        return jsonify(success=False, message="No file found in session."), 400

    def generate():
        logging.info(f"Starting caption generation from file: {file_url}")

        # Download the file from Vercel Blob
        file_content = vercel_blob.download_file(file_url)
        df = pd.read_csv(file_content)

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
                "description": description,  # Include description
                "designer": designer,        # Include designer
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

            # Download and upload images to vercel_blob
            download_images(project_dir, visuals_links, caption_info)

            yield f"data: {json.dumps(caption_info)}\n\n"
            time.sleep(1)

    return Response(generate(), mimetype='text/event-stream')


@main_bp.route('/update_caption', methods=['POST'])
def update_caption():
    data = request.get_json()
    project_name = data['project_name']
    description = data['description']
    designer = data['designer']
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
    session.pop('file_url', None)
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

@media_bp.route("/upload_carousel", methods=["POST"])
def upload_carousel():
    """
    Handle uploading media for carousel posts and creating individual containers.
    """
    try:
        # Log request details
        logging.info(f"Request form: {request.form}")

        # Extract required data
        profile = request.form.get("profile")
        files = request.files.getlist("file")

        if not profile or not files:
            return jsonify(success=False, message="Profile and files are required."), 400

        if len(files) > 10:
            return jsonify(success=False, message="You can upload a maximum of 10 files."), 400

        creds = get_creds(profile)
        access_token = creds["access_token"]
        ig_user_id = creds["instagram_account_id"]

        # Create containers for each file
        children_ids = []
        for file in files:
            # Save file locally to generate a URL (assuming files are served from static/uploads)
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)

            # Upload to Vercel Blob Storage
            with open(file_path, 'rb') as f:
                blob_response = vercel_blob.put(filename, f.read())
                media_url = blob_response['url']

            # Determine media type
            media_type = "IMAGE" if file.content_type.startswith("image") else "VIDEO"

            # Create a container for the carousel item
            container_id = create_carousel_item(access_token, ig_user_id, media_url, media_type)
            children_ids.append(container_id)

        return jsonify(success=True, children_ids=children_ids)

    except Exception as e:
        logging.exception("Error uploading carousel items.")
        return jsonify(success=False, message=str(e)), 500


@media_bp.route("/publish_carousel", methods=["POST"])
def publish_carousel_route():
    """
    Handle publishing a carousel post.
    """
    try:
        # Parse request data
        data = request.json
        profile = data.get("profile")
        caption = data.get("caption", "")
        children_ids = data.get("children_ids")

        if not profile or not children_ids:
            return jsonify(success=False, message="Profile and children IDs are required."), 400

        creds = get_creds(profile)
        access_token = creds["access_token"]
        ig_user_id = creds["instagram_account_id"]

        # Create carousel container
        carousel_container_id = create_carousel_container(access_token, ig_user_id, children_ids, caption)

        # Publish the carousel
        media_id = publish_carousel(access_token, ig_user_id, carousel_container_id)

        return jsonify(success=True, media_id=media_id)

    except Exception as e:
        logging.exception("Error publishing carousel.")
        return jsonify(success=False, message=str(e)), 500
