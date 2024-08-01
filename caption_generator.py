import torch
import os
import pandas as pd
import requests
from transformers import AutoModelForCausalLM, AutoTokenizer

def sanitize_filename(filename):
    # Define invalid characters
    invalid_chars = '<>:"/\\|?*'
    # Replace each invalid character with an underscore
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename

def load_model():
    model = AutoModelForCausalLM.from_pretrained(
        "mistralai/Mistral-7B-v0.1", device_map="auto", load_in_4bit=True
    )
    tokenizer = AutoTokenizer.from_pretrained("mistralai/Mistral-7B-v0.1", padding_side="left")
    tokenizer.pad_token = tokenizer.eos_token  # Set pad token
    return model, tokenizer

def generate_caption(instagram_handle, description, model, tokenizer):
    prompt = f"Create a social media caption for an Instagram post. Designer: {instagram_handle}, Description: {description}"
    model_inputs = tokenizer([prompt], return_tensors="pt", padding=True).to("cuda")
    generated_ids = model.generate(**model_inputs)
    caption = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
    return caption

# Load the model and tokenizer
model, tokenizer = load_model()

# Load your CSV file into a DataFrame (assuming df is your DataFrame)
# df = pd.read_csv('your_csv_file.csv') # Uncomment and update the file path as needed

# Base directory where projects will be stored
df = pd.read_csv('submission/Submission.csv')
output_base_dir = 'data/posts'

# Create the base directory if it doesn't exist
os.makedirs(output_base_dir, exist_ok=True)

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
    
    # Create a directory for each project and name it using the project name and index
    project_dir = os.path.join(output_base_dir, f"{sanitized_project_name}_{index+1}")
    os.makedirs(project_dir, exist_ok=True)
    
    # Generate caption using the transformer model
    caption = generate_caption(designer, description, model, tokenizer)
    
    # Save project name, description, and caption in a text file
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