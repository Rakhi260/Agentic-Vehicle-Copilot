# import speech_recognition as sr

# recognizer = sr.Recognizer()

# def listen_to_driver():
    
#     with sr.Microphone() as source:
        
#         print("Listening...")
        
#         recognizer.adjust_for_ambient_noise(source,duration=1)
        
#         audio = recognizer.listen(source)
        
#     try:
#         text = recognizer.recognize_google(audio)
#         print("Driver:", text)
#         return text

#     except Exception as e:
#         return f"Error: {e}"    