#using pyttsx3

from flask import Flask, render_template, request, jsonify
import speech_recognition as sr
import google.generativeai as genai
import pyttsx3
import re
import keys
import threading
import time

app = Flask(__name__)

# Configure Google Gemini API
genai.configure(api_key=keys.GOOGLE_API_KEY)

# Initialize pyttsx3
engine = pyttsx3.init()

# Select a female voice explicitly
female_voice = None
voices = engine.getProperty('voices')

for voice in voices:
    if "female" in voice.name.lower():  # Check for female voice
        female_voice = voice.id
        break

# If a female voice is found, use it; otherwise, use a fallback
if female_voice:
    engine.setProperty('voice', female_voice)
else:
    print("No female voice found. Using default voice.")
    engine.setProperty('voice', voices[0].id)  # Default to the first available voice

engine.setProperty('rate', 170)  # Adjust speed
engine.setProperty('volume', 1.0)  # Set volume

# Ensure only one speech thread runs at a time
speech_lock = threading.Lock()

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

def generate_response(prompt):
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    
    # Clean text and limit to 7-8 lines
    cleaned_text = re.sub(r'\*', '', response.text)  # Remove asterisks
    lines = cleaned_text.split("\n")  # Split into lines
    limited_text = "\n".join(lines[:8])  # Keep only first 8 lines

    return limited_text

def text_to_speech(text):
    def speak():
        with speech_lock:  # Prevent multiple speech instances
            engine.stop()  # Stop previous speech
            time.sleep(0.1)  # Small delay to ensure stopping
            engine.say(text)
            engine.runAndWait()

    speech_thread = threading.Thread(target=speak, daemon=True)
    speech_thread.start()

@app.route('/')
def index():
    return render_template('index.html')

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
