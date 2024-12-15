from flask import Flask, render_template
from routes import list_blobs_route, upload_blob_route, delete_blob_route, get_blob_metadata_route, copy_blob_route

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

# Define routes using imported functions from routes.py
app.add_url_rule('/list_blobs', view_func=list_blobs_route, methods=['GET'])
app.add_url_rule('/upload_blob', view_func=upload_blob_route, methods=['POST'])
app.add_url_rule('/delete_blob', view_func=delete_blob_route, methods=['DELETE'])
app.add_url_rule('/blob_metadata', view_func=get_blob_metadata_route, methods=['GET'])
app.add_url_rule('/copy_blob', view_func=copy_blob_route, methods=['POST'])

if __name__ == '__main__':
    app.run(debug=True)
