import speech_recognition as sr

def listen_to_driver():
    
    recognizer = sr.Recognizer()
    
    with sr.Microphone() as source:
        
        print("Listening...")
        
        recognizer.adjust_for_ambient_noise(source)
        
        audio = recognizer.listen(source)
        
    try:
        text = recognizer.recognize_google(audio)
        
        return text

    except Exception as e:
        return f"Error: {e}"    