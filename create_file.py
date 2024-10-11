import os
import pandas as pd
import requests
from main import generate_caption

print("Loading data...")
df = pd.read_csv('data/submissions/Submission.csv')
# Base directory where projects will be stored
output_base_dir = 'data/newpost'
# Create the base directory if it doesn't exist
os.makedirs(output_base_dir, exist_ok=True)

def sanitize_filename(filename):
    # Define invalid characters
    invalid_chars = '<>:"/\\|?*'
    # Replace each invalid character with an underscore
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename
print("Processing data...")
# Iterate over each row in the CSV file
for index, row in df.iterrows():
    project_name = row['Project Name']
    description = row['Project Description']
    designer = row["Instagram @"]
    visuals_links = row['Upload your Visuals (max. 10!)']
    support = row["Support Frabiché"]
    company = row["Company Name"]
    
    # Sanitize the project name
    sanitized_project_name = sanitize_filename(project_name)

    #transform instagram @ from a link to a username
    if pd.notna(designer):
        if 'instagram.com' in designer:
            print(designer)
            designer = designer.split('/')[3]
            print(designer)
            #add @ to the username
            designer = '@' + designer
        elif '@' in designer:
            pass
        else:
            designer = '@' + designer

    caption = generate_caption(project_name, description, designer)
    
    # Create a directory for each project and name it using the project name and index
    project_dir = os.path.join(output_base_dir, f"{sanitized_project_name}_{index+1}")
    os.makedirs(project_dir, exist_ok=True)
    
    # Save project name and description in a text file
    with open(os.path.join(project_dir, 'details.txt'), 'w', encoding='utf-8') as file:
        file.write(f"Project Name: {project_name}\n")
        file.write(f"Description: {description}\n")
        file.write(f"Designer: {designer}\n")
        file.write(f"Company: {company}\n")
        file.write(f"Support: {support}\n")
        file.write(f"Caption: {caption}\n")
    
    # Download images
    if pd.notna(visuals_links):
        urls = visuals_links.split(';')  # Split URLs by semicolon
        for i, url in enumerate(urls):
            url = url.strip()
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    with open(os.path.join(project_dir, f'image_{i+1}.jpg'), 'wb') as img_file:
                        img_file.write(response.content)
                else:
                    print(f"Failed to download image from {url}")
            except Exception as e:
                print(f"Error downloading image from {url}: {e}")

print("Script completed successfully.")