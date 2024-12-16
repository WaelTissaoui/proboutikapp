import streamlit as st
import base64
import tempfile
from Extraction_api import extract_product_info, sanitize_message, transcribe_audio_file, extract_products

def custom_css():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');
        @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css');

        body {
            font-family: 'Roboto', sans-serif;
            background: #f1f3f5;
            color: #333;
        }

        /* Layout Tweaks */
        .main, .stApp {
            padding: 20px;
        }

        /* Sidebar Styling */
        .css-1cypcdb {
            background: #ffffff;
            border-right: 1px solid #eee;
            padding: 20px;
        }

        .app-title {
            font-size: 1.6em;
            font-weight: 700;
            margin-bottom: 30px;
            color: #2c3e50;
            text-align: center;
        }

        /* Cards (Mode Selection Buttons) */
        .cards-container {
            display: flex;
            flex-direction: column;
            gap: 20px;
            align-items: center;
        }

        .stButton > button {
            background: #ffffff;
            border-radius: 8px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.05);
            width: 250px;
            height: 120px;
            cursor: pointer;
            font-size: 1em;
            font-weight: 500;
            color: #2c3e50;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            border: none;
            transition: transform 0.2s, box-shadow 0.2s;
        }

        .stButton > button:hover {
            transform: translateY(-5px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }

        /* Titles and Headings */
        h1.main-title {
            font-weight: 700;
            color: #2c3e50;
            font-size: 2.2em;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        h1.main-title i {
            font-size: 1.3em;
        }

        .section-subtitle {
            font-size: 1.1em;
            color: #555;
            margin-bottom: 30px;
        }

        h3.history-title {
            font-size: 1.3em;
            border-bottom: 2px solid #eee;
            padding-bottom: 10px;
            color: #2c3e50;
            margin-top: 40px;
            font-weight: 600;
        }

        /* Chat Container */
        .chat-container {
            max-width: 600px;
            margin: 0 auto;
        }

        /* Chat message bubbles */
        .chat-bubble {
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            line-height: 1.4;
            font-size: 15px;
            max-width: 80%;
            word-wrap: break-word;
            position: relative;
        }

        .chat-bubble.user {
            background: #d9ecff;
            margin-left: auto;
            text-align: left;
            border: 1px solid #c6ddf7;
        }

        .chat-bubble.system {
            background: #ffffff;
            margin-right: auto;
            text-align: left;
            border: 1px solid #eaeaea;
        }

        /* Chat images */
        .chat-image {
            max-width: 120px;
            border-radius: 8px;
            display: block;
            margin-bottom: 10px;
            border: 1px solid #ddd;
        }

        /* Info Cards */
        .info-card {
            background: #fefefe;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
            font-size: 15px;
        }

        .info-card strong {
            color: #2c3e50;
        }

        /* File Uploaders */
        .stFileUploader, .stCameraInput, .stAudioInput {
            border: 2px dashed #ccc;
            border-radius: 6px;
            padding: 20px;
            margin-bottom: 20px;
            text-align: center;
            background: #fafafa;
        }

        /* Make the file uploader area smaller and cleaner */
        .stFileUploader > div, .stCameraInput > div {
            width: 100%;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )

def main():
    custom_css()

    if "image_chat_history" not in st.session_state:
        st.session_state.image_chat_history = []
    if "audio_chat_history" not in st.session_state:
        st.session_state.audio_chat_history = []
    if "app_mode" not in st.session_state:
        st.session_state.app_mode = "image_extraction"

    with st.sidebar:
        st.markdown("<h2 class='app-title'>PROBOUTIK APP</h2>", unsafe_allow_html=True)
        st.markdown('<div class="cards-container">', unsafe_allow_html=True)

        if st.button("🖼️ Image Extraction"):
            st.session_state.app_mode = "image_extraction"

        if st.button("🎤 Speech to Text"):
            st.session_state.app_mode = "speech_to_text"

        st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.app_mode == "image_extraction":
        image_extraction_chat()
    else:
        speech_extraction()

def image_extraction_chat():
    st.markdown("<h1 class='main-title'><i class='fa fa-image'></i> Image-Based Product Information</h1>", unsafe_allow_html=True)
    st.markdown("<p class='section-subtitle'>Upload or capture an image and we’ll extract the key product details for you!</p>", unsafe_allow_html=True)

    uploaded_image = st.file_uploader("Upload an image...", type=["jpg", "jpeg", "png"])
    camera_image = st.camera_input("Take a picture")

    if camera_image is not None:
        image_name = "Captured Image"
        if image_name != st.session_state.get("last_processed_input_image"):
            process_image(camera_image, image_name)
            st.session_state.last_processed_input_image = image_name

    elif uploaded_image is not None:
        image_name = uploaded_image.name
        if image_name != st.session_state.get("last_processed_input_image"):
            process_image(uploaded_image, image_name)
            st.session_state.last_processed_input_image = image_name

    display_image_chat_history()

def process_image(image_file, image_name):
    base64_image = base64.b64encode(image_file.getvalue()).decode("utf-8")
    st.session_state.image_chat_history.append({
        "role": "user",
        "image": base64_image,
        "name": image_name
    })

    with st.spinner("Processing image..."):
        product_info = extract_product_info(image_file)

    # Build a nice HTML response
    formatted_message = f"""
    <div class="info-card">
        <strong>Extracted Information:</strong>
        <ul>
            <li><strong>Product Name:</strong> {product_info.get('product_name', 'N/A')}</li>
            <li><strong>Company:</strong> {product_info.get('company', 'N/A')}</li>
            <li><strong>Start Date:</strong> {product_info.get('start_date', 'N/A')}</li>
            <li><strong>End Date:</strong> {product_info.get('end_date', 'N/A')}</li>
        </ul>
    </div>
    """

    st.session_state.image_chat_history.append({
        "role": "system",
        "message": sanitize_message(formatted_message)
    })

def display_image_chat_history():
    if st.session_state.image_chat_history:
        st.markdown("<h3 class='history-title'>Chat History</h3>", unsafe_allow_html=True)
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        for chat in st.session_state.image_chat_history:
            if chat["role"] == "user":
                if "image" in chat:
                    st.markdown(f"""
                    <div class="chat-bubble user">
                        <img class="chat-image" src="data:image/png;base64,{chat['image']}" alt="{chat['name']}"/>
                        <strong>You uploaded:</strong> {chat['name']}
                    </div>
                    """, unsafe_allow_html=True)
            elif chat["role"] == "system":
                st.markdown(f"""
                <div class="chat-bubble system">
                    {chat["message"]}
                
                """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

def speech_extraction():
    st.markdown("<h1 class='main-title'><i class='fa fa-microphone'></i> Speech-Based Product Information</h1>", unsafe_allow_html=True)
    st.markdown("<p class='section-subtitle'>Upload or record an audio file and we’ll transcribe the spoken product details for you!</p>", unsafe_allow_html=True)

    uploaded_audio = st.file_uploader("Upload an audio file...", type=["wav", "mp3"])
    recorded_audio = st.audio_input("Record audio")

    if recorded_audio is not None:
        audio_name = "Recorded Audio"
        if audio_name != st.session_state.get("last_processed_input_audio"):
            process_audio(recorded_audio, audio_name)
            st.session_state.last_processed_input_audio = audio_name

    elif uploaded_audio is not None:
        audio_name = uploaded_audio.name
        if audio_name != st.session_state.get("last_processed_input_audio"):
            process_audio(uploaded_audio, audio_name)
            st.session_state.last_processed_input_audio = audio_name

    display_audio_chat_history()

def process_audio(audio_file, audio_name):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
        temp_audio_file.write(audio_file.getvalue())
        temp_audio_path = temp_audio_file.name

    with st.spinner("Transcribing audio..."):
        transcription = transcribe_audio_file(temp_audio_path)

    # Extract product information from the transcription
    product_data = extract_products(transcription)
    print(product_data)
    # Build a prettier HTML layout for the extracted products
    product_list_html = ""
    if isinstance(product_data, dict) and "products" in product_data:
        for product in product_data["products"]:
            product_name = product.get("product_name", "N/A")
            quantity = product.get("quantity", "N/A")
            price = product.get("price", "N/A")
            product_list_html += f"""
            <ul>
                <li><strong>Product Name:</strong> {product_name}</li>
                <li><strong>Quantity:</strong> {quantity}</li>
                <li><strong>Price:</strong> {price}</li>
            </ul>
            """

    formatted_message = f"""
    <div class="info-card">
        <strong>File:</strong> {audio_name}<br><br>
        <strong>Transcription:</strong><br>
        <div>{transcription}</div><br><br>
        <strong>Extracted Product Information:</strong><br>
        <div>{product_list_html}</div>
    </div>
    """

    st.session_state.audio_chat_history.append({
        "role": "system",
        "message": formatted_message
    })

def display_audio_chat_history():
    if st.session_state.audio_chat_history:
        st.markdown("<h3 class='history-title'>Chat History</h3>", unsafe_allow_html=True)
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        for chat in st.session_state.audio_chat_history:
            if chat["role"] == "system":
                st.markdown(f"""
                <div class="chat-bubble system">
                    {chat["message"]}
                
                """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
