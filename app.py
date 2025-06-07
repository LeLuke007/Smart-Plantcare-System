import streamlit as st
import requests, os
from io import BytesIO
from PIL import Image
import numpy as np
import pandas as pd
import datetime, time, json
from tensorflow.keras.models import load_model
from streamlit_autorefresh import st_autorefresh


ESP32_CAM_IP = '192.xxx.xx.xxx' # Set your ESP32-CAM IP
ESP32_IP = '192.xxx.xx.xxx' # Set your ESP32 IP

st.set_page_config(page_title="Smart PlantCare", layout="wide", initial_sidebar_state="expanded", page_icon="🌱")

st_autorefresh(interval=2000, key="datarefresh")

@st.cache_resource
def get_model():
    return load_model("model.h5", compile=False)

def get_threshold(sensor):
    try:
        response = requests.get(f"http://{esp_soil_ip}/setthresholds", timeout=5)
        response.raise_for_status()
        data = json.loads(response.text.strip())
        return data[sensor]
    except Exception as e:
        st.error(f"Error fetching thresholds: {e}", icon="⛔")
        return None

def on_mode_change():
    esp_mode = st.session_state.mode.lower()
    try:
        requests.get(f"http://{esp_soil_ip}/setmode", params={"mode": esp_mode}, timeout=3)
        st.toast(f"Mode set to {st.session_state.mode}", icon="✅")
    except Exception as e:
        st.toast(f"Failed to set mode: {e}", icon="⛔")

try:
    model = get_model()
    with open("categories.json", "r") as f:
        categories = json.load(f)
    class_labels = [None] * len(categories)
    for label, idx in categories.items():
        class_labels[idx] = label.replace("___", " - ").replace("_", " ")
    model_loaded=True
except Exception as e:
    st.warning(f"Model load failed: {e}")
    model_loaded=False

