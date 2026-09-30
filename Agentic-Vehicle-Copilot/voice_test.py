from voice_agent import listen_to_driver
from tts_agent import speak

from supervisor import process_query

text = listen_to_driver()

if text:

    result = process_query(text)

    risk = result.get("risk", "Unknown")

    if "service_centre" in result:
        centre = result["service_centre"][0]

        message = (
         f"Nearest service centre found. "
         f"{centre['name']}"
    )
    
    elif risk == "CRITICAL":

        message = (
            "Critical issue detected. "
            "Please stop the vehicle safely."
        )

    elif risk == "HIGH":

        message = (
            "High risk issue detected."
        )

    else:

        message = (
            f"Risk level is {risk}"
        )

    speak(message)