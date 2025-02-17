from PIL import Image
import sys
import streamlit as st
import os
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont
import textwrap
from io import BytesIO

# API Key (Replace with your actual key or use st.secrets)
genai.configure(api_key="api")

# Model Configuration
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",
    generation_config=generation_config,
)


def text_to_handwriting_images(text, chars_per_image=500):  # Added chars_per_image parameter
    """
    Generates one or more handwriting-style images from the given text,
    splitting the text into chunks if it's too long.

    Args:
        text: The text to convert.
        chars_per_image: The maximum number of characters to include in each image.

    Returns:
        A list of PIL Image objects.
    """
    images = []
    start = 0
    while start < len(text):
        end = min(start + chars_per_image, len(text))
        chunk = text[start:end]
        image = create_handwriting_image(chunk)  # Call the image creation function
        if image:
            images.append(image)
        start = end
    return images


def create_handwriting_image(text):  # Renamed and refactored
    """
    Creates a single handwriting-style image from the given text chunk.

    Args:
        text: The text chunk to convert.

    Returns:
        A PIL Image object, or None if an error occurred.
    """
    try:
        BG = Image.open("font/bg.png")  # Ensure bg.png exists in the font directory
    except FileNotFoundError:
        st.error("Could not find bg.png in the font directory.  Make sure it exists.")
        return None
    sheet_width = BG.width
    gap, ht = 0, 0

    for char in text:
        try:
            char_code = ord(char)
            char_image = Image.open(f"font/{char_code}.png")  # Ensure character images exist

            BG.paste(char_image, (gap, ht))
            size = char_image.width
            height = char_image.height
            gap += size

            if sheet_width < gap or len(char) * 115 > (sheet_width - gap):
                gap, ht = 0, ht + 140

        except FileNotFoundError:
            # If the character image isn't found, try to substitute with a space or skip silently
            if char_code == 32: # Check if the missing character is a space (ASCII 32)

                gap += 20  # Add a small gap for the space
                if sheet_width < gap :
                    gap, ht = 0, ht + 140


            elif char_code == 10 or char_code == 13: # newline character
                gap, ht = 0, ht + 140 #new line without warning
            else:
            # Option 1: Skip Silently (no warning)

            # Option 2: Use a default image if you have one
                try:
                   default_char_image = Image.open("font/default.png") # Create a default.png file
                   BG.paste(default_char_image, (gap, ht))
                   size = default_char_image.width
                   height = default_char_image.height
                   gap += size

                   if sheet_width < gap or len(char) * 115 > (sheet_width - gap):
                      gap, ht = 0, ht + 140


                except FileNotFoundError:
                   pass #skip with no message



        except Exception as e:  # Catch any other potential errors during image processing
            st.error(f"An error occurred while processing character '{char}': {e}")
            return None  # Return None if there is error

    return BG


# Streamlit App
st.title("AI Text Generation to Handwriting Converter")

# Input text from the user
prompt = st.text_area("Enter your prompt for AI generation:", "Write a short poem about a cat.")

# Image size control
chars_per_image = st.number_input("Max Characters Per Image", min_value=100, max_value=2000, value=500, step=100)

# Generate text with the AI model
if st.button("Generate Text"):
    with st.spinner("Generating text..."):
        chat_session = model.start_chat(history=[])
        response = chat_session.send_message(prompt)
        generated_text = response.text
        st.session_state.generated_text = generated_text

# Display the generated text
if 'generated_text' in st.session_state:
    st.subheader("Generated Text:")
    st.write(st.session_state.generated_text)

    # Convert the generated text to handwriting
    if st.button("Convert to Handwriting"):
        with st.spinner("Converting to handwriting..."):
            images = text_to_handwriting_images(st.session_state.generated_text, chars_per_image)  # Call the new function

            if images:  # Check if any images were created
                for i, image in enumerate(images):
                    st.image(image, caption=f"Handwritten Text (Part {i+1})", use_container_width=True)

                    # Download link for each image
                    img_bytes = BytesIO()
                    image.save(img_bytes, format="PNG")
                    st.download_button(
                        label=f"Download Handwriting Image (Part {i+1})",
                        data=img_bytes.getvalue(),
                        file_name=f"handwriting_output_part_{i+1}.png",
                        mime="image/png",
                    )
            else:
                st.error("No handwriting images could be generated.")
