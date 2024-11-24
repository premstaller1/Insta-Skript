import os
import pandas as pd
import requests
from archive.langchain import generate_caption

def sanitize_filename(filename):
    # Define invalid characters
    invalid_chars = '<>:"/\\|?*'
    # Replace each invalid character with an underscore
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename