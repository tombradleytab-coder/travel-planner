import streamlit as st
import datetime
import google.generativeai as genai

# --- APP CONFIGURATION ---
st.set_page_config(page_title="Bradley Family Travel Planner", page_icon="🚐", layout="wide")

# --- SIDEBAR: SETTINGS & VEHICLE PROFILE ---
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Securely accept API Key
    api_key = st.text_input("Enter Google Gemini API Key", type="password", help="Get one at aistudio.google.com")
    
    st.divider()
    
    st.header("🚛 Vehicle Profile")
    # Defaults based on your specific trailer
    tow_vehicle = st.text_input("Tow Vehicle", value="2023 RAM 2500 Rebel (Gasoline)")
    trailer_name = st.text_input("Trailer", value="2026 Forest River Impression 318RL")
    
    col1, col2 = st.columns(2)
    with col1:
        length = st.text_input("Length", value="39'")
        height = st.text_input("Height", value="13'4\"")
    with col2:
        weight = st.text_input("Weight", value="~14k lbs")
        
    st.info(f"⚠️ Safety Limits Configured:\n- Wind >30mph\n- Temps <-10°F\n- Clearance <15'")

# --- MAIN PAGE: TRIP DETAILS ---
st.title("🚐 Travel Day Briefing Generator")
st.markdown("Generates a v11.0 briefing using **Gemini 3.0**.")

# 1. TRIP INPUTS
with st.container(border=True):
    st.subheader("1. Trip Details")
    col_a, col_b = st.columns(2)
    
    with col_a:
        origin = st.text_input("📍 Departure Location", placeholder="e.g., Whitefish RV Park, MT")
        dept_date = st.date_input("Departure Date", datetime.date.today())
        dept_time = st.time_input("Departure Time", datetime.time(14, 0)) # Default 2:00 PM
        
    with col_b:
        destination = st.text_input("🏁 Destination", placeholder="e.g., Red Mountain RV Park, Bozeman, MT")
        
# 2. PREFERENCES
with st.container(border=True):
    st.subheader("2. Preferences & Strategy")
    
    col_x, col_y = st.columns(2)
    
    with col_x:
        st.markdown("**Accommodation Priority**")
        pref_membership = st.checkbox("Thousand Trails / Harvest Hosts", value=True)
        pref_boondock = st.checkbox("Boondocking (Public Land/Cabela's)", value=True)
        pref_luxury = st.checkbox("Luxury Break (Marriott/Amex)", value=True)
        
    with col_y:
        st.markdown("**Dining Style**")
        slide_out = st.checkbox("Require 'Slide-out Capable' stops (Lunch)", value=True)
        rv_friendly = st.checkbox("RV-Friendly Restaurants (Large Lots)", value=True)
        
    st.markdown("**Homeschool & Fun**")
    include_homeschool = st.checkbox("Include History/Science Fact & Podcast", value=True)

# --- THE PROMPT GENERATOR ---
def generate_dynamic_prompt():
    # Constructing Section 1.1 based on User Input
    dynamic_inputs = f"""
    1.1 INPUT REQUIRED:
    Departure Location: {origin}
    Departure Date: {dept_date}
    Departure Time: {dept_time.strftime("%I:%M %p")}
    Destination: {destination}
    """
    
    # Constructing Section 1.2 based on Sidebar
    vehicle_context = f"""
    1.2 CONTEXT: Family Travel Profile
    Vehicle Setup:
    * Tow Vehicle: {tow_vehicle}
    * Trailer: {trailer_name} ({length} Long, {height} High, {weight}).
    Accommodation Preferences:
    {f"1. Memberships (Thousand Trails/Harvest Hosts)" if pref_membership else ""}
    {f"2. Boondocking" if pref_boondock else ""}
    {f"3. Luxury Break" if pref_luxury else ""}
    Dining Preferences:
    * Lunch: 11:30 AM - 1:30 PM.
    * Dinner: 5:00 PM - 6:30 PM.
    * Style: { "Scenic rest areas (Slide-out capable)" if slide_out else "Any" }, { "RV-friendly restaurants" if rv_friendly else "Any" }.
    Safety Limits:
    * ⚠️ EXTREME CAUTION if wind >30 mph or temps <-10°F.
    * ⚠️ Flag clearances <15' (RV is {height}).
    """

    # The Static Instructions
    static_instructions = """
    1.3 YOUR TASK:
    Act as an expert travel logistics planner. Generate a comprehensive Travel Day Briefing optimized for mobile viewing.
    You must browse the web to find real-time weather, current gas prices, and specific dining/stop options matching the family profile.
    
    1.4 OUTPUT STRUCTURE:
    Provide a structured output with:
    1.4.1 EXECUTIVE SUMMARY (Status: GO/CAUTION, Route Map Link)
    1.4.2 ROUTE OVERVIEW (Miles, Time, Fuel Needed, Overnight Stop if >5hrs)
    1.4.3 WEATHER & WIND (Hourly forecast, Pass conditions, Confidence)
    1.4.4 FUEL & MEAL STRATEGY (Best prices, Slide-out friendly stops for lunch)
    1.4.5 OVERNIGHT RECOMMENDATIONS (If needed)
    1.4.6 HAZARDS (Truck network, grades, wildlife)
    1.4.7 HOMESCHOOL & FUN (Podcast, Science fact, Playground)
    1.4.8 PRE-DEPARTURE CHECKLIST
    1.4.9 ARRIVAL DETAILS (Sunset vs Arrival time)
    
    Ensure all advice considers the specific vehicle length (39') and weight (~14k lbs).
    """
    
    return dynamic_inputs + "\n" + vehicle_context + "\n" + static_instructions

# --- ACTION BUTTON ---
if st.button("🚀 Generate Briefing", type="primary"):
    if not api_key:
        st.error("Please enter your Google Gemini API Key in the sidebar.")
    else:
        if not origin or not destination:
            st.warning("Please enter both Departure and Destination.")
        else:
            with st.spinner("Analyzing route, weather, and campgrounds..."):
                try:
                    # 1. Configure the AI
                    genai.configure(api_key=api_key)
                    
                    # 2. Select the Model (UPDATED FOR GEMINI 3.0)
                    # 'gemini-3-flash-preview' is the high-speed standard for 2025.
                    model = genai.GenerativeModel('gemini-3-flash-preview')
                    
                    # 3. Construct the prompt
                    final_prompt = generate_dynamic_prompt()
                    
                    # 4. Send to AI
                    response = model.generate_content(final_prompt)
                    
                    # 5. Display Result
                    st.success("Briefing Generated!")
                    st.markdown("---")
                    st.markdown(response.text)
                    
                except Exception as e:
                    st.error(f"An error occurred: {e}")
