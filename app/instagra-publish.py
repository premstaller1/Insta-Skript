import requests

BASE_URL = "https://graph.facebook.com/v21.0"

def create_media_container(access_token, ig_user_id, image_url, caption):
    url = f"{BASE_URL}/{ig_user_id}/media"
    payload = {
        "image_url": image_url,
        "caption": caption,
        "access_token": access_token
    }
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        return response.json().get("id")
    else:
        raise Exception(f"Failed to create media container: {response.text}")

def publish_media_container(access_token, ig_user_id, container_id):
    url = f"{BASE_URL}/{ig_user_id}/media_publish"
    payload = {
        "creation_id": container_id,
        "access_token": access_token
    }
    response = requests.post(url, data=payload)
    if response.status_code == 200:
        return response.json().get("id")
    else:
        raise Exception(f"Failed to publish media: {response.text}")
