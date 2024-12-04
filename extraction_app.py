import streamlit as st
import base64
import tempfile
from Extraction_api import extract_product_info, sanitize_message, transcribe_audio_file


def custom_css():
    st.markdown(
        """
        <style>
        body {
            font-family: 'Roboto', sans-serif;
            background: #f5f7fa;
        }

        .info-card {
            background-color: #ffffff;
            border-radius: 10px;
            padding: 15px;
            box-shadow: 0 3px 15px rgba(0, 0, 0, 0.1);
            margin: 15px 0;
            font-size: 16px;
        }

        .chat-image {
            border-radius: 8px;
            box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);
            margin-bottom: 10px;
            max-width: 300px;
            display: block;
            margin: 0 auto;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main():
    custom_css()

    # Initialize session state
    if "image_chat_history" not in st.session_state:
        st.session_state.image_chat_history = []
    if "audio_chat_history" not in st.session_state:
        st.session_state.audio_chat_history = []

    # Sidebar navigation
    with st.sidebar:
        st.markdown("## Navigation")
        if st.button("🖼️ Image Extraction"):
            st.session_state.app_mode = "Image Extraction Chat"
        if st.button("🎤 Speech Extraction"):
            st.session_state.app_mode = "Speech Extraction"

    # Determine app mode
    app_mode = st.session_state.get("app_mode", "Image Extraction Chat")

    if app_mode == "Image Extraction Chat":
        image_extraction_chat()
    elif app_mode == "Speech Extraction":
        speech_extraction()


def image_extraction_chat():
    st.title("🖼️ Image-Based Product Information")

    # File uploader and camera input
    uploaded_image = st.file_uploader("Upload an image...", type=["jpg", "jpeg", "png"])
    camera_image = st.camera_input("Take a picture")

    # Process the most recent input
    if camera_image is not None:
        process_image(camera_image, "Captured Image")
    elif uploaded_image is not None:
        process_image(uploaded_image, uploaded_image.name)

    # Display chat history
    display_image_chat_history()


def process_image(image, image_name):
    """Process the uploaded or captured image and save to chat history."""
    # Convert the image to base64 for chat display
    base64_image = base64.b64encode(image.getvalue()).decode("utf-8")

    # Add the image to chat history
    st.session_state.image_chat_history.append(
        {
            "role": "user",
            "image": base64_image,
            "name": image_name,
        }
    )

    # Extract product information
    with st.spinner("Processing image..."):
        product_info = extract_product_info(image)

    # Format the extracted information
    formatted_message = f"""
    <div class="info-card">
        <strong>Extracted Information:</strong>
        <ul>
            <li><strong>Product Name:</strong> {product_info['product_name']}</li>
            <li><strong>Company:</strong> {product_info['company']}</li>
            <li><strong>Start Date:</strong> {product_info['start_date']}</li>
            <li><strong>End Date:</strong> {product_info['end_date']}</li>
        </ul>
    </div>
    """

    # Add the extracted information to chat history
    st.session_state.image_chat_history.append(
        {
            "role": "system",
            "message": sanitize_message(formatted_message),
        }
    )


def display_image_chat_history():
    """Display the chat history for images."""
    if len(st.session_state.image_chat_history) > 0:
        st.write("### Chat History")
        for chat in st.session_state.image_chat_history:
            if chat["role"] == "user" and "image" in chat:
                st.markdown(
                    f'<img class="chat-image" src="data:image/png;base64,{chat["image"]}" alt="{chat["name"]}"/>',
                    unsafe_allow_html=True,
                )
            elif chat["role"] == "system":
                st.markdown(chat["message"], unsafe_allow_html=True)


def speech_extraction():
    st.title("🎤 Speech-Based Product Information")

    # File uploader and audio recorder
    uploaded_audio = st.file_uploader("Upload an audio file...", type=["wav", "mp3"])
    recorded_audio = st.audio_input("Record audio")

    # Process the most recent input
    if recorded_audio is not None:
        process_audio(recorded_audio, "Recorded Audio")
    elif uploaded_audio is not None:
        process_audio(uploaded_audio, uploaded_audio.name)

    # Display chat history
    display_audio_chat_history()


def process_audio(audio, audio_name):
    """Process the uploaded or recorded audio and save to chat history."""
    # Save the audio file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
        temp_audio_file.write(audio.getvalue())
        temp_audio_path = temp_audio_file.name

    # Transcribe the audio
    with st.spinner("Transcribing audio..."):
        transcription = transcribe_audio_file(temp_audio_path)

    # Add transcription to chat history
    formatted_message = f"""
    <div class="info-card">
        <strong>File:</strong> {audio_name}<br>
        <strong>Transcription:</strong><br>
        <div>{transcription}</div>
    </div>
    """
    st.session_state.audio_chat_history.append(
        {
            "role": "system",
            "message": formatted_message,
        }
    )


def display_audio_chat_history():
    """Display the chat history for audio."""
    if len(st.session_state.audio_chat_history) > 0:
        st.write("### Chat History")
        for chat in st.session_state.audio_chat_history:
            if chat["role"] == "system":
                st.markdown(chat["message"], unsafe_allow_html=True)


if __name__ == "__main__":
    main()
