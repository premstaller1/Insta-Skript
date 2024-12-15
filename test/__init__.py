import vercel_blob
from flask import Flask, request, render_template, redirect
import dotenv
import os

# Initialize Flask app
app = Flask(__name__)

# Load environment variables from .env file
dotenv.load_dotenv()

# Ensure the BLOB_READ_WRITE_TOKEN is in the environment
BLOB_TOKEN = os.getenv('BLOB_READ_WRITE_TOKEN')
if not BLOB_TOKEN:
    raise ValueError("BLOB_READ_WRITE_TOKEN not set in .env file")

# Initialize vercel_blob with the token
vercel_blob.set_token(BLOB_TOKEN)

@app.route('/')
def index():
    # List all blobs in storage
    blobs = vercel_blob.list().get('blobs', [])
    return render_template('index.html', files=blobs)

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    # Upload the file to Vercel Blob Storage
    vercel_blob.put(file.filename, file.read())
    return redirect('/')

@app.route('/delete', methods=['GET'])
def delete():
    file_url = request.args.get('url')
    # Delete the file from Vercel Blob Storage
    vercel_blob.delete(file_url)
    return redirect('/')

@app.route('/download', methods=['GET'])
def download():
    file_url = request.args.get('url')
    # Retrieve download URL and redirect to it
    download_url = vercel_blob.head(file_url).get('downloadUrl')
    return redirect(download_url)

if __name__ == '__main__':
    app.run(debug=True)
