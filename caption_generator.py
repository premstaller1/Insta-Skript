import torch
import os
import pandas as pd
import requests
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from huggingface_hub import login

# Login to Hugging Face Hub
login(token="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")

def sanitize_filename(filename):
    """Sanitize the filename by replacing invalid characters with underscores."""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename

def load_model():
    """Load the text-generation pipeline from Hugging Face."""
    try:
        model = AutoModelForCausalLM.from_pretrained(
            "microsoft/Phi-3-mini-4k-instruct",
            device_map="cuda",  # Set to CUDA for GPU acceleration
            torch_dtype="auto",
            trust_remote_code=True,
        )
        tokenizer = AutoTokenizer.from_pretrained("microsoft/Phi-3-mini-4k-instruct")
        pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
        )
    except Exception as e:
        print(f"Error loading model: {e}")
        raise e
    return pipe

def generate_caption(instagram_handle, description, pipe):
    """Generate a caption for an Instagram post."""
    try:
        prompt = f"Create a social media caption for an Instagram post. Designer: {instagram_handle}, Description: {description}"
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": prompt}
        ]
        generation_args = {
            "max_new_tokens": 256,
            "return_full_text": False,
            "temperature": 0.5,  # Adjusted for more creative outputs
            "do_sample": True,
        }
        outputs = pipe(messages, **generation_args)
        caption = outputs[0]["generated_text"].strip()
    except Exception as e:
        print(f"Error generating caption: {e}")
        caption = "Error generating caption."
    return caption

def main():
    """Main function to process CSV and generate captions."""
    try:
        # Load the text-generation pipeline
        pipe = load_model()

        # Load your CSV file into a DataFrame
        df = pd.read_csv('submission/Submission.csv')

        # Base directory where projects will be stored
        output_base_dir = 'data/test'
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

            # Create a directory for each project
            project_dir = os.path.join(output_base_dir, f"{sanitized_project_name}_{index+1}")
            os.makedirs(project_dir, exist_ok=True)

            # Generate caption using the text-generation pipeline
            caption = generate_caption(designer, description, pipe)

            # Save project details and caption in a text file
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

    except Exception as e:
        print(f"An error occurred: {e}")
        # Clear CUDA cache to free up memory in case of an error
        torch.cuda.empty_cache()

if __name__ == "__main__":
    main()
