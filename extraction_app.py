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
            padding: 20px;
            box-shadow: 0 3px 15px rgba(0, 0, 0, 0.1);
            margin: 15px 0;
            line-height: 1.6;
            font-size: 18px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main():
    custom_css()

    # Initialize app_mode in session state
    if "app_mode" not in st.session_state:
        st.session_state.app_mode = "Image Extraction Chat"

    # Sidebar navigation
    with st.sidebar:
        st.markdown("## Navigation")
        if st.button("🖼️ Image Extraction"):
            st.session_state.app_mode = "Image Extraction Chat"
        if st.button("🎤 Speech Extraction"):
            st.session_state.app_mode = "Speech Extraction"

    # Determine app mode
    app_mode = st.session_state.app_mode

    if app_mode == "Image Extraction Chat":
        image_extraction_chat()
    elif app_mode == "Speech Extraction":
        speech_extraction()


def image_extraction_chat():
    st.title("🖼️ Image-Based Product Information")

    # Upload or capture an image
    uploaded_image = st.file_uploader("Upload an image...", type=["jpg", "jpeg", "png"])
    camera_image = st.camera_input("Take a picture")

    if camera_image is not None:
        # Process the camera image
        process_image(camera_image, "captured_image.png")
    elif uploaded_image is not None:
        # Process the uploaded image
        process_image(uploaded_image, uploaded_image.name)


def process_image(image, image_name):
    """Process the uploaded or captured image."""
    with st.spinner("Processing image..."):
        product_info = extract_product_info(image)

    # Format the extracted information
    formatted_message = f"""
    <div style="font-size: 18px; line-height: 1.6;">
        <strong>Extracted Information:</strong>
        <ul style="list-style-type: disc; margin-left: 20px;">
            <li><strong>Product Name:</strong> {product_info['product_name']}</li>
            <li><strong>Company:</strong> {product_info['company']}</li>
            <li><strong>Start Date:</strong> {product_info['start_date']}</li>
            <li><strong>End Date:</strong> {product_info['end_date']}</li>
        </ul>
    </div>
    """

    # Display the extracted information
    st.markdown(f"<div class='info-card'>{sanitize_message(formatted_message)}</div>", unsafe_allow_html=True)

    # Display the image
    st.image(image, caption=image_name, use_column_width=True)


def speech_extraction():
    st.title("🎤 Speech-Based Product Information")

    # Upload or record audio
    uploaded_audio = st.file_uploader("Upload an audio file...", type=["wav", "mp3"])
    recorded_audio = st.audio_input("Record audio")

    if recorded_audio is not None:
        # Process the recorded audio
        process_audio(recorded_audio, "recorded_audio.wav")
    elif uploaded_audio is not None:
        # Process the uploaded audio
        process_audio(uploaded_audio, uploaded_audio.name)


def process_audio(audio, audio_name):
    """Process the uploaded or recorded audio."""
    with st.spinner("Transcribing audio..."):
        # Save the audio to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
            temp_audio_file.write(audio.getvalue())
            temp_audio_path = temp_audio_file.name

        # Transcribe the audio file
        transcription = transcribe_audio_file(temp_audio_path)

    # Format and display the transcription
    formatted_message = f"""
    <div style="font-size: 18px; line-height: 1.6;">
        <strong>File:</strong> {audio_name}<br>
        <strong>Transcription:</strong><br>
        <div style="margin-left: 20px;">{transcription}</div>
    </div>
    """
    st.markdown(f"<div class='info-card'>{formatted_message}</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