# Custom CSS
st.markdown("""
<style>
.main-header { font-size:38px;font-weight:bold;color:#2E7D32;text-align:center;margin-bottom:30px; }
.section-header { font-size:24px;font-weight:bold;color:#1976D2;padding-top:20px; }
.dashboard-card { background:#f5f5f5;border-radius:10px;padding:20px;box-shadow:0 4px 8px rgba(0,0,0,0.1);margin-bottom:20px; }
.status-good{color:#4CAF50;font-weight:bold;} .status-warning{color:#FF9800;font-weight:bold;} .status-bad{color:#F44336;font-weight:bold;}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.title("⚙️ Configurations")
    # st.markdown("### 🔧 Configurations")
    now = datetime.datetime.now().strftime("%H:%M:%S")
    st.sidebar.markdown(f"**Last updated:** {now}")
    with st.expander("📡 Network Settings",expanded=True):
        esp_cam_ip=st.text_input("ESP32-CAM IP",value=ESP32_CAM_IP)
        esp_soil_ip=st.text_input("ESP32 IP",value=ESP32_IP)
    with st.expander("⚙️ Auto Mode Settings",expanded=True):
        soil_th  = st.slider("Soil Moisture (%)", 0,100,55)
        temp_th  = st.slider("Temperature (°C)", 10.0,50.0,27.5, step=0.5)
        hum_th   = st.slider("Humidity (%)", 0,100,75)
        if st.button("Apply Thresholds"):
            try:
                requests.get(
                    f"http://{esp_soil_ip}/setthresholds",
                    params={"soil":soil_th,"temp":temp_th,"hum":hum_th},
                    timeout=3
                )
                st.toast("Thresholds updated", icon="✅")
            except:
                st.toast("Failed to update thresholds", icon="⛔")

st.markdown('<p class="main-header"> <h1> 🌱 Smart Plant Care System </h1></p>', unsafe_allow_html=True)

# Tabs
tab1,tab2,tab3,tab4,tab5=st.tabs(["📸 Camera Feed","💧 Soil Moisture","🌡️ Temperature & Humidity","🌤️ Sunlight","🛠️ Manual Controls"])

with tab5:
    # Mode control (Auto/Manual)
    mode = st.radio(
        "Select Mode:", 
        ["Auto", "Manual"], 
        key="mode", 
        on_change=on_mode_change
    )

    if st.session_state.mode == "Auto":
        st.write("#### 📡 System is in Auto mode.")
    else:
        st.write("#### 🛠️ System is in Manual mode.")

        st.markdown("### Pump Control")
        pump1, pump2 = st.columns(2)
        if pump1.button("Turn Pump ON", icon="🟢", use_container_width=True):
            try:
                requests.get(f"http://{esp_soil_ip}/manualpump?state=on", timeout=5)
                st.toast("Pump Turned ON", icon="✅")
            except Exception as e:
                st.toast(f"Error turning pump ON: {e}", icon="⛔")

        if pump2.button("Turn Pump OFF", icon="🔴", use_container_width=True):
            try:
                requests.get(f"http://{esp_soil_ip}/manualpump?state=off", timeout=5)
                st.toast("Pump Turned OFF", icon="⚠️")
            except Exception as e:
                st.toast(f"Error turning pump OFF: {e}", icon="⛔")

        st.write("")
        st.markdown("### Fan Control")
        fan1, fan2 = st.columns(2)
        if fan1.button("Turning Fan ON", icon="🟢", use_container_width=True):
            try:
                requests.get(f"http://{esp_soil_ip}/manualfan?state=on", timeout=5)
                st.toast("Turning Fan ON", icon="✅")
            except Exception as e:
                st.toast(f"Error turning fan ON: {e}", icon="⛔")

        if fan2.button("Turning Fan OFF", icon="🔴", use_container_width=True):
            try:
                requests.get(f"http://{esp_soil_ip}/manualfan?state=off", timeout=5)
                st.toast("Turning Fan OFF", icon="⚠️")
            except Exception as e:
                st.toast(f"Error turning fan OFF: {e}", icon="⛔")

        st.write("")
        st.markdown("### Roof Control")
        roof1, roof2 = st.columns(2)
        if roof1.button("Open the Roof", icon="🟢", use_container_width=True):
            try:
                requests.get(f"http://{esp_soil_ip}/manualroof?state=open", timeout=5)
                st.toast("Opening the Roof", icon="✅")
            except Exception as e:
                st.toast(f"Error opening the Roof: {e}", icon="⛔")

        if roof2.button("Close the Roof", icon="🔴", use_container_width=True):
            try:
                requests.get(f"http://{esp_soil_ip}/manualroof?state=close", timeout=5)
                st.toast("Closing the Roof", icon="⚠️")
            except Exception as e:
                st.toast(f"Error closing the roof: {e}", icon="⛔")

with tab2:
    st.header("💧 Soil Moisture Monitoring")
    st.write("")

    if "moisture_data" not in st.session_state:
        st.session_state.moisture_data = pd.DataFrame(columns=["Time", "Moisture"])

    dynamic = st.container()

    with dynamic:
        try:
            soil_url = f"http://{esp_soil_ip}/sensor"
            soil_resp = requests.get(soil_url, timeout=5)
            soil_resp.raise_for_status()
            moisture = int(soil_resp.text)
            st.metric(label="🌿 Current Soil Moisture (%)", value=moisture)
            st.write("")

            current_time = datetime.datetime.now()
            new_row = pd.DataFrame({"Time": [current_time], "Moisture": [moisture]})
            st.session_state.moisture_data = pd.concat(
                [st.session_state.moisture_data, new_row], ignore_index=True
            )
            # if len(st.session_state.moisture_data) > 20:
            #     st.session_state.moisture_data = st.session_state.moisture_data.iloc[-20:]

            st.line_chart(
                st.session_state.moisture_data.set_index("Time"),
                y="Moisture",
                use_container_width=True
            )

            st.write("Water Pump Status")
            if mode == "Auto":
                if moisture <= get_threshold('soil'):
                    st.success("✅ Pump ON (Auto)", width=200)
                else:
                    st.warning("⚠️ Pump OFF (Auto)", width=200)
            else:
                st.info("ℹ️ Manual Mode Active", width=200)
        except Exception as e:
            st.toast(f"Failed to fetch soil data: {e}", icon="⛔")

    
with tab3:
    st.header("🌡️ Temperature & Humidity Monitoring")
    st.write("")

    dynamic = st.container()

    with dynamic:
        try:
            response = requests.get(f"http://{esp_soil_ip}/dht", timeout=5)
            response.raise_for_status()
            data = response.text.strip().split(",")
            hum = float(data[0])
            temp = float(data[1])

            st.metric("🌡 Temperature (°C)", f"{temp:.1f}")
            st.metric("💧 Humidity (%)", f"{hum:.1f}")
            st.write("Fan Status")
            if mode == "Auto":
                if temp > get_threshold('temp') or hum > get_threshold('hum'):
                    # requests.get(f"http://{esp_soil_ip}/fanauto?state=on", timeout=5)
                    st.success("✅ Fan ON (Auto)", width=200)
                else:
                    # requests.get(f"http://{esp_soil_ip}/fanauto?state=off", timeout=5)
                    st.warning("⚠️ Fan OFF (Auto)", width=200)
            else:
                st.info("ℹ️ Manual Mode Active", width=200)
        except Exception as e:
            st.error(f"Error reading DHT22 or controlling fan: {e}")


with tab4:
    st.header("🌤️ Sunlight Exposure")
    st.write("")

    dynamic = st.container()

    with dynamic:
        try:
            response = requests.get(f"http://{esp_soil_ip}/ldr", timeout=5)
            response.raise_for_status()
            light = int(response.text.strip())
            if light == 0:
                st.markdown("### ☀️ Sunlight Present")
            if light == 1:
                st.markdown("### 🌑 No Sunlight")
            st.write("")
            st.write("Roof Status")
            if mode == "Auto":
                if light == 0:
                    st.success("✅ Roof Open (Auto)", width=200)
                if light == 1:
                    st.warning("⚠️ Roof Closed (Auto)", width=200)
            else:
                st.info("ℹ️ Manual Mode Active", width=200)
        except Exception as e:
            st.toast(f"Error reading or controlling roof: {e}", icon="⛔")

# ESP32-CAM Feed and Detection
with tab1:
    st.header("📸 Live Plant Camera Feed")
    st.write("")

    dynamic2 = st.container()

    # Live Feed from ESP32-CAM
    with dynamic2:
        try:
            url = f"http://{esp_cam_ip}/capture"
            resp = requests.get(url, timeout=5, headers={"Connection": "close"})
            resp.raise_for_status()
            img = Image.open(BytesIO(resp.content))
            st.image(img, caption="ESP32-CAM Live", use_container_width=True)
            captured_img = img
            st.markdown("### 🦠 Disease Detection Status")
            # detect_button = st.button("🛎 Detect Disease")

            if captured_img is not None:
                img_resized = captured_img.resize((224, 224)) # resize
                arr = np.array(img_resized) / 255.0
                arr = np.expand_dims(arr, axis=0)
                preds = model.predict(arr)
                idx = np.argmax(preds[0])
                label = class_labels[idx]
                confidence = preds[0][idx]
                if 'healthy' in label.lower():
                    st.markdown(f'<span style="font-size:20px; color: green;"> Prediction: **{label}** ({confidence*100:.1f}%)</span>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<span style="font-size:20px; color: red;"> Prediction: **{label}** ({confidence*100:.1f}%)</span>', unsafe_allow_html=True)
                detect_button = False
                captured_img = None
        except Exception as e:
            st.toast(f"Error fetching live feed: {e}", icon="⛔")


        st.write("")
        st.markdown("### 💡 Flash Control")
        col1, col2 = st.columns(2)
        if col1.button("Turn Flash ON", icon="🔦", use_container_width=True):
            try:
                requests.get(f"http://{esp_cam_ip}/flashon", timeout=5)
                st.toast("Flash turned ON", icon="✅")
            except Exception as e:
                st.toast(f"Error turning flash ON: {e}", icon="⛔")

        if col2.button("Turn Flash OFF", icon="🚫", use_container_width=True):
            try:
                requests.get(f"http://{esp_cam_ip}/flashoff", timeout=5)
                st.toast("Flash turned OFF", icon="✅")
            except Exception as e:
                st.toast(f"Error turning flash OFF: {e}", icon="⛔")