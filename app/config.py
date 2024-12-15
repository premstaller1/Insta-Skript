import json

def get_creds(profile='productminimal'):
    """
    Retrieves API credentials based on the selected profile.
    :param profile: The profile name (e.g., 'productminimal' or 'productsdesign').
    :return: A dictionary containing credentials.
    """
    # Load credentials from the JSON file
    try:
        with open('data/metadata.json', 'r') as file:
            all_creds = json.load(file)
    except FileNotFoundError:
        raise FileNotFoundError("The metadata.json file was not found.")
    except json.JSONDecodeError:
        raise ValueError("The metadata.json file is not properly formatted.")

    # Retrieve credentials for the specified profile
    if profile in all_creds:
        creds = all_creds[profile]
        # Ensure all required keys are present
        required_keys = ['access_token', 'instagram_account_id', 'graph_domain', 'graph_version']
        missing_keys = [key for key in required_keys if key not in creds]
        if missing_keys:
            raise KeyError(f"The following keys are missing for profile '{profile}': {', '.join(missing_keys)}")
        return creds
    else:
        raise ValueError(f"Profile '{profile}' does not exist in the metadata.json file.")