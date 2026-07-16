import time
# import streamlit as st

# from supervisor import process_query
# from voice_agent import listen_to_driver

import streamlit as st

print("1. Streamlit imported")

from supervisor import process_query
print("2. Supervisor imported")

from voice_agent import listen_to_driver
print("3. Voice agent imported")

st.set_page_config(
    page_title="Vehicle Copilot",
    page_icon="🚗",
    layout="wide"
)

st.title("🚗 Vehicle Copilot")
st.write("AI-powered vehicle assistant")

# --------------------------
# Session State
# --------------------------

if "issue" not in st.session_state:
    st.session_state.issue = ""

# --------------------------
# Text Input
# --------------------------

issue = st.text_input(
    "Describe your vehicle issue",
    value=st.session_state.issue
)

# --------------------------
# Voice Input
# --------------------------

if st.button("🎤 Speak Issue"):

    with st.spinner("Listening..."):

        spoken_issue = listen_to_driver()

    st.session_state.issue = spoken_issue

    issue = spoken_issue

    st.success(f"You said: {spoken_issue}")

# --------------------------
# Analyze
# --------------------------

if st.button("Analyze"):

    if issue:

        with st.spinner("Analyzing vehicle issue..."):

            start = time.time()

            result = process_query(issue)

            end = time.time()

        st.success(f"Processing Time: {end-start:.2f} sec")

        # --------------------------
        # Risk
        # --------------------------

        st.subheader("🚨 Risk Level")

        risk = result.get("risk", "Unknown")

        if risk == "CRITICAL":
            st.error(risk)

        elif risk == "HIGH":
            st.warning(risk)

        else:
            st.success(risk)

        # --------------------------
        # Weather
        # --------------------------

        weather = result.get("weather", {})

        st.subheader("🌦 Weather")

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Temperature",
            f"{weather.get('temperature','N/A')} °C"
        )

        col2.metric(
            "Humidity",
            f"{weather.get('humidity','N/A')} %"
        )

        col3.metric(
            "Wind Speed",
            f"{weather.get('wind_speed','N/A')} m/s"
        )

        col4.metric(
            "Feels Like",
            f"{weather.get('feels_like','N/A')} °C"
        )

        st.write(
            f"Condition: {weather.get('condition','N/A')}"
        )

        # --------------------------
        # Service Centre
        # --------------------------

        st.subheader("🔧 Nearby Service Centre")

        service = result.get("service_centre", [])

        if service:

            centre = service[0]

            st.success(
                f"""
**Name:** {centre['name']}

**Address:** {centre['address']}
"""
            )

            st.link_button(
                "📍 Open in Google Maps",
                f"https://www.google.com/maps?q={centre['latitude']},{centre['longitude']}"
            )

        else:

            st.info("No service centre found.")

        # --------------------------
        # Manual
        # --------------------------

        st.subheader("📖 Manual Guidance")

        manual = result.get(
            "manual",
            "No manual information available."
        )

        with st.expander("View Full Manual Guidance"):

            st.write(manual)

    else:

        st.warning("Please type or speak an issue.")