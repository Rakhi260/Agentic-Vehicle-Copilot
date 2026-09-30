import pyttsx3

engine = pyttsx3.init()

engine.say(
    "Critical engine overheating detected. Stop the vehicle safely."
)
engine.runAndWait()