import time
import requests
import streamlit as st

st.set_page_config(page_title="Race Telemetry", layout="wide")
st.title("🏎️ Live Telemetry Dashboard")


# Function to draw custom colored bars

def draw_progress_bar(label, value, color):
    st.write(label)
    # Clamp value between 0.0 and 1.0 just in case
    safe_value = max(0.0, min(1.0, value))
    st.markdown(f"""
        <div style="background-color: #2b2b2b; border-radius: 5px; width: 100%; margin-bottom: 15px;">
            <div style="background-color: {color}; width: {safe_value * 100}%; height: 24px; border-radius: 5px; transition: width 0.05s ease-out;"></div>
        </div>
        """, unsafe_allow_html=True)


try:
    response = requests.get("http://localhost:8000/live")
    snapshot = response.json()

    if snapshot is None:
        st.warning("Backend is running, but no simulator is connected.")
    else:
        col1, col2 = st.columns(2)

        with col1:
            st.metric("Current Lap Time", f"{snapshot['lap']['current_lap_time_s']:.2f} s")
            st.metric("Speed", f"{snapshot['powertrain']['vehicle_speed_kph']:.1f} kph")

        with col2:
            throttle = snapshot['inputs']['throttle_ratio'] or 0.0
            brake = snapshot['inputs']['brake_ratio'] or 0.0

            # Draw the custom HTML bars!

            draw_progress_bar("Throttle", throttle, "#00ff00")  # Bright Green
            draw_progress_bar("Brake", brake, "#ff0000")  # Bright Red

except requests.exceptions.ConnectionError:
    st.error("Cannot connect to backend engine. Is it running?")

# Push the pedal to the metal on refresh rate


@st.fragment
def updaten_im_hintergrund_oida():
    while True:
        draw_progress_bar("Pedal", 0.5, "#00ff00")
        draw_progress_bar("Brake", 0.5, "#ff0000")