import streamlit as st
import asyncio
import speech_recognition as sr
from deepgram import Deepgram
from groq import Groq
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings
import os
import playsound

# 🔐 API Keys
DG_API_KEY = "929a643078dfbcb11431cabd06e72980a68cd90a"
GROQ_API_KEY = "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"
ELEVEN_API_KEY = "sk_d2591bfc30ee089694c1f789fd4344962692cc53aed72d2d"

# 🧠 Initialize Clients
dg_client = Deepgram(DG_API_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)
tts_client = ElevenLabs(api_key=ELEVEN_API_KEY)

if "conversation" not in st.session_state:
    st.session_state.conversation = [
        {"role": "system", "content": "You're a lovable but mean assistant and your job is to roast people like Seth Macfarlane"}
    ]

# 🧠 Groq response
def get_groq_response():
    completion = groq_client.chat.completions.create(
        model="llama3-70b-8192",
        messages=st.session_state.conversation,
        temperature=0.7
    )
    return completion.choices[0].message.content

# 🗣️ Speak
def speak(text):
    audio_stream = tts_client.generate(
        text=text,
        voice="Rachel",
        model="eleven_monolingual_v1",
        stream=True,
        voice_settings=VoiceSettings(
            stability=0.4,
            similarity_boost=0.75
        )
    )
    filename = "response.mp3"
    with open(filename, "wb") as f:
        for chunk in audio_stream:
            f.write(chunk)
    playsound.playsound(filename)
    os.remove(filename)

# 🎤 Listen
def listen():
    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 350
    recognizer.pause_threshold = 1.2
    with sr.Microphone() as source:
        st.info("🎤 Listening... Speak now!")
        audio = recognizer.listen(source, phrase_time_limit=None, timeout=None)
    audio_data = audio.get_wav_data()

    async def transcribe():
        response = await dg_client.transcription.prerecorded(
            {"buffer": audio_data, "mimetype": "audio/wav"},
            {"punctuate": True}
        )
        return response["results"]["channels"][0]["alternatives"][0]["transcript"]

    return asyncio.run(transcribe())

# 🌐 Streamlit UI
st.title("AI Roasting Assistant")

user_input = st.text_input("Type a message or click 'Talk' below:")

col1, col2 = st.columns([1, 2])

with col1:
    if st.button("🎙️ Talk"):
        voice_input = listen()
        if voice_input:
            user_input = voice_input

if user_input:
    st.session_state.conversation.append({"role": "user", "content": user_input})
    reply = get_groq_response()
    st.session_state.conversation.append({"role": "assistant", "content": reply})

    st.markdown(f"**You:** {user_input}")
    st.markdown(f"**Agent:** {reply}")
    speak(reply)