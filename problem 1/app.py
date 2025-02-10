from flask import Flask, render_template, request, jsonify
import asyncio
import speech_recognition as sr
import google.generativeai as genai
import pyttsx3
import keys
import re

app = Flask(__name__)

genai.configure(api_key=keys.GOOGLE_API_KEY)

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

# def generate_response(prompt):
#     model = genai.GenerativeModel("gemini-1.5-flash")
#     response = model.generate_content(prompt)
#     return response.text

def generate_response(prompt):
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    cleaned_text = re.sub(r'\*', '', response.text)  # Remove all asterisks
    return cleaned_text


def text_to_speech(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

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