import base64
import re
import requests
import streamlit as st
import json
from datetime import datetime, timedelta

# Import the OpenAI client from your installed openai module
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

# Function to sanitize the message by removing any unwanted HTML tags
def sanitize_message(message):
    sanitized_message = re.sub(r"<.*?>", "", message)
    return sanitized_message

# Function to extract product information from an image and return JSON with null values
def extract_image_product_info(image_path):
    # Read the image file once into memory
    with open(image_path, "rb") as f:
        image_data = f.read()

    # Encode the image data in base64
    base64_image = base64.b64encode(image_data).decode("utf-8")

    # Expert-level prompt to extract product details
    prompt = [
        {
            "type": "text",
            "text": (
                "You are an expert at extracting structured information from images. "
                "You are given an image that may contain a product (like a packaged good, a poster, a label, etc.). "
                "Your task is to extract the following information and return it as a Python dictionary with the exact keys: "
                "\"product_name\", \"company\", \"start_date\", and \"end_date\".\n\n"
                "Requirements:\n"
                "- If any piece of information is not present or cannot be deduced, return null for that field.\n"
                "- The dates should be returned in the format 'jj-mm-aa' (day-month-year). For example, '01-09-24' would represent 1 September 2024.\n"
                "- If the product name or company name is unclear, do your best to infer it from logos, text fragments, or any textual clues.\n"
                "- For start and end dates, carefully inspect the image for dates that might represent a production date, expiration date, "
                "promotion period, or validity window. Dates may be partially visible or formatted in various ways (dd/mm/yy, dd-mm-yy, mm/yy, etc.). "
                "Try to interpret and standardize them into 'jj-mm-aa' as best as you can.\n"
                "- If multiple potential dates are visible, choose the ones that most reasonably represent a start and end timeframe for the product "
                "(e.g., a promotional period or a product's valid shelf life). If no logical inference can be made, return null for those dates.\n"
                "- Use advanced reasoning and be creative in interpreting unclear or incomplete clues. Consider language nuances, brand hints, or numeric sequences that could represent dates.\n"
                "- Always return strictly a single Python dictionary in the following format:\n\n"
                "{\n"
                "  \"product_name\": \"...\" or null,\n"
                "  \"company\": \"...\" or null,\n"
                "  \"start_date\": \"jj-mm-aa\" or null,\n"
                "  \"end_date\": \"jj-mm-aa\" or null\n"
                "}\n"
            ),
        },
        {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}",
            },
        }
    ]

    # Make the API call
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )

    # Retrieve the raw string response from the model
    extracted_data = response.choices[0].message.content

    # Initialize the product info with None for missing values (will become null in JSON)
    product_info = {
        "product_name": None,
        "company": None,
        "start_date": None,
        "end_date": None,
        "days_before_expire": None,
    }

    # Regex patterns for extracting fields
    patterns = {
        "product_name": r'"product_name":\s*"([^"]+)"',
        "company": r'"company":\s*"([^"]+)"',
        "start_date": r'"start_date":\s*"([^"]+)"',
        "end_date": r'"end_date":\s*"([^"]+)"',
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, extracted_data)
        if match:
            product_info[key] = match.group(1)
        else:
            product_info[key] = None  # Explicitly mark missing data as None

    # Calculate days_before_expire if both dates are available
    if product_info["start_date"] and product_info["end_date"]:
        try:
            start_date = datetime.strptime(product_info["start_date"], "%d-%m-%y")
            end_date = datetime.strptime(product_info["end_date"], "%d-%m-%y")
            delta = end_date - start_date
            product_info["days_before_expire"] = delta.days
        except ValueError:
            product_info["days_before_expire"] = None

    # Convert the result to a JSON string so that None appears as null
    return json.dumps(product_info, ensure_ascii=False, indent=2)

# Function to transcribe an audio file and return transcription text
def transcribe_audio_file(file_path):
    headers = {
        "Authorization": f"Bearer {ANDAKIA_API_KEY}",
    }
    
    with open(file_path, 'rb') as audio_file:
        files = {'incoming_file': audio_file}
        data = {
            'sample_rate': 16000,
            'tempo_factor': 1.0,
            'target_language': 'fr',
        }
        try:
            response = requests.post(API_URL, headers=headers, files=files, data=data)
            response_data = response.json()
            if response.status_code == 200:
                return response_data.get('transcription', '')
            else:
                return f"Error: {response_data.get('error_message', 'Unknown error')}"
        except Exception as e:
            return f"Error: {str(e)}"

# Clean the GPT response to ensure valid JSON (remove extra markers)
def clean_json_response(content):
    content = content.strip().strip("`").strip()
    match = re.search(r'\{.*\}', content, re.DOTALL)
    if match:
        return match.group(0)
    return "{}"

# Function to extract product details from transcribed text and return JSON with null values
def extract_products(text):
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    prompt = f'''
Le texte suivant est en français: "{text}"

Nous sommes le {today_str}. Veuillez :

1. Extraire le nom de la personne mentionnée dans le texte (par exemple "M. Dupont", "Alice", "Jean Martin", "Madame Sakho", etc.).  
   - Incluez les titres honorifiques (par exemple, "Madame", "Monsieur") si mentionnés dans le texte.
   - S'il n'y a pas de nom explicite, retournez "None".

2. Extraire les informations sur les produits et retourner STRICTEMENT le format JSON suivant :

{{
  "person_name": "Nom de la personne ou None",
  "products": [
    {{
      "product_name": "Nom du produit",
      "quantity": "Nombre ou None",
      "price": "Prix ou None",
      "transaction_type": "vente ou achat",
      "payment_date": "Date de paiement au format YYYY-MM-DD ou None"
    }}
  ]
}}

Contraintes supplémentaires :
- N'incluez aucun texte supplémentaire comme des traductions ou des introductions dans la réponse.
- "transaction_type" doit être "vente" ou "achat" selon ce qui est trouvé dans le texte.
- Identifiez toute date ou période de paiement mentionnée dans le texte, qu'elle soit absolue (ex : "15 janvier 2024") ou relative (ex : "dans deux semaines", "le mois prochain", ou "vendredi prochain"). 
  - Convertissez cette information en une date exacte au format YYYY-MM-DD en vous basant sur la date du jour ({today_str}).
  - Si aucune date n'est trouvée, retournez "None".
- "quantity" doit être un nombre si trouvé, sinon "None".
- "price" doit être un nombre si trouvé, sinon "None".
- Le JSON doit STRICTEMENT respecter ce format (n'ajoutez ni ne retirez aucune clé).
- Si plusieurs dates sont mentionnées, choisissez celle qui semble la plus logiquement liée au paiement.
- Soyez créatif dans l'interprétation des dates implicites ou relatives, mais conservez un format rigoureux.

IMPORTANT : Ne retournez rien d'autre que la structure JSON demandée.
'''

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=500
    )

    content = response.choices[0].message.content.strip()
    cleaned_content = clean_json_response(content)

    try:
        result = json.loads(cleaned_content)
    except json.JSONDecodeError:
        result = {
            "person_name": None,
            "products": []
        }

    # Ensure missing fields are set as None
    if "person_name" not in result or not result["person_name"]:
        result["person_name"] = None

    if "products" not in result or not isinstance(result["products"], list):
        result["products"] = []
    else:
        for product in result["products"]:
            product.setdefault("product_name", None)
            product.setdefault("quantity", None)
            product.setdefault("price", None)
            product.setdefault("transaction_type", None)
            product.setdefault("payment_date", None)

    # Return as a JSON string to have null values (instead of Python's None)
    return json.dumps(result, ensure_ascii=False, indent=2)
