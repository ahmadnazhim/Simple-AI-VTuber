import google.generativeai as genai
import os
import requests
from pydub import AudioSegment
from pydub.playback import play
from googletrans import Translator
import speech_recognition as sr


# Define the VoiceVox API endpoint
voicevox_url = "http://localhost:50021"

# Gemini AI API key
apiKey = 'INSERT GEMINI AI API KEY HERE'
os.environ['API_KEY'] = apiKey

genai.configure(api_key=os.environ['API_KEY'])

# Create the model
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
)

chat_session = model.start_chat(history=[])

def get_microphone_input():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        audio = recognizer.listen(source)
    try:
        print("Recognizing...")
        text = recognizer.recognize_google(audio)
        return text
    except sr.UnknownValueError:
        print("AI: Sorry, I did not understand the audio.")
    except sr.RequestError:
        print("Could not request results from the speech recognition service.")

while True:
    try:
        choices = int(input('(1.Chat  2.Microphone)\nEnter your choice: '))
        
        if choices == 1:
            prompt = input('\nUser: ')
        elif choices == 2:
            prompt = get_microphone_input()
            print('\nUser',prompt)
            if not prompt:
                continue

        print('\nWaiting for AI to respond...')
        ai_response = chat_session.send_message(prompt).text

        max_length = 300
        if len(ai_response) > max_length:
            ai_response = chat_session.send_message(prompt + ' Please respond in two sentences only').text

    except genai.types.generation_types.StopCandidateException:
        print('AI: Error prompt')
        break

    # Translator
    translation = Translator()
    result = translation.translate(ai_response, dest='ja').text

    query_response = requests.post(f"{voicevox_url}/audio_query", params={"text": result, "speaker": 8})#Choose speaker for voice audio
    audio_query = query_response.json()
    synthesis_response = requests.post(f"{voicevox_url}/synthesis", json=audio_query, params={"speaker": 8})

    # Save the audio to a file
    audio_file_path = "output.wav"
    with open(audio_file_path, "wb") as audio_file:
        audio_file.write(synthesis_response.content)

    print('--' * 75)
    print("\n[AI is talking....]")
    print('\nAI:', ai_response)
    print('Japanese Translation: ', result)
    print('--' * 75)

    # Load the audio file
    audio = AudioSegment.from_file(audio_file_path)

    # Play the audio file
    play(audio)