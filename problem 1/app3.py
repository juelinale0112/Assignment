#using google text to speech 
from flask import Flask, render_template, request, jsonify
import speech_recognition as sr
import google.generativeai as genai
from gtts import gTTS
import os
import re
import keys
import threading
import time

app = Flask(__name__)

# Configure Google Gemini API
genai.configure(api_key=keys.GOOGLE_API_KEY)

# Function to transcribe speech
def transcribe_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
    
    try:
        text = recognizer.recognize_google(audio)
        return text
    except sr.UnknownValueError:
        return "Could not understand audio"
    except sr.RequestError:
        return "Error with the speech recognition service"

def generate_response(user_prompt):
    system_prompt = (
        "You are a helpful assistant. Always provide polite and formal responses. "
        "Ensure your answers are precise and mention the source of your information when relevant. "
        "Do not respond to any controversial or inappropriate questions."
    )
    
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content([system_prompt, user_prompt])  # Include system prompt
    
    # Clean text and limit to 7-8 lines
    cleaned_text = re.sub(r'\*', '', response.text)  # Remove asterisks
    lines = cleaned_text.split("\n")  # Split into lines
    limited_text = "\n".join(lines[:8])  # Keep only first 8 lines

    return limited_text

# Function to convert text to speech using Google TTS
def text_to_speech(text):
    def speak():
        try:
            tts = gTTS(text=text, lang='en', tld='co.uk', slow=False)  # UK Female voice
            tts.save("response.mp3")  # Save as MP3 file
            os.system("mpg321 response.mp3")  # Play audio (use `afplay` on macOS)
        except Exception as e:
            print(f"TTS Error: {e}")

    t = threading.Thread(target=speak, daemon=True)
    t.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_text', methods=['POST'])
def process_text():
    data = request.get_json()
    user_text = data.get("text", "")

    if not user_text:
        return jsonify({"error": "Empty input"}), 400

    try:
        response_text = generate_response(user_text)
        return jsonify({"bot": response_text})
    except Exception as e:
        print(f"Error processing text: {e}")
        return jsonify({"error": "Error processing request"}), 500


@app.route('/process_speech', methods=['POST'])
def process_speech():
    user_text = transcribe_speech()
    if user_text.startswith("Error"):
        return jsonify({"error": user_text})
    
    response_text = generate_response(user_text)
    text_to_speech(response_text)
    
    return jsonify({"user": user_text, "bot": response_text})

if __name__ == '__main__':
    app.run(debug=True)

