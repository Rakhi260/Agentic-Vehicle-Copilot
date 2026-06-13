import speech_recognition as sr
import pyttsx3

from supervisor import process_query

#TTS Engine
recognizer = sr.Recognizer()

# Speech Recognition
engine = pyttsx3.init()

with sr.Microphone() as source:
    
    print("Speak..")
    
    recognizer.adjust_for_ambient_noise(source)
    
    audio = recognizer.listen(source)
try:  
    text = recognizer.recognize_google(audio)

    print("\nYou said:")
    print(text)
        
    #Send to supervisor
    result = process_query(text)

    risk = result.get("risk","Unknown")

    print("\nRisk:")
    print(risk)

    # Build response
    if risk == "CRITICAL":

        message = (
            "Critical issue detected. "
            "Please stop the vehicle safely and seek assistance."
        )

    elif risk == "HIGH":

        message = (
            "High risk issue detected. "
            "Please inspect the vehicle soon."
        )

    else:

        message = (
            f"Risk level is {risk}."
        )

    print("\nSpeaking...")
    print(message)

    # TTS
    engine.say(message)
    engine.runAndWait()

except Exception as e:

    print("Error:", e)