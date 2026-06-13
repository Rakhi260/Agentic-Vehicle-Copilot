import streamlit as st
from supervisor import process_query

st.title("Vehicle Copilot")

issue = st.text_input("Describe your vehicle issue")

if st.button("Analyze"):
    result = process_query(issue)
    
    risk = result.get("risk","Unknown")

    if risk == "CRITICAL":
        st.error(f"🚨 {risk}")

    elif risk == "HIGH":
        st.warning(f"⚠️ {risk}")

    else:
        st.success(f"✅ {risk}")
        
    weather = result.get("weather", {})

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Temperature",
            f"{weather.get('temperature','N/A')} °C"
        )

    with col2:
        st.metric(
            "Humidity",
            f"{weather.get('humidity','N/A')} %"
        )

    with col3:
        st.metric(
            "Wind Speed",
            f"{weather.get('wind_speed','N/A')} m/s"
        )

    st.subheader("🌦 Weather")

    st.write(f"Condition: {weather.get('condition','N/A')}")
    st.write(f"Temperature: {weather.get('temperature','N/A')} °C")
    st.write(f"Humidity: {weather.get('humidity','N/A')} %")
    st.write(f"Wind Speed: {weather.get('wind_speed','N/A')} m/s")
    
    service = result.get("service_centre", [])

    st.subheader("🔧 Nearby Service Centre")

    if service:
        centre = service[0]

        st.success(f"""
    Name: {centre['name']}

    Address:
    {centre['address']}
    """)
        
    manual = result.get("manual", "")

    st.subheader("📖 Manual Guidance")

    st.info(manual[:500] + "...")