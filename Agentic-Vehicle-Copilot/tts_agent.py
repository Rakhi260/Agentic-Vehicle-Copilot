import pyttsx3 #loads text to speech library

engine = pyttsx3.init() #initialize the speech engine (setting up the voice system)

def speak(text):
    
    print("Copilot:",text)
    
    engine.say(text) #Sends the text to the speech engine to be spoken aloud.
    
    engine.runAndWait() #Processes the voice command and waits until speaking is finished.