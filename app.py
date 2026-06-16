import streamlit as st

from supervisor import process_query
from voice_agent import listen_to_driver

st.set_page_config(
    page_title="Vehicle Copilot",
    page_icon="🚗",
    layout="wide"
)

st.title("🚗 Vehicle Copilot")
st.write("AI-powered vehicle assistant")

# --------------------------
# Text Input
# --------------------------

issue = st.text_input(
    "Describe your vehicle issue"
)

# --------------------------
# Voice Input
# --------------------------

if st.button("🎤 Speak Issue"):

    with st.spinner("Listening..."):

        issue = listen_to_driver()

    st.success(f"You said: {issue}")

# --------------------------
# Analyze
# --------------------------

if st.button("Analyze"):

    if issue:

        with st.spinner("Analyzing vehicle issue..."):

            result = process_query(issue)

        # --------------------------
        # Risk Level
        # --------------------------
        
        st.subheader("🚨 Risk Level")

        risk = result.get("risk", "Unknown")

        if risk == "CRITICAL":
            st.error(f"🚨 {risk}")

        elif risk == "HIGH":
            st.warning(f"⚠️ {risk}")

        else:
            st.success(f"✅ {risk}")

        # --------------------------
        # Weather Metrics
        # --------------------------

        weather = result.get("weather", {})

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                "Temperature",
                f"{weather.get('temperature', 'N/A')} °C"
            )

        with col2:
            st.metric(
                "Humidity",
                f"{weather.get('humidity', 'N/A')} %"
            )

        with col3:
            st.metric(
                "Wind Speed",
                f"{weather.get('wind_speed', 'N/A')} m/s"
            )

        st.subheader("🌦 Weather")

        st.write(
            f"Condition: {weather.get('condition', 'N/A')}"
        )

        # --------------------------
        # Service Centre
        # --------------------------

        st.subheader("🔧 Nearby Service Centre")

        service = result.get("service_centre", [])

        if service:

            centre = service[0]

            st.success(f"""
            Name: {centre['name']}

            Address:
            {centre['address']}
            """)
            
            st.link_button(
            "Open in Maps",
            f"https://www.google.com/maps?q={centre['latitude']},{centre['longitude']}"
)

        else:

            st.info("No service centre found.")

        # --------------------------
        # Manual Guidance
        # --------------------------

        st.subheader("📖 Manual Guidance")

        manual = result.get(
            "manual",
            "No manual information available."
        )

        with st.expander("View Full Manual Guidance"):
            st.write(manual)
    else:

        st.warning(
            "Please type or speak an issue first."
        )