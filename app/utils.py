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

def create_media_container(profile, image_url=None, caption="", is_carousel=False, children=None):
    """
    Create a media container for Instagram.
    
    :param profile: The profile name ('productminimal' or 'productsdesign').
    :param image_url: URL of the image to upload.
    :param caption: Caption for the media.
    :param is_carousel: Whether the media is part of a carousel.
    :param children: Child container IDs for a carousel.
    :return: Container ID.
    """
    creds = get_creds(profile)
    url = f"{creds['endpoint_base']}{creds['instagram_account_id']}/media"
    payload = {
        "access_token": creds["access_token"],
        "caption": caption
    }
    if is_carousel:
        payload["media_type"] = "CAROUSEL"
        payload["children"] = ",".join(children)
    elif image_url:
        payload["image_url"] = image_url
    else:
        raise ValueError("Either image_url or is_carousel with children must be provided.")

    response = requests.post(url, data=payload)
    if response.status_code != 200:
        logging.error(f"Error creating media container: {response.text}")
        raise Exception(f"Failed to create media container: {response.text}")
    return response.json().get("id")

def publish_media_container(profile, container_id):
    """
    Publish a media container to Instagram.
    
    :param profile: The profile name ('productminimal' or 'productsdesign').
    :param container_id: The container ID to publish.
    :return: Media ID.
    """
    creds = get_creds(profile)
    url = f"{creds['endpoint_base']}{creds['instagram_account_id']}/media_publish"
    payload = {
        "creation_id": container_id,
        "access_token": creds["access_token"]
    }
    response = requests.post(url, data=payload)
    if response.status_code != 200:
        logging.error(f"Error publishing media container: {response.text}")
        raise Exception(f"Failed to publish media: {response.text}")
    return response.json().get("id")
