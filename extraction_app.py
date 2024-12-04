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


# Streamlit app
def main():
    custom_css()

    # Initialize app_mode in session state
    if "app_mode" not in st.session_state:
        st.session_state.app_mode = "Image Extraction Chat"

    # Initialize chat histories
    if "image_chat_history" not in st.session_state:
        st.session_state.image_chat_history = []
    if "audio_chat_history" not in st.session_state:
        st.session_state.audio_chat_history = []
    if "image_processed" not in st.session_state:
        st.session_state.image_processed = False

    # Sidebar navigation
    with st.sidebar:
        st.markdown("## Navigation")
        if st.button("🖼️ Image Extraction"):
            st.session_state.app_mode = "Image Extraction Chat"
        if st.button("🎤 Speech Extraction"):
            st.session_state.app_mode = "Speech Extraction"
        if st.button("🔄 Reset"):
            reset_session_state()

    # Determine app mode
    app_mode = st.session_state.app_mode

    if app_mode == "Image Extraction Chat":
        image_extraction_chat()
    elif app_mode == "Speech Extraction":
        speech_extraction()


def reset_session_state():
    """Reset the session state to clear all data."""
    st.session_state.image_chat_history = []
    st.session_state.audio_chat_history = []
    st.session_state.image_processed = False
    st.session_state.app_mode = "Image Extraction Chat"
    st.experimental_rerun()


def image_extraction_chat():
    st.title("🖼️ Image-Based Product Information")

    # Upload or capture an image
    uploaded_image = st.file_uploader("Upload an image...", type=["jpg", "jpeg", "png"])
    camera_image = st.camera_input("Take a picture")

    # Process the latest input
    if not st.session_state.image_processed:
        if camera_image is not None:
            process_image(camera_image, "captured_image.png")
        elif uploaded_image is not None:
            process_image(uploaded_image, uploaded_image.name)


def process_image(image, image_name):
    """Process the uploaded or captured image."""
    st.session_state.image_processed = True
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

    # Save the processed image and data to chat history
    base64_image = base64.b64encode(image.getvalue()).decode("utf-8")
    st.session_state.image_chat_history.append(
        {
            "role": "user",
            "image": base64_image,
            "message": None,
        }
    )
    st.session_state.image_chat_history.append(
        {
            "role": "system",
            "message": sanitize_message(formatted_message),
        }
    )

    # Display chat history
    display_image_chat_history()


def display_image_chat_history():
    """Display the image chat history."""
    if len(st.session_state.image_chat_history) > 0:
        st.write("### Image Chat History")
        for chat in st.session_state.image_chat_history:
            if chat["role"] == "user" and "image" in chat:
                st.image(base64.b64decode(chat["image"]), caption="Uploaded or Captured Image", width=400)
            elif chat["role"] == "system":
                st.markdown(f"<div class='info-card'>{chat['message']}</div>", unsafe_allow_html=True)


def speech_extraction():
    st.title("🎤 Speech-Based Product Information")

    # Upload or record audio
    uploaded_audio = st.file_uploader("Upload an audio file...", type=["wav", "mp3"])
    recorded_audio = st.audio_input("Record audio")

    audio_to_process = None
    audio_name = None

    if recorded_audio is not None:
        audio_to_process = recorded_audio
        audio_name = "recorded_audio.wav"
    elif uploaded_audio is not None:
        audio_to_process = uploaded_audio
        audio_name = uploaded_audio.name

    if audio_to_process is not None:
        with st.spinner("Transcribing audio..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
                temp_audio_file.write(audio_to_process.getvalue())
                temp_audio_path = temp_audio_file.name

            transcription = transcribe_audio_file(temp_audio_path)

        # Save transcription to chat history
        formatted_message = f"""
        <div style="font-size: 18px; line-height: 1.6;">
            <strong>File:</strong> {audio_name}<br>
            <strong>Transcription:</strong><br>
            <div style="margin-left: 20px;">{transcription}</div>
        </div>
        """
        st.session_state.audio_chat_history.append(
            {
                "role": "user",
                "message": audio_name,
            }
        )
        st.session_state.audio_chat_history.append(
            {
                "role": "system",
                "message": formatted_message,
            }
        )

        # Display audio chat history
        display_audio_chat_history()


def display_audio_chat_history():
    """Display the audio chat history."""
    if len(st.session_state.audio_chat_history) > 0:
        st.write("### Audio Chat History")
        for chat in st.session_state.audio_chat_history:
            if chat["role"] == "user":
                st.markdown(f"**User Uploaded File**: {chat['message']}")
            elif chat["role"] == "system":
                st.markdown(f"<div class='info-card'>{chat['message']}</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
