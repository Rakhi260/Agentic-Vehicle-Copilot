from safety_agent import assess_risk

while True:

    query = input("Issue: ")

    if query.lower() == "exit":
        break

    print("Sending to Gemini...")

    risk = assess_risk(query)

    print("Risk Level:", risk)