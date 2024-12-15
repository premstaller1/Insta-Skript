import vercel_blob
import os
import datetime

# List all files in Blob Storage
def list_blobs(limit=5):
    try:
        return vercel_blob.list({'limit': str(limit)})
    except Exception as e:
        raise Exception(f"Error listing blobs: {str(e)}")

# Upload a file to Blob Storage
def upload_blob(file, folder='upload'):
    try:
        file_data = file.read()

        # Check if the file is a .csv
        if file.filename.endswith('.csv'):
            # Generate a timestamp for the file name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{os.path.splitext(file.filename)[0]}_{timestamp}{os.path.splitext(file.filename)[1]}"
            folder = 'archives'  # Change folder to archives for .csv files
        else:
            filename = file.filename

        # Upload to the specified folder
        response = vercel_blob.put(f'{folder}/{filename}', file_data)
        return response
    except Exception as e:
        raise Exception(f"Error uploading blob: {str(e)}")

# Delete a blob from Blob Storage
def delete_blob(blob_url):
    try:
        response = vercel_blob.delete([blob_url])
        return {'message': 'Blob deleted successfully'}
    except Exception as e:
        raise Exception(f"Error deleting blob: {str(e)}")

# Get blob metadata
def get_blob_metadata(blob_url):
    try:
        metadata = vercel_blob.head(blob_url)
        return metadata
    except Exception as e:
        raise Exception(f"Error fetching metadata: {str(e)}")

# Copy a blob to another folder
def copy_blob(source_url, destination_path):
    try:
        response = vercel_blob.copy(source_url, destination_path)
        return response
    except Exception as e:
        raise Exception(f"Error copying blob: {str(e)}")
