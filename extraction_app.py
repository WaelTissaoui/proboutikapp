import streamlit as st
import base64
import tempfile
from Extraction_api import extract_product_info, sanitize_message, transcribe_audio_file


def custom_css():
    # Custom CSS for styling
    st.markdown(
        """
        <style>
        /* General Styles */
        body {
            font-family: 'Roboto', sans-serif;
            background: #f5f7fa;
        }

        /* Chat Message Styles */
        .chat-message {
            margin-bottom: 15px;
            display: flex;
            align-items: flex-start;
            width: 100%;
        }

        .chat-message.user {
            justify-content: flex-end;
        }

        .chat-message .message-content {
            max-width: 65%;
            padding: 15px;
            border-radius: 12px;
            font-size: 16px;
            line-height: 1.6;
            word-wrap: break-word;
            box-shadow: 0 3px 12px rgba(0, 0, 0, 0.1);
        }

        .chat-message.user .message-content {
            background: linear-gradient(135deg, #6b73ff 0%, #000dff 100%);
            color: white;
            text-align: right;
        }

        .chat-message.system .message-content {
            background: #ffffff;
            color: #333;
            text-align: left;
        }

        /* Information Card for System Messages */
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
    custom_css()  # Apply custom CSS

    # Initialize app_mode in session state
    if "app_mode" not in st.session_state:
        st.session_state.app_mode = "Image Extraction Chat"  # Default mode

    # Initialize chat histories
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

    # Determine the app mode
    app_mode = st.session_state.app_mode

    if app_mode == "Image Extraction Chat":
        image_extraction_chat()
    elif app_mode == "Speech Extraction":
        speech_extraction()


def image_extraction_chat():
    st.title("🖼️ Image-Based Product Information")

    # File uploader for images
    uploaded_image = st.file_uploader("Upload an image...", type=["jpg", "jpeg", "png"])
    
    # Camera input for taking pictures
    camera_image = st.camera_input("Take a picture")

    # Initialize the image to process
    image_to_process = None
    image_name = None

    # Give priority to the most recent input
    if camera_image is not None:
        # Use the image captured from the camera
        image_to_process = camera_image
        image_name = "captured_image.png"  # Default name for camera image
    elif uploaded_image is not None:
        # Use the uploaded image
        image_to_process = uploaded_image
        image_name = uploaded_image.name

    # Process the selected image
    if image_to_process is not None:
        with st.spinner("Processing image..."):
            # Analyze the image
            product_info = extract_product_info(image_to_process)

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

        # Store the image and extracted information in session state
        base64_image = base64.b64encode(image_to_process.getvalue()).decode("utf-8")
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

    # Display chat history if available
    if len(st.session_state.image_chat_history) > 0:
        st.write("### Image Chat History")
        for chat in st.session_state.image_chat_history:
            if chat["role"] == "user" and "image" in chat:
                st.image(base64.b64decode(chat["image"]), caption="Uploaded or Captured Image", width=400)
            elif chat["role"] == "system":
                st.markdown(f"<div class='info-card'>{chat['message']}</div>", unsafe_allow_html=True)


def speech_extraction():
    st.markdown("<div class='speech-extraction'>", unsafe_allow_html=True)
    st.title("🎤 Speech-Based Product Information")
    st.write("Upload a WAV or MP3 file for transcription or record audio.")

    uploaded_audio = st.file_uploader("Upload an audio file...", type=["wav", "mp3"])

    audio_to_process = None

    if uploaded_audio is not None:
        audio_to_process = uploaded_audio
        audio_name = uploaded_audio.name

    if audio_to_process is not None:
        with st.spinner("Transcribing audio..."):
            # Use a temporary file to save the uploaded or recorded audio
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
                temp_audio_file.write(audio_to_process.getvalue())
                temp_audio_path = temp_audio_file.name

            # Transcribe the uploaded audio file
            transcription = transcribe_audio_file(temp_audio_path)

        # Format and save the transcription result in audio chat history
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

    # Display Audio Chat History if available
    if len(st.session_state.audio_chat_history) > 0:
        st.write("### Audio Chat History")
        for chat in st.session_state.audio_chat_history:
            if chat["role"] == "user":
                st.markdown(f"**User Uploaded File**: {chat['message']}")
            elif chat["role"] == "system":
                st.markdown(f"<div class='info-card'>{chat['message']}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
