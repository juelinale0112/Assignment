from flask import Flask, render_template, request, jsonify
import speech_recognition as sr
import google.generativeai as genai
from gtts import gTTS
import os
import re
import keys
import threading

app = Flask(__name__)

# Configure Google Gemini API
genai.configure(api_key=keys.GOOGLE_API_KEY)

# Function to transcribe speech from microphone
def transcribe_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)
    
    try:
        return recognizer.recognize_google(audio)
    except sr.UnknownValueError:
        return "Could not understand audio"
    except sr.RequestError:
        return "Error with the speech recognition service"

# Function to generate AI response using Google Gemini API
def generate_response(user_prompt):
    system_prompt = (
        "You are a helpful assistant. Always provide polite and formal responses. "
        "Ensure your answers are precise and mention the source of your information when relevant. "
        "Do not respond to any controversial or inappropriate questions."
    )
    
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content([system_prompt, user_prompt])
    
    # Clean and limit response to 8 lines
    cleaned_text = re.sub(r'\\*', '', response.text)
    lines = cleaned_text.split("\n")
    return "\n".join(lines[:8])

# Function to convert text to speech and play the response
def text_to_speech(text):
    def speak():
        try:
            tts = gTTS(text=text, lang='en', tld='co.uk', slow=False)
            tts.save("response.mp3")
            os.system("mpg321 response.mp3")  # Use 'afplay' on macOS
        except Exception as e:
            print(f"TTS Error: {e}")
    
    threading.Thread(target=speak, daemon=True).start()

# Route for rendering the homepage
@app.route('/')
def index():
    return render_template('index.html')

# Route to process text input and generate AI response
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

# Route to process speech input, generate response, and play the response
@app.route('/process_speech', methods=['POST'])
def process_speech():
    user_text = transcribe_speech()
    if user_text.startswith("Error"):
        return jsonify({"error": user_text})
    
    response_text = generate_response(user_text)
    text_to_speech(response_text)
    
    return jsonify({"user": user_text, "bot": response_text})

# Run the Flask application
if __name__ == '__main__':
    app.run(debug=True)
