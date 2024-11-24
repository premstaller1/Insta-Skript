import os
import requests
import logging
import shutil
import pandas as pd
from app.config import get_creds

def save_details_to_file(details_path, project_details):
    try:
        with open(details_path, 'w', encoding='utf-8') as file:
            for key, value in project_details.items():
                file.write(f"{key}: {value}\n")
    except Exception as e:
        logging.error(f"Error saving details to file {details_path}: {e}")

def download_images(project_dir, visuals_links, caption_info):
    """Helper function to download images and videos for a project."""
    BASE_URL = "http://127.0.0.1:5000"
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

###################################################################

# Function to create a media container for carousel items
def create_carousel_item(access_token, ig_user_id, media_url, media_type="IMAGE"):
    """
    Create a container for an image or video in a carousel.
    
    Parameters:
        access_token (str): Instagram access token.
        ig_user_id (str): Instagram user ID.
        media_url (str): URL of the media file (image or video).
        media_type (str): Type of media ("IMAGE" or "VIDEO").

    Returns:
        str: Media container ID.
    """
    url = f"https://graph.facebook.com/v21.0/{ig_user_id}/media"
    payload = {
        "access_token": access_token,
        "is_carousel_item": True,
    }

    if media_type == "IMAGE":
        payload["image_url"] = media_url
    elif media_type == "VIDEO":
        payload["media_type"] = "VIDEO"
        payload["video_url"] = media_url
    else:
        raise ValueError("Invalid media type. Only 'IMAGE' and 'VIDEO' are supported.")

    response = requests.post(url, data=payload)
    if response.status_code == 200:
        return response.json().get("id")
    else:
        logging.error(f"Error creating carousel item: {response.text}")
        raise Exception(f"Failed to create carousel item: {response.text}")


# Function to create the main carousel container
def create_carousel_container(access_token, ig_user_id, children_ids, caption=""):
    """
    Create a container for a carousel post.

    Parameters:
        access_token (str): Instagram access token.
        ig_user_id (str): Instagram user ID.
        children_ids (list): List of container IDs for carousel items.
        caption (str): Caption for the carousel post.

    Returns:
        str: Carousel container ID.
    """
    url = f"https://graph.facebook.com/v21.0/{ig_user_id}/media"
    payload = {
        "access_token": access_token,
        "media_type": "CAROUSEL",
        "children": ",".join(children_ids),
        "caption": caption,
    }

    response = requests.post(url, data=payload)
    if response.status_code == 200:
        return response.json().get("id")
    else:
        logging.error(f"Error creating carousel container: {response.text}")
        raise Exception(f"Failed to create carousel container: {response.text}")


# Function to publish the carousel post
def publish_carousel(access_token, ig_user_id, creation_id):
    """
    Publish a carousel post.

    Parameters:
        access_token (str): Instagram access token.
        ig_user_id (str): Instagram user ID.
        creation_id (str): Carousel container ID.

    Returns:
        str: Instagram media ID of the published carousel.
    """
    url = f"https://graph.facebook.com/v21.0/{ig_user_id}/media_publish"
    payload = {
        "access_token": access_token,
        "creation_id": creation_id,
    }

    response = requests.post(url, data=payload)
    if response.status_code == 200:
        return response.json().get("id")
    else:
        logging.error(f"Error publishing carousel: {response.text}")
        raise Exception(f"Failed to publish carousel: {response.text}")