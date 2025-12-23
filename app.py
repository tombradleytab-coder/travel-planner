import streamlit as st
import sys
import subprocess
import datetime
import os
import time

# --- SELF-HEALING MECHANISM ---
try:
    from google import genai
    from google.genai import types
    from google.genai import errors
except ImportError:
    st.warning("⚠️ Google GenAI Library missing. Attempting auto-fix...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "google-genai"])
        st.success("✅ Library Installed! Please REFRESH this page now.")
        st.stop()
    except Exception as e:
        st.error(f"❌ Auto-fix failed: {e}")
        st.stop()

# --- 1. APP CONFIGURATION ---
st.set_page_config(
    page_title="Bradley Planner v17.8", 
    page_icon="🚐", 
    layout="centered", 
    initial_sidebar_state="expanded"
)

# --- 2. CUSTOM CSS ---
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            .stApp {padding-top: 10px;}
            div[data-testid="stVerticalBlock"] > div {gap: 0.8rem;}
            .stButton>button {
                width: 100%;
                border-radius: 10px;
                height: 3em;
                font-weight: bold;
                background-color: #FF4B4B; 
                color: white;
            }
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- 3. BRADLEY FAMILY CONTEXT (V4.0) ---
BRADLEY_PLAN_CONTEXT = """
FAMILY PROFILE:
- Tom & Cara (40): Expert Skiers (Double Blacks), Mtn Biking.
- Kids: Rowan (8), Rhys (6). Loves outdoors, playgrounds. Medical: Stage 1 Kidney (No NSAIDs).
- Dog: Finn (9). Needs on-leash friendly areas.
- Homeschool Focus: Geology, History, Wildlife.

RIG SPECS (Critical for Routing):
- Tow: 2023 RAM 2500 Rebel.
- Trailer: 2026 Impression 318RL (Length: 39').
- Constraints: Requires large pull-thrus. Avoids narrow routes (e.g., NO Teton Pass).
- Memberships: Thousand Trails, Harvest Hosts, Amex Platinum (FHR), Marriott Bonvoy.

MAINTENANCE PROTOCOLS (Mandatory Checks):
- Trailer Lugs: Torque to 100-120 ft/lbs before major travel.
- Trailer Slides: Lubricate seals/tracks if >1 month stationary.
- Tires: Inspect pressure (Heavy towing wear pattern).
- Roof: Visual inspection for seal cracks (Dicor).
"""

# --- 4. SIDEBAR: API KEY & MODEL DOCTOR ---
with st.sidebar:
    st.header("🔐 App Settings")
    
    # API Key Input
    try:
        if "GOOGLE_API_KEY" in st.secrets:
            api_key = st.secrets["GOOGLE_API_KEY"]
            st.success("API Key Loaded")
        else:
            api_key = st.text_input("Gemini API Key", type="password")
    except Exception:
        api_key = st.text_input("Gemini API Key", type="password")

    # --- THE MODEL DOCTOR ---
    st.markdown("### 🤖 Model Selector")
    st.caption("Fetching valid models from your account...")
    
    available_models = []
    
    if api_key:
        try:
            client_check = genai.Client(api_key=api_key)
            # Fetch the raw list from Google
            models_iterable = client_check.models.list()
            
            for m in models_iterable:
                # We get the full name (e.g., "models/gemini-1.5-flash-001")
                name = getattr(m, 'name', str(m))
                # Only keep models that support content generation
                if "generateContent" in getattr(m, 'supported_generation_methods', []) or "gemini" in name:
                    available_models.append(name)
            
            if not available_models:
                st.error("Key valid, but no models found.")
        except Exception as e:
            st.error(f"Connection Failed: {e}")

    # Fallback if fetch failed
    if not available_models:
        available_models = ["models/gemini-1.5-flash", "models/gemini-1.5-pro"]
    
    # THE DROPDOWN: User picks a VALID model
    selected_model = st.selectbox("Select Active Model:", available_models, index=0)
    st.write(f"**Target:** `{selected_model}`")

    st.info("System: v17.8 Fixed")

# --- 5. MAIN INTERFACE ---
st.title("Multi-Day Trip Planner v17.8")
st.caption("Guaranteed Model Compatibility")

# --- VEHICLE CONFIGURATION ---
with st.expander("🚐 Vehicle Config (Edit)", expanded=True):
    c1, c2 = st.columns(2)
    with c1:
        tow_vehicle = st.text_input("Tow Vehicle", value="2023 RAM 2500 Rebel (Gas)", key="tow_v28")
    with c2:
        trailer_name = st.text_input("Trailer", value="2026 Impression 318RL (39')", key="trail_v28")
    
    c3, c4, c5 = st.columns(3)
    with c3:
        # Fixed formatting here to prevent line-break errors
        length = st.text_input("Length", value="39'", key="len_v28")
    with c4:
        weight = st.text_input("Weight", value="~14.1k lbs", key="wgt_v28")
    with c5:
        mpg = st.number_input("MPG", value=8.0, step=0.5, format="%.1f", key="mpg_v28")

# --- TRIP DETAILS ---
with st.container(border=True):
    st.subheader("📍 Route & Pace")
    origin = st.text_input("Departure Location", placeholder="e.g. North Bend, WA")
    destination = st.text_input("Final Destination", placeholder="e.g. Moab, UT")
    st.markdown("###")
    max_drive = st.slider("Max Driving Hours per Day", min_value=2, max_value=12, value=6, format="%d hrs")
    c_date, c_time = st.columns(2)
    with c_date:
        dept_date = st.date_input("Start Date", datetime.date(2026, 2, 15))
    with c_time:
        dept_time = st.time_input("Start Time", datetime.time(9, 0))

# --- PREFERENCES ---
with st.expander("🛠️ Strategy & Homeschool", expanded=False):
    c1, c2 = st.columns(2)
    with c1:
        pref_membership = st.checkbox("Thousand Trails/HH", value=True)
        pref_boondock = st.checkbox("Allow Boondocking", value=True)
    with c2:
        slide_out = st.checkbox("Lunch: Slide-outs", value=True)
        pref_luxury = st.checkbox("Luxury Break (Amex/Marriott)", value=True)
    st.divider()
    homeschool_focus = st.selectbox("Homeschool Topic:", 
                                    ["Auto-Detect (Route Context)", "General Knowledge", "Geology & Earth Science", "American History", "Wildlife Biology", "Engineering/Infrastructure"])

# --- 6. LOGIC: PROMPT GENERATION ---
def generate_prompt(live_search_enabled=True):
    fuel_type = "Diesel" if "diesel" in tow_vehicle.lower() else "Gas"
    
    if "Auto-Detect" in homeschool_focus:
        hs_instruction = "Look at the geography/history of the route and AUTO-SELECT the most relevant educational topic."
    else:
        hs_instruction = f"Focus on {homeschool_focus}."

    if live_search_enabled:
        live_instruction = f"""
        **CRITICAL INSTRUCTION: EXECUTE GOOGLE SEARCH.**
        You have access to the 'google_search' tool. You MUST use it to find:
        1. **SPECIFIC {fuel_type.upper()} PRICES:** Search for current {fuel_type} prices at the specific stations you recommend. 
        2. **Active road closures/alerts.**
        3. **Google Star Ratings.**
        """
    else:
        live_instruction = "Note: Live search unavailable."
    
    return f"""
    ### TRAVEL DAY BRIEFING PROMPT
    
    INPUT REQUIRED:
    Departure: {origin}
    Destination: {destination}
    Start Date: {dept_date}
    
    BRADLEY FAMILY CONTEXT (V4.0 PLAN):
    {BRADLEY_PLAN_CONTEXT}
    
    CURRENT CONTEXT:
    Rig: {tow_vehicle} ({fuel_type}) + {trailer_name} ({length}, {weight}).
    Fuel Economy: {mpg} MPG.
    
    YOUR TASK:
    {live_instruction}
    1. Calculate total mileage.
    2. Estimate Fuel Cost based on the LIVE prices found.
    3. Split the route into days based on {max_drive} hours driving.
    4. **EXPANDED OPTIONS:** For every Overnight, Lunch, and Sightseeing stop, provide **multiple options (3-5)** if valid candidates exist. Rank them.
    5. **RATINGS & PRICES:** Include Google Maps Star Rating AND the specific Fuel Price found.
    6. **OFFLINE NAVIGATION:** You MUST include the **GPS Coordinates** (Lat, Long) for every single stop.
    7. **HOMESCHOOL:** {hs_instruction}
    
    **FORMATTING REQUIREMENT:**
    - All links MUST be Markdown hyperlinks: [Map Link](URL)
    - GPS Coordinates must be visible next to the link.
    - Provide options as a numbered list.

    OUTPUT STRUCTURE (Markdown):

    ## 🛠️ PRE-DEPARTURE CHECKLIST (V4.0 Protocol)
    * **Impression 318RL:** Torque Lug Nuts (100-120 ft/lbs).
    * **Impression 318RL:** Check slide seals & roof.
    * **RAM 2500:** Check {fuel_type} level & Oil Monitor.
    * **Safety:** Confirm Winch/Recovery Gear is accessible.

    ## 🚦 LIVE DATA CHECK
    * **Active Alerts:** [List or "None"]
    * **Fuel Trend:** [e.g. Prices rising/falling in this region]

    ## 📊 Trip Overview
    | Metric | Estimate |
    | :--- | :--- |
    | **Total Distance** | [X] Miles |
    | **Total Days** | [X] Days |
    | **Avg {fuel_type} Price** | **$[X.XX]/gal** (Live Search Avg) |
    | **Est. Fuel Cost** | **$[X]** |
    *(Cost based on {mpg} MPG)*
    
    **Status:** GO / ⚠️ CAUTION
    **Route Map:** [Map Link](URL)

    ---
    (REPEAT FOR EACH DAY)

    ### 📅 DAY [X]: [Start] ➡️ [End]
    * **Date:** [Date]
    * **Stats:** [X] Miles | [X] Hours

    🌤️ **Weather** (Confidence: High/Med/Low)
    * Forecast: [AM/PM summary]

    📸 **Sightseeing & Leg-Stretchers**
    * **1.** [Name] (⭐ [Rating]) - [Map Link](URL) `[Lat, Long]`
        * *Why:* [Brief description]
    * **2.** [Name] (⭐ [Rating]) - [Map Link](URL) `[Lat, Long]`
    * **3.** [Name] (⭐ [Rating]) - [Map Link](URL) `[Lat, Long]`
    
    ⛽ **Fuel Strategy ({fuel_type})**
    * **1. (Best Price):** [Station Name] (**$[Price]**) - [Map Link](URL) `[Lat, Long]`
    * **2. (Easy Access):** [Station Name] (**$[Price]**) - [Map Link](URL) `[Lat, Long]`
    * **3. (Alternative):** [Station Name] (**$[Price]**) - [Map Link](URL) `[Lat, Long]`

    🍴 **Lunch Strategy (Slide-out Capable/Kid Friendly)**
    * **1.** [Name/Location] (⭐ [Rating]) - [Map Link](URL) `[Lat, Long]`
        * *Fit:* [Why it fits Bradley Family]
    * **2.** [Name/Location] (⭐ [Rating]) - [Map Link](URL) `[Lat, Long]`
    * **3.** [Name/Location] (⭐ [Rating]) - [Map Link](URL) `[Lat, Long]`

    🛌 **Overnight Options (Ranked by Suitability)**
    * **1. (Top Pick):** [Name] (⭐ [Rating]) - [Map Link](URL) `[Lat, Long]`
        * *Why:* [Thousand Trails match? / V4.0 Plan preference?]
    * **2.** [Name] (⭐ [Rating]) - [Map Link](URL) `[Lat, Long]`
    * **3.** [Name] (⭐ [Rating]) - [Map Link](URL) `[Lat, Long]`
    * **4.** [Name] (⭐ [Rating]) - [Map Link](URL) `[Lat, Long]`
    
    🎓 **Homeschool (Auto-Selected):** [Topic & Fact/Activity]

    ⚠️ **Hazards:** [Steep Grades / Truck Routes / Wind]

    ---
    """

# --- 7. ACTION BUTTON ---
st.markdown("###")
if st.button("🚀 Plan Multi-Day Trip", type="primary"):
    if not api_key:
        st.error("⚠️ API Key missing. Check sidebar.")
    elif not origin or not destination:
        st.warning("⚠️ Enter Departure and Destination.")
    else:
        status_box = st.status("📋 Initializing...", expanded=True)
        try:
            # --- NEW GENAI SDK INITIALIZATION ---
            client = genai.Client(api_key=api_key)
            
            # Use the MANUALLY SELECTED model from the Sidebar
            model_id = selected_model
            status_box.write(f"✅ Using Target Model: {model_id}")

            # Configure Search Tool
            generate_config = types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                response_modalities=["TEXT"]
            )
            
            prompt = generate_prompt(live_search_enabled=True)
            
            status_box.write("✍️ Executing Search & Streaming Results...")
            
            # --- STREAMING CALL ---
            result_container = st.empty()
            full_response = ""

            try:
                response_stream = client.models.generate_content_stream(
                    model=model_id,
                    contents=prompt,
                    config=generate_config
                )

                for chunk in response_stream:
                    if chunk.text:
                        full_response += chunk.text
                        result_container.markdown(full_response + "▌")
                
                result_container.markdown(full_response)
                status_box.update(label="✅ Briefing Complete!", state="complete", expanded=False)
                
                if full_response:
                    filename = f"Trip_Plan_{destination.replace(' ', '_')}_{datetime.date.today()}.md"
                    st.download_button(
                        label="📥 Download Plan (Offline)",
                        data=full_response,
                        file_name=filename,
                        mime="text/markdown"
                    )
            
            except Exception as e:
                # Catch 429 Errors explicitly
                if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                    status_box.update(label="⚠️ Traffic Limit Hit", state="error")
                    st.error("📉 High Traffic: Google's AI is busy. Please wait 60 seconds and try again, or try a shorter route.")
                elif "404" in str(e):
                    st.error(f"❌ Model Not Found: '{model_id}' rejected. Please select a different model in the sidebar.")
                else:
                    raise e

        except Exception as e:
            status_box.update(label="❌ System Error", state="error")
            st.error(f"Error details: {e}")
