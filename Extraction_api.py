import base64
import re
import requests
import streamlit as st
import json
import openai  # Added to use OpenAI Whisper
from datetime import datetime, timedelta
from datetime import datetime as dt
from openai import OpenAI

# Load secrets
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
ANDAKIA_API_KEY = st.secrets["ANDAKIA_API_KEY"]
API_URL = st.secrets["API_URL"]

# Initialize the OpenAI client (optionally, we can still use client below)
client = OpenAI(api_key=OPENAI_API_KEY)

# Also set OpenAI's API key for direct usage (for Whisper, etc.)
openai.api_key = OPENAI_API_KEY

# Function to encode the image in base64
def encode_image(image_file):
    image_file.seek(0)  # Reset file pointer to start
    return base64.b64encode(image_file.read()).decode("utf-8")

# Function to sanitize the message to remove any unwanted HTML tags
def sanitize_message(message):
    # Remove any HTML tags to avoid unwanted divs or other tags
    sanitized_message = re.sub(r"<.*?>", "", message)
    return sanitized_message

# Function to extract product information from an image
def extract_product_info(image_path):
    # Open the image file once and read into memory
    with open(image_path, "rb") as f:
        image_data = f.read()

    # Encode the image data to base64
    base64_image = base64.b64encode(image_data).decode("utf-8")

    # Expert-level prompt
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
                "- For start and end dates, carefully inspect the image for dates that might represent a production date, expiration date, promotion period, or validity window. "
                "Dates may be partially visible or formatted in various ways (dd/mm/yy, dd-mm-yy, mm/yy, etc.). "
                "Try to interpret and standardize them into 'jj-mm-aa' as best as you can.\n"
                "- If multiple potential dates are visible, choose the ones that most reasonably represent a start and end timeframe for the product (e.g., a promotional period or a product's valid shelf life). "
                "If no logical inference can be made, return null for those dates.\n"
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

    extracted_data = response.choices[0].message.content
    product_info = {
        "product_name": None,
        "company": None,
        "start_date": None,
        "end_date": None,
        "days_before_expire": None,
    }

    # Extract fields using regex
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

    # Calculate the days before expiration (end_date - start_date)
    if product_info["start_date"] and product_info["end_date"]:
        try:
            # Convert the dates from 'jj-mm-aa' to datetime
            start_date = dt.strptime(product_info["start_date"], "%d-%m-%y")
            end_date = dt.strptime(product_info["end_date"], "%d-%m-%y")
            
            # Calculate the difference in days between end_date and start_date
            delta = end_date - start_date
            product_info["days_before_expire"] = delta.days
        except ValueError:
            product_info["days_before_expire"] = None  # If date parsing fails

    return product_info

# The Andakia API transcription function (for Wolof)
def transcribe_audio_file(file_path):
    headers = {
        "Authorization": f"Bearer {ANDAKIA_API_KEY}",
    }

    with open(file_path, 'rb') as audio_file:
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

            if response.status_code == 200:
                return response_data.get('transcription', '')
            else:
                return f"Error: {response_data.get('error_message', 'Unknown error')}"
        except Exception as e:
            return f"Error: {str(e)}"

def clean_json_response(content):
    """
    Clean the GPT response to ensure it is valid JSON.
    """
    # Remove code block markers (```) or extra backticks
    content = content.strip().strip("`").strip()
    
    # Use regex to find the first valid JSON structure in the response
    match = re.search(r'\{.*\}', content, re.DOTALL)
    if match:
        return match.group(0)  # Return the matched JSON
    return "{}"  # Fallback to empty JSON if nothing found

def extract_products(text):
    # Calcul dynamique de la date actuelle
    today_str = datetime.now().strftime("%Y-%m-%d")
    
    # Prompt amélioré
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
- Identifiez toute date ou période de paiement mentionnée dans le texte, qu'elle soit absolue (par ex. "15 janvier 2024") ou relative (par ex. "dans deux semaines", "le mois prochain", ou "vendredi prochain"). 
  - Convertissez cette information en une date exacte au format YYYY-MM-DD en vous basant sur la date du jour ({today_str}).
  - Si aucune date n'est trouvée, retournez "None".
- "quantity" doit être un nombre si trouvé, sinon "None".
- "price" doit être un nombre si trouvé, sinon "None".
- Le JSON doit strictement respecter ce format (n'ajoutez ni ne retirez aucune clé, à l'exception de "person_name" déjà demandée).
- Si plusieurs dates sont mentionnées, choisissez celle qui semble le plus logiquement liée au paiement.
- Soyez créatif dans l'interprétation des dates implicites ou relatives, mais conservez un format rigoureux.

IMPORTANT : Ne retournez rien d'autre que la structure JSON demandée.
'''

    # API Call à GPT-4o ou GPT-4
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0,
        max_tokens=500
    )

    # Récupération du contenu brut
    content = response.choices[0].message.content.strip()

    # Nettoyage avant parsing
    cleaned_content = clean_json_response(content)

    try:
        # Conversion en dictionnaire Python
        result = json.loads(cleaned_content)
    except json.JSONDecodeError:
        # En cas d'erreur de parsing JSON, on renvoie une structure par défaut
        result = {
            "person_name": None,
            "products": []
        }

    return result

# ------------------------------------------------------------------------------
# NEW FUNCTIONS ADDED FOR AUTO-DETECTION & TRANSCRIPTION WITH OPENAI WHISPER
# ------------------------------------------------------------------------------

def detect_language_openai(file_path):
    """
    Detect language and transcribe using OpenAI Whisper API.
    Returns a tuple (language_code, text).
    Example: ("fr", "Transcribed text...")
    """
    with open(file_path, "rb") as audio_file:
        # Let Whisper auto-detect language
        response = openai.Audio.transcribe(
            model="whisper-1",
            file=audio_file,
            language=None  # None => auto-detect
        )
    # 'language' might be "en", "fr", "ar", ...
    language_code = response.get("language", "")
    text = response.get("text", "")
    return language_code, text

def transcribe_audio_with_condition(file_path):
    """
    1. Use OpenAI Whisper to detect language & do a first transcription.
    2. If language is Wolof => use Andakia's API for final transcription.
    3. If language is Arabic (ar), French (fr), English (en) => use Whisper text.
    4. Then extract product information from the final transcription.
    """
    detected_language, openai_transcription = detect_language_openai(file_path)

    # Decide which transcription to keep based on detected_language
    if detected_language.lower() in ["wo", "wolof"]:
        # Wolof => use Andakia
        final_text = transcribe_audio_file(file_path)
    elif detected_language.lower() in ["ar", "fr", "en"]:
        # Arabic, French, or English => use OpenAI Whisper transcription
        final_text = openai_transcription
    else:
        # Fallback for any other language not handled
        final_text = (
            f"Language detected: {detected_language}. "
            "Currently not supported by this pipeline."
        )

    # Now we can extract products (or any other structured info) from final_text
    structured_data = extract_products(final_text)

    return {
        "detected_language": detected_language,
        "transcription": final_text,
        "structured_data": structured_data
    }
