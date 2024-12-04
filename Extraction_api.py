import base64
import re
import requests
import streamlit as st
from openai import OpenAI

# Load secrets
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
ANDAKIA_API_KEY = st.secrets["ANDAKIA_API_KEY"]
API_URL = st.secrets["API_URL"]

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Function to encode the image in base64
def encode_image(image_file):
    image_file.seek(0)  # Reset file pointer to start
    return base64.b64encode(image_file.read()).decode("utf-8")

# Function to sanitize the message to remove any unwanted HTML tags
def sanitize_message(message):
    # Remove any HTML tags to avoid unwanted divs or other tags
    sanitized_message = re.sub(r"<.*?>", "", message)
    return sanitized_message

# Function to extract product information
def extract_product_info(image_file):
    base64_image = encode_image(image_file)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Extract me the name of the product if it exists and the company and the start date and the end date of the product. Make them into a Python dictionary. If it does not exist, put null. Do your best in the start and end dates because they might not be very clear. Make the dates in the same format 'jj-mm-aa' and do your best to get them correct. Use some image processing methods.",
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                        },
                    },
                ],
            }
        ],
    )

    extracted_data = response.choices[0].message.content
    product_info = {
        "product_name": None,
        "company": None,
        "start_date": None,
        "end_date": None,
    }

    # Regex patterns to capture each field
    patterns = {
        "product_name": r'"product_name":\s*"([^"]+)"',
        "company": r'"company":\s*"([^"]+)"',
        "start_date": r'"start_date":\s*"([^"]+)"',
        "end_date": r'"end_date":\s*"([^"]+)"',
    }

    # Apply each pattern to the extracted_data string
    for key, pattern in patterns.items():
        match = re.search(pattern, extracted_data)
        if match:
            product_info[key] = match.group(1)

    return product_info

# Function to transcribe a single audio file
def transcribe_audio_file(file_path):
    headers = {
        "Authorization": f"Bearer {ANDAKIA_API_KEY}",
    }

    # Open the file to include it in the form data
    with open(file_path, 'rb') as audio_file:
        # Form the payload for multipart/form-data
        files = {
            'incoming_file': audio_file,
        }
        data = {
            'sample_rate': 16000,
            'tempo_factor': 1.0,
            'target_language': 'fr',
        }

        try:
            response = requests.post(API_URL, headers=headers, files=files, data=data)
            response_data = response.json()

            # Extract transcription from the response
            if response.status_code == 200:
                return response_data.get('transcription', '')
            else:
                return f"Error: {response_data.get('error_message', 'Unknown error')}"

        except Exception as e:
            return f"Error: {str(e)}"
