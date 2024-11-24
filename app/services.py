from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessage
from app.config import get_creds
import requests
import os

def generate_caption(project_name, description, designer):
    """
    Generates an Instagram caption using an AI model.
    
    Args:
        project_name (str): The name of the project.
        description (str): A description of the project.
        designer (str): The designer's Instagram handle.
    
    Returns:
        str: The generated Instagram caption.
    """
    print("Generating caption...")
    llm = ChatOllama(
        model="llama3.1",
        temperature=1
    )
    # Define the input messages
    print("Model loaded...")
    messages = [
        (
            "system", 
            "You are a skilled Social Media Manager crafting Instagram captions for a design-focused account. "
            "For each post, you will receive details about the project, including the designer, project name, and a description. "
            "Your task is to write a well-structured and engaging caption in the third person that: "
            "(1) opens with a clever wordplay or hook related to the design, "
            "(2) mentions the designer’s Instagram handle (e.g., '@designer_handle') once, "
            "(3) accurately describes the project’s core elements, and "
            "(4) avoids excessive adjectives, keeping the tone objective and descriptive. "
            "Keep each part direct and relevant to the project. End with 3–5 relevant hashtags that suit the project’s aesthetic and focus. "
            "Avoid adding any placeholder text or additional comments."
        ),
        ("human", f"This is {project_name} by {designer}. {description}"),
    ]
    
    # Pass the messages to the AI model
    print("Passing messages to the model...")
    ai_msg = llm.invoke(messages)
    print("Caption generated...")
    
    # Return the caption
    caption = ai_msg.content
    return caption


def sanitize_filename(filename):
    """
    Sanitizes a filename by replacing invalid characters with underscores.
    
    Args:
        filename (str): The original filename.
    
    Returns:
        str: The sanitized filename.
    """
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename
