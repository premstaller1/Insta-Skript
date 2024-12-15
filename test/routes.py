from flask import request, jsonify
from blob_operations import list_blobs, upload_blob, delete_blob, get_blob_metadata, copy_blob

# List all files in Blob Storage
def list_blobs_route():
    try:
        blobs = list_blobs()
        return jsonify(blobs)
    except Exception as e:
        return str(e), 500

# Upload a file to Blob Storage
def upload_blob_route():
    try:
        file = request.files['file']
        response = upload_blob(file)
        return jsonify(response), 201
    except Exception as e:
        return str(e), 500

# Delete a blob from Blob Storage
def delete_blob_route():
    try:
        blob_url = request.json.get('url')
        if not blob_url:
            return 'No URL provided', 400
        response = delete_blob(blob_url)
        return jsonify(response), 200
    except Exception as e:
        return str(e), 500

# Get blob metadata
def get_blob_metadata_route():
    try:
        blob_url = request.args.get('url')
        if not blob_url:
            return 'No URL provided', 400
        metadata = get_blob_metadata(blob_url)
        return jsonify(metadata), 200
    except Exception as e:
        return str(e), 500

# Copy a blob to another folder
def copy_blob_route():
    try:
        source_url = request.json.get('source_url')
        destination_path = request.json.get('destination_path')
        if not source_url or not destination_path:
            return 'Source URL or destination path missing', 400
        response = copy_blob(source_url, destination_path)
        return jsonify(response), 200
    except Exception as e:
        return str(e), 500
