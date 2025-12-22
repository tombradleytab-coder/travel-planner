import streamlit as st
import datetime
import google.generativeai as genai

# --- 1. APP CONFIGURATION ---
st.set_page_config(
    page_title="Bradley Planner v11.9 (Main Page View)", 
    page_icon="🚐", 
    layout="centered", 
    # CHANGED: Sidebar is now expanded by default, just in case
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
            }
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- 3. SIDEBAR: API KEY ONLY ---
with st.sidebar:
    st.header("🔐 App Settings")
    # Secure API Key Logic
    try:
        if "GOOGLE_API_KEY" in st.secrets:
            api_key = st.secrets["GOOGLE_API_KEY"]
            st.success("API Key Loaded")
        else:
            api_key = st.text_input("Gemini API Key", type="password")
    except Exception:
        api_key = st.text_input("Gemini API Key", type="password")
    
    st.info("Note: Vehicle settings have been moved to the main page for easier access.")

# --- 4. MAIN INTERFACE ---
st.title("Multi-Day Trip Planner v11.9")

# --- NEW: VEHICLE CONFIGURATION (MOVED TO MAIN PAGE) ---
# We use an expander that is OPEN (expanded=True) by default so you see it immediately.
with st.expander("🚐 Vehicle Configuration (Edit Here)", expanded=True):
    st.caption("Verify your rig details below:")
    
    # These are now on the main page, impossible to miss
    col_tow, col_trail = st.columns(2)
    with col_tow:
        tow_vehicle = st.text_input("Tow Vehicle", value="2023 RAM 2500 Rebel (Gas)", key="main_tow_v3")
    with col_trail:
        trailer_name = st.text_input("Trailer", value="2026 Impression 318RL", key="main_trailer_v3")
    
    col_specs1, col_specs2, col_specs3 = st.columns(3)
    with col_specs1:
        length = st.text_input("Length", value="39'", key="main_len_v3")
    with col_specs2:
        weight = st.text_input("Weight", value="~14k lbs", key="main_weight_v3")
    with col_specs3:
        mpg = st.number_input("Est. MPG", value=8.5, step=0.5, format="%.1f", key="main_mpg_v3")

# --- TRIP DETAILS ---
with st.container(border=True):
    st.subheader("📍 Route & Pace")
    
    origin = st.text_input("Departure Location", placeholder="e.g. North Bend, WA")
    destination = st.text_input("Final Destination", placeholder="e.g. Moab, UT")
    
    st.markdown("###")
    
    # Slider to control how many days the AI creates
    max_drive = st.slider("Max Driving Hours per Day", min_value=2, max_value=12, value=6, format="%d hrs")

    col_date, col_time = st.columns(2)
    with col_date:
        # Defaults to Tomorrow
        default_date = datetime.date.today() + datetime.timedelta(days=1)
        dept_date = st.date_input("Start Date", default_date)
    with col_time:
        # Defaults to 9:00 AM
        dept_time = st.time_input("Start Time", datetime.time(9, 0))

# --- PREFERENCES ---
with st.expander("🛠️ Strategy & Homeschool", expanded=False):
    c1, c2 = st.columns(2)
    with c1:
        pref_membership = st.checkbox("Thousand Trails/Harvest Hosts", value=True)
        pref_boondock = st.checkbox("Allow Boondocking", value=True)
    with c2:
        slide_out = st.checkbox("Lunch: Slide-out Capable", value=True)
        pref_luxury = st.checkbox("Luxury Break (Marriott/Amex)", value=True)
    
    st.divider()
    homeschool_focus = st.selectbox("Homeschool Focus for this Leg:", 
                                    ["General Knowledge", "Geology & Earth Science", "American History", "Wildlife Biology", "Engineering/Infrastructure"])

# --- 5. LOGIC ---
def generate_dynamic_prompt():
    return f"""
    ### TRAVEL DAY BRIEFING PROMPT (v11.9)
    Instructions: Generate a segmented multi-day briefing with MULTIPLE options for every stop.

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
    1. Calculate total mileage and ESTIMATED COST ($).
    2. Split the route into days based on {max_drive} hours driving.
    3. FOR EVERY STOP (Fuel & Lunch), provide 2 DISTINCT OPTIONS.
    4. Provide specific Google Maps links for ALL locations.

    OUTPUT STRUCTURE (Markdown):

    🚨 TRIP OVERVIEW & BUDGET
    * Total Distance: [X] Miles.
    * Total Days: [X].
    * 💰 Est. Fuel Cost: $[X] (Based on {mpg} mpg).
    * Status: GO / ⚠️ CAUTION.
    * 🗺️ Route Map: [Google Maps Link]

    ---
    (REPEAT FOR EACH DAY)

    ## 📅 DAY [X]: [Start] ➡️ [End]
    * Date: [Date]
    * Stats: [X] Miles | [X] Hours

    🌤️ WEATHER (Confidence: High/Med/Low)
    * Forecast: [AM/PM summary]

    ⛽ FUEL STRATEGY (2 Options)
    * Option 1 (Best Price): [Station Name] ($[Price]) - [Link]
    * Option 2 (Best Access/RV Lanes): [Station Name] - [Link]

    🍴 LUNCH STRATEGY (2 Options)
    * Option A (Slide-outs OK): [Name/Location] - [Link]
        * Why: [e.g. Scenic rest area, large park]
    * Option B (Restaurant/Fast): [Name/Location] - [Link]
        * Why: [e.g. Large lot, kid-friendly]

    🛌 OVERNIGHT (2 Options)
    * Option 1 (Preferred): [Name] - [Link].
        * Why: [e.g. Membership match].
    * Option 2 (Backup): [Name] - [Link].
        * Why: [e.g. Location].
    
    🎓 HOMESCHOOL ({homeschool_focus})
    * Lesson: [Fact/Activity related to {homeschool_focus}].

    🛣️ HAZARDS
    * [Steep Grades / Truck Routes / Wind / Parking Maneuver Analysis]

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
