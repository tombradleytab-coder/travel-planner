import streamlit as st
import datetime
import google.generativeai as genai

# --- 1. APP CONFIGURATION ---
st.set_page_config(
    page_title="Bradley Planner v12.1 (Mobile Optimized)", 
    page_icon="🚐", 
    layout="centered", 
    initial_sidebar_state="collapsed"
)

# --- 2. CUSTOM CSS ---
# This CSS removes extra white space to make it look tighter on mobile screens
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

# --- 3. SIDEBAR: API KEY ONLY ---
with st.sidebar:
    st.header("🔐 App Settings")
    try:
        if "GOOGLE_API_KEY" in st.secrets:
            api_key = st.secrets["GOOGLE_API_KEY"]
            st.success("API Key Loaded")
        else:
            api_key = st.text_input("Gemini API Key", type="password")
    except Exception:
        api_key = st.text_input("Gemini API Key", type="password")
    
    st.info("Vehicle settings are now on the main page.")

# --- 4. MAIN INTERFACE ---
st.title("Multi-Day Trip Planner v12.1")

# --- VEHICLE CONFIGURATION (Compact View) ---
with st.expander("🚐 Vehicle Config (Edit)", expanded=True):
    # Row 1: The Rig Names (Uses 2 columns)
    c1, c2 = st.columns(2)
    with c1:
        tow_vehicle = st.text_input("Tow Vehicle", value="2023 RAM 2500 Rebel (Gas)", key="tow_v5")
    with c2:
        trailer_name = st.text_input("Trailer", value="2026 Impression 318RL", key="trail_v5")
    
    # Row 2: The Specs (Uses 3 columns for mobile efficiency)
    c3, c4, c5 = st.columns(3)
    with c3:
        length = st.text_input("Length", value="39'", key="len_v5")
    with c4:
        weight = st.text_input("Weight", value="~14k lbs", key="wgt_v5")
    with c5:
        # Formatted clearly as a number
        mpg = st.number_input("MPG", value=8.5, step=0.5, format="%.1f", key="mpg_v5", help="Estimated towing MPG")

# --- TRIP DETAILS ---
with st.container(border=True):
    st.subheader("📍 Route & Pace")
    
    origin = st.text_input("Departure Location", placeholder="e.g. North Bend, WA")
    destination = st.text_input("Final Destination", placeholder="e.g. Moab, UT")
    
    st.markdown("###")
    
    max_drive = st.slider("Max Driving Hours per Day", min_value=2, max_value=12, value=6, format="%d hrs")

    c_date, c_time = st.columns(2)
    with c_date:
        default_date = datetime.date.today() + datetime.timedelta(days=1)
        dept_date = st.date_input("Start Date", default_date)
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
        pref_luxury = st.checkbox("Luxury Break", value=True)
    
    st.divider()
    homeschool_focus = st.selectbox("Homeschool Topic:", 
                                    ["General Knowledge", "Geology & Earth Science", "American History", "Wildlife Biology", "Engineering/Infrastructure"])

# --- 5. LOGIC ---
def generate_dynamic_prompt():
    return f"""
    ### TRAVEL DAY BRIEFING PROMPT (v12.1 Mobile Optimized)
    
    INPUT REQUIRED:
    Departure: {origin}
    Destination: {destination}
    Start Date: {dept_date}
    Start Time: {dept_time.strftime("%I:%M %p")}
    MAX DRIVING PER DAY: {max_drive} hours.

    CONTEXT:
    Rig: {tow_vehicle} + {trailer_name} ({length}, {weight}).
    Fuel Economy: {mpg} MPG (Use this to calculate fuel cost).
    
    PREFERENCES:
    - Accom: {'Thousand Trails/HH' if pref_membership else 'Public/Paid'} / {'Boondocking OK' if pref_boondock else 'No Boondocking'}.
    - Dining: Slide-outs {'Required' if slide_out else 'Not Required'}.
    - Homeschool Topic: {homeschool_focus}.

    YOUR TASK:
    1. Calculate total mileage.
    2. ESTIMATE COST: Calculate estimated fuel cost for the trip based on {mpg} MPG and average gas prices.
    3. Split the route into days based on {max_drive} hours driving.
    4. Provide specific Google Maps links for ALL stops.

    OUTPUT STRUCTURE (Markdown):

    ## 📊 Trip Overview
    | Metric | Estimate |
    | :--- | :--- |
    | **Total Distance** | [X] Miles |
    | **Total Days** | [X] Days |
    | **Est. Fuel Cost** | **$[X]** |
    *(Cost based on {mpg} MPG)*
    
    **Status:** GO / ⚠️ CAUTION
    **Route Map:** [Google Maps Link]

    ---
    (REPEAT FOR EACH DAY)

    ### 📅 DAY [X]: [Start] ➡️ [End]
    * **Date:** [Date]
    * **Stats:** [X] Miles | [X] Hours

    🌤️ **Weather** (Confidence: High/Med/Low)
    * Forecast: [AM/PM summary]

    ⛽ **Fuel Strategy**
    * **Option 1 (Price):** [Station Name] ($[Price]) - [Link]
    * **Option 2 (Access):** [Station Name] - [Link]

    🍴 **Lunch Strategy**
    * **Option A (Slide-outs):** [Name/Location] - [Link]
    * **Option B (Restaurant):** [Name/Location] - [Link]

    🛌 **Overnight Options**
    * **Option 1 (Preferred):** [Name] - [Link]
        * *Why:* [Reason]
    * **Option 2 (Backup):** [Name] - [Link]
    
    🎓 **Homeschool:** [Fact/Activity regarding {homeschool_focus}]

    ⚠️ **Hazards:** [Steep Grades / Truck Routes / Wind]

    ---
    """

# --- 6. ACTION BUTTON ---
st.markdown("###")
if st.button("🚀 Plan Multi-Day Trip", type="primary"):
    if not api_key:
        st.error("⚠️ API Key missing. Check sidebar.")
    elif not origin or not destination:
        st.warning("⚠️ Enter Departure and Destination.")
    else:
        status_box = st.status("📋 Planning & Calculating Costs...", expanded=True)
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-3-flash-preview')
            
            # Update status
            status_box.write(f"Analyzing route for {tow_vehicle}...")
            prompt = generate_dynamic_prompt()
            
            status_box.write("✍️ Drafting Itinerary...")
            response = model.generate_content(prompt)
            
            status_box.update(label="✅ Briefing Complete!", state="complete", expanded=False)
            
            # DISPLAY RESULT
            with st.container(border=True):
                st.markdown(response.text)

            # DOWNLOAD BUTTON (Offline Mode)
            filename = f"Trip_Plan_{destination.replace(' ', '_')}_{datetime.date.today()}.md"
            st.download_button(
                label="📥 Download Plan (Offline)",
                data=response.text,
                file_name=filename,
                mime="text/markdown"
            )
                
        except Exception as e:
            status_box.update(label="❌ Error", state="error")
            st.error(f"System Error: {e}")
