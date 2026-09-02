import streamlit as st
import pandas as pd
import numpy as np
import folium
import re
from streamlit_folium import st_folium
from math import radians, cos, sin, asin, sqrt

# --- Page Setup & Theme Branding ---
st.set_page_config(
    page_title="South & West India EV Network Dashboard",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Dark Navy #0B0F19, Voltran Electric Green #10B981, Glassmorphic Cards)
st.markdown("""
    <style>
    .main {
        background-color: #0B0F19;
        color: #F8FAFC;
    }
    .stMetric {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }
    .stMetric label {
        color: #94A3B8 !important;
        font-weight: 600;
    }
    .stMetric div[data-testid="stMetricValue"] {
        color: #10B981 !important;
        font-weight: 700;
    }
    </style>
""", unsafe_allow_html=True)

# --- Distance Calculation (Haversine Formula in km) ---
def haversine(lat1, lon1, lat2, lon2):
    r = 6371.0 # Radius of earth in kilometers
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return 2 * r * asin(sqrt(a))

# --- Comprehensive Dataset with Operational & Upcoming Hubs ---
@st.cache_data
def load_data():
    return pd.DataFrame([
        # ==========================================
        # 1. TELANGANA
        # ==========================================
        # Voltran Operational
        {"name": "Voltran - Madhapur Hub", "provider": "Voltran", "state": "Telangana", "status": "Operational", "lat": 17.4461, "lon": 78.3983, "corridor": "Hyderabad Urban", "kw": "60kW DC", "address": "Road No. 9, Kakatiya Hills, Madhapur, Hyderabad"},
        {"name": "Voltran - Suryapet Hub 1 (NH65)", "provider": "Voltran", "state": "Telangana", "status": "Operational", "lat": 17.1438, "lon": 79.6238, "corridor": "NH65 (Hyd-Vja)", "kw": "60kW DC", "address": "Rayangudem, Suryapet, Telangana"},
        {"name": "Voltran - Suryapet 2 Hub", "provider": "Voltran", "state": "Telangana", "status": "Operational", "lat": 17.1510, "lon": 79.6350, "corridor": "NH65 (Hyd-Vja)", "kw": "60kW DC", "address": "Rayangudem, Pillala Marri Rural, Telangana 508376"},
        {"name": "Voltran - Shamshabad Hub", "provider": "Voltran", "state": "Telangana", "status": "Operational", "lat": 17.2543, "lon": 78.4312, "corridor": "NH44 / ORR", "kw": "60kW DC", "address": "Shamshabad Junction, Hyderabad"},
        {"name": "Voltran - Nizamabad Hub", "provider": "Voltran", "state": "Telangana", "status": "Operational", "lat": 18.6725, "lon": 78.0941, "corridor": "NH44 North", "kw": "60kW DC", "address": "Nizamabad NH44 Bypass, Telangana"},
        {"name": "Voltran - Beechupalli Hub", "provider": "Voltran", "state": "Telangana", "status": "Operational", "lat": 16.1423, "lon": 77.9256, "corridor": "NH44 South", "kw": "60kW DC", "address": "Near Beechupalli Temple, NH44"},
        {"name": "Voltran - Miryalaguda Hub", "provider": "Voltran", "state": "Telangana", "status": "Operational", "lat": 16.8760, "lon": 79.5630, "corridor": "Miryalaguda Bypass", "kw": "60kW DC", "address": "Miryalaguda Bypass Rd, Telangana"},
        {"name": "Voltran - Nallagandla Hub", "provider": "Voltran", "state": "Telangana", "status": "Operational", "lat": 17.4851, "lon": 78.3090, "corridor": "Hyderabad West", "kw": "60kW DC", "address": "Nallagandla, Hyderabad, Telangana"},
        
        # Voltran Upcoming (From Voltran.in/#locations)
        {"name": "Voltran - Aziz Nagar / Aushapur Hub", "provider": "Voltran", "state": "Telangana", "status": "Upcoming", "lat": 17.3481, "lon": 78.2519, "corridor": "Warangal Highway / Aziz Nagar", "kw": "60kW DC", "address": "FP7V+JM2, Aushapur, Telangana 501301"},
        {"name": "Voltran - Ramoji Film City Charge Hub", "provider": "Voltran", "state": "Telangana", "status": "Upcoming", "lat": 17.3117, "lon": 78.6811, "corridor": "NH65 Vijayawada Highway", "kw": "60kW DC", "address": "Abdullahpurmet, Vijayawada Highway, Hyderabad 501512"},

        # Partner Operational
        {"name": "Tata Power - Somajiguda Greenlands", "provider": "Tata Power", "state": "Telangana", "status": "Operational", "lat": 17.4328, "lon": 78.4583, "corridor": "Hyderabad Urban", "kw": "30kW DC", "address": "Begumpet Rd, Somajiguda, Hyderabad"},
        {"name": "Tata Power - LB Nagar Metro", "provider": "Tata Power", "state": "Telangana", "status": "Operational", "lat": 17.3512, "lon": 78.5521, "corridor": "NH65 Exit", "kw": "50kW DC", "address": "LB Nagar Ring Rd, Hyderabad"},
        {"name": "Statiq - Courtyard Marriott (Tankbund)", "provider": "Statiq", "state": "Telangana", "status": "Operational", "lat": 17.4180, "lon": 78.4810, "corridor": "Hyderabad Central", "kw": "60kW DC", "address": "Lower Tank Bund Rd, Hyderabad"},
        {"name": "ChargeZone - Medak Rimmanguda", "provider": "ChargeZone", "state": "Telangana", "status": "Operational", "lat": 17.8420, "lon": 78.4610, "corridor": "NH44 North", "kw": "60kW DC", "address": "Rimmanguda NH44, Medak District"},
        {"name": "Jio-bp pulse - ORR Ghatkesar", "provider": "Jio-bp pulse", "state": "Telangana", "status": "Operational", "lat": 17.4520, "lon": 78.6810, "corridor": "Outer Ring Road", "kw": "60kW DC", "address": "Ghatkesar Toll Plaza Exit, Hyderabad"},

        # Partner Upcoming
        {"name": "Tata Power - Karimnagar Highway Plaza", "provider": "Tata Power", "state": "Telangana", "status": "Upcoming", "lat": 18.4386, "lon": 79.1288, "corridor": "State Highway 1", "kw": "60kW Fast DC", "address": "Karimnagar Bypass Rd, Telangana"},
        {"name": "Statiq - Cyber Towers Hub", "provider": "Statiq", "state": "Telangana", "status": "Upcoming", "lat": 17.4504, "lon": 78.3811, "corridor": "HITEC City", "kw": "60kW DC", "address": "HITEC City Main Rd, Madhapur, Hyderabad"},

        # ==========================================
        # 2. ANDHRA PRADESH
        # ==========================================
        # Voltran Operational
        {"name": "Voltran - Tirupati Charge Hub", "provider": "Voltran", "state": "Andhra Pradesh", "status": "Operational", "lat": 13.6288, "lon": 79.4192, "corridor": "NH71 / Rayalaseema", "kw": "60kW DC", "address": "Tirumala Bypass Rd, Srinivasa Nagar, Tirupati 517501"},
        {"name": "Voltran - Srikakulam Hub", "provider": "Voltran", "state": "Andhra Pradesh", "status": "Operational", "lat": 18.2969, "lon": 83.8968, "corridor": "NH16 North Coast", "kw": "60kW DC", "address": "Survey 75/25A, NH16, Kushalapuram, Srikakulam 532001"},
        {"name": "Voltran - Rajahmundry Hub", "provider": "Voltran", "state": "Andhra Pradesh", "status": "Operational", "lat": 17.0005, "lon": 81.7800, "corridor": "NH16 Mid Coast", "kw": "60kW DC", "address": "Samalkota Rd Junction, Rajanagaram 533294"},
        {"name": "Voltran - Ongole Charge Hub", "provider": "Voltran", "state": "Andhra Pradesh", "status": "Operational", "lat": 15.5057, "lon": 80.0499, "corridor": "NH16 South Coast", "kw": "60kW DC", "address": "G3P2+J7H, Mukthinutala Padu Rural 523225"},
        {"name": "Voltran - Nellore Charge Hub", "provider": "Voltran", "state": "Andhra Pradesh", "status": "Operational", "lat": 14.4426, "lon": 79.9865, "corridor": "NH16 South Coast", "kw": "60kW DC", "address": "7WX4+9R, Kanupur Bit-II at Chowtapalem"},
        {"name": "Voltran - Mydukur Charge Hub", "provider": "Voltran", "state": "Andhra Pradesh", "status": "Operational", "lat": 14.7833, "lon": 78.6000, "corridor": "NH40 Rayalaseema", "kw": "60kW DC", "address": "PP3R+8M9, Mydukur Bypass Rd, Bhumayapalle 516172"},
        {"name": "Voltran - Anantapur Hub", "provider": "Voltran", "state": "Andhra Pradesh", "status": "Operational", "lat": 14.6819, "lon": 77.6006, "corridor": "NH44 South", "kw": "60kW DC", "address": "Rudrampeta NH44 Bypass, Kakalapalli 515004"},
        {"name": "Voltran - Kakinada Charge Hub", "provider": "Voltran", "state": "Andhra Pradesh", "status": "Operational", "lat": 16.9891, "lon": 82.2475, "corridor": "Kakinada Coast", "kw": "60kW DC", "address": "Achampeta Junction, Thimmapuram 533005"},
        {"name": "Voltran - Gannavaram Hub", "provider": "Voltran", "state": "Andhra Pradesh", "status": "Operational", "lat": 16.5388, "lon": 80.7961, "corridor": "NH16 Airport Line", "kw": "60kW DC", "address": "1-63/1, NH5, Kesarapalle 521102"},
        {"name": "Voltran - Gollapudi Hub", "provider": "Voltran", "state": "Andhra Pradesh", "status": "Operational", "lat": 16.5412, "lon": 80.5780, "corridor": "NH65 Vijayawada", "kw": "60kW DC", "address": "NH65 Nallakunta, Gollapudi 521225"},
        {"name": "Voltran - Amaravati Hub", "provider": "Voltran", "state": "Andhra Pradesh", "status": "Operational", "lat": 16.3520, "lon": 80.5283, "corridor": "Capital Belt / NH65", "kw": "60kW DC", "address": "9GQP+5Q8, Kaza, Andhra Pradesh"},
        {"name": "Voltran - Machilipatnam Hub", "provider": "Voltran", "state": "Andhra Pradesh", "status": "Operational", "lat": 16.1812, "lon": 81.1320, "corridor": "Machilipatnam Coast", "kw": "60kW DC", "address": "643P+7W9, Machilipatnam, Andhra Pradesh"},

        # Voltran Upcoming (From Voltran.in/#locations)
        {"name": "Voltran - Chittoor Charge Hub", "provider": "Voltran", "state": "Andhra Pradesh", "status": "Upcoming", "lat": 13.2172, "lon": 79.1003, "corridor": "Bengaluru - Tirupati Hwy", "kw": "60kW DC", "address": "Bengaluru - Tirupati Hwy, Varigapalle, Kukkalapalle 517128"},

        # Partner Operational
        {"name": "Tata Power - Tadepalle (Vijayawada)", "provider": "Tata Power", "state": "Andhra Pradesh", "status": "Operational", "lat": 16.4821, "lon": 80.6012, "corridor": "NH16 Mid Coast", "kw": "50kW DC", "address": "Tadepalle Bypass, Vijayawada"},
        {"name": "Tata Power - Vempadu (Visakhapatnam)", "provider": "Tata Power", "state": "Andhra Pradesh", "status": "Operational", "lat": 17.5510, "lon": 82.8800, "corridor": "NH16 North Coast", "kw": "60kW DC", "address": "Vempadu Highway Plaza, Vizag"},
        {"name": "Jio-bp pulse - Tanguturu (Ongole)", "provider": "Jio-bp pulse", "state": "Andhra Pradesh", "status": "Operational", "lat": 15.3420, "lon": 80.0210, "corridor": "NH16 South Coast", "kw": "60kW DC", "address": "Tanguturu Toll Plaza NH16"},

        # Partner Upcoming
        {"name": "Tata Power - Kadapa Apparajupet", "provider": "Tata Power", "state": "Andhra Pradesh", "status": "Upcoming", "lat": 14.4715, "lon": 78.8210, "corridor": "NH40 Rayalaseema", "kw": "50kW DC", "address": "Apparajupet Bypass, Kadapa"},
        {"name": "Zeon - Kurnool Highway Hub", "provider": "Zeon Charging", "state": "Andhra Pradesh", "status": "Upcoming", "lat": 15.8281, "lon": 78.0373, "corridor": "NH44 Hyd-Blr", "kw": "120kW Dual DC", "address": "Kurnool NH44 Highway Plaza"},

        # ==========================================
        # 3. KARNATAKA
        # ==========================================
        {"name": "Zeon - Hosur Road (Bengaluru)", "provider": "Zeon Charging", "state": "Karnataka", "status": "Operational", "lat": 12.8920, "lon": 77.6410, "corridor": "NH44 (Blr-TN Border)", "kw": "120kW Dual DC", "address": "Hosur Main Rd, Bommanahalli, Bengaluru"},
        {"name": "Zeon - Mysuru Expressway Hub", "provider": "Zeon Charging", "state": "Karnataka", "status": "Operational", "lat": 12.4200, "lon": 76.8120, "corridor": "Blr-Mysuru Exp", "kw": "60kW DC", "address": "Bidadi Plaza, Mysuru Highway"},
        {"name": "Tata Power - Electronic City Phase 1", "provider": "Tata Power", "state": "Karnataka", "status": "Operational", "lat": 12.8452, "lon": 77.6602, "corridor": "Bengaluru IT Belt", "kw": "50kW DC", "address": "Electronic City, Hosur Rd, Bengaluru"},
        {"name": "Statiq - UB City (JW Marriott)", "provider": "Statiq", "state": "Karnataka", "status": "Operational", "lat": 12.9712, "lon": 77.5955, "corridor": "Bengaluru Central", "kw": "60kW DC", "address": "Vittal Mallya Rd, Ashok Nagar, Bengaluru"},
        {"name": "Ather Grid - Hebbal Expressway", "provider": "Ather Grid", "state": "Karnataka", "status": "Operational", "lat": 13.0358, "lon": 77.5970, "corridor": "NH44 Airport Line", "kw": "Fast DC Grid", "address": "Hebbal Flyover Junction, Bengaluru"},
        {"name": "ChargeZone - Hubballi Bypass", "provider": "ChargeZone", "state": "Karnataka", "status": "Operational", "lat": 15.3647, "lon": 75.1240, "corridor": "NH48 (Blr-Pune)", "kw": "60kW DC", "address": "Hubballi NH48 Bypass, Karnataka"},

        # Partner Upcoming
        {"name": "Statiq - Mangaluru Airport Road", "provider": "Statiq", "state": "Karnataka", "status": "Upcoming", "lat": 12.9141, "lon": 74.8560, "corridor": "Coastal Highway", "kw": "60kW DC", "address": "Bajpe Airport Rd, Mangaluru"},
        {"name": "Tata Power - Tumakuru Industrial Hub", "provider": "Tata Power", "state": "Karnataka", "status": "Upcoming", "lat": 13.3409, "lon": 77.1006, "corridor": "NH48 North", "kw": "60kW DC", "address": "Tumakuru Industrial Area"},

        # ==========================================
        # 4. MAHARASHTRA
        # ==========================================
        {"name": "ChargeZone - BKC Financial Center", "provider": "ChargeZone", "state": "Maharashtra", "status": "Operational", "lat": 19.0657, "lon": 72.8686, "corridor": "Mumbai Central", "kw": "120kW Fast DC", "address": "Bandra Kurla Complex, Mumbai"},
        {"name": "Tata Power - Vashi Sector 17", "provider": "Tata Power", "state": "Maharashtra", "status": "Operational", "lat": 19.0770, "lon": 72.9980, "corridor": "Navi Mumbai", "kw": "50kW DC", "address": "Sector 17, Vashi, Navi Mumbai"},
        {"name": "Statiq - Lonavala Expressway Food Plaza", "provider": "Statiq", "state": "Maharashtra", "status": "Operational", "lat": 18.7557, "lon": 73.4091, "corridor": "Mumbai-Pune Exp", "kw": "60kW DC", "address": "Mumbai-Pune Expressway, Lonavala"},
        {"name": "GLIDA - Hinjewadi IT Park", "provider": "GLIDA", "state": "Maharashtra", "status": "Operational", "lat": 18.5912, "lon": 73.7389, "corridor": "Pune Tech Corridor", "kw": "60kW DC", "address": "Phase 1, Hinjewadi, Pune"},
        {"name": "Jio-bp pulse - Kolhapur NH48", "provider": "Jio-bp pulse", "state": "Maharashtra", "status": "Operational", "lat": 16.7050, "lon": 74.2433, "corridor": "NH48 (Pune-Blr)", "kw": "60kW DC", "address": "Kolhapur Highway Plaza, NH48"},
        
        # Partner Upcoming
        {"name": "Tata Power - Samruddhi Mahamarg Corridor", "provider": "Tata Power", "state": "Maharashtra", "status": "Upcoming", "lat": 19.8762, "lon": 75.3433, "corridor": "Nagpur-Mumbai Expressway", "kw": "120kW Dual DC", "address": "Chhatrapati Sambhaji Nagar Exit"},
        {"name": "ChargeZone - Navi Mumbai Airport Zone", "provider": "ChargeZone", "state": "Maharashtra", "status": "Upcoming", "lat": 18.9892, "lon": 73.0720, "corridor": "NMIA Expressway", "kw": "120kW Fast DC", "address": "Ulwe, Navi Mumbai"},

        # ==========================================
        # 5. TAMIL NADU
        # ==========================================
        {"name": "Zeon - Sriperumbudur Highway", "provider": "Zeon Charging", "state": "Tamil Nadu", "status": "Operational", "lat": 12.9690, "lon": 79.9410, "corridor": "NH48 (Blr-Chennai)", "kw": "120kW Dual DC", "address": "Sriperumbudur NH48 Plaza, Tamil Nadu"},
        {"name": "Zeon - Ulundurpet Highway Hub", "provider": "Zeon Charging", "state": "Tamil Nadu", "status": "Operational", "lat": 11.6912, "lon": 79.2900, "corridor": "NH45 (Chennai-Trichy)", "kw": "60kW DC", "address": "Ulundurpet Toll Plaza, NH45"},
        {"name": "Tata Power - Guindy Metro", "provider": "Tata Power", "state": "Tamil Nadu", "status": "Operational", "lat": 13.0067, "lon": 80.2020, "corridor": "Chennai South", "kw": "50kW DC", "address": "Guindy Metro Parking, Chennai"},
        {"name": "Statiq - Shenoy Nagar Metro", "provider": "Statiq", "state": "Tamil Nadu", "status": "Operational", "lat": 13.0780, "lon": 80.2250, "corridor": "Chennai Central", "kw": "60kW DC", "address": "Shenoy Nagar Metro Station, Chennai"},
        {"name": "ChargeZone - Avinashi Road (Coimbatore)", "provider": "ChargeZone", "state": "Tamil Nadu", "status": "Operational", "lat": 11.0280, "lon": 77.0120, "corridor": "Coimbatore Axis", "kw": "60kW DC", "address": "Avinashi Rd, Peelamedu, Coimbatore"},

        # Partner Upcoming
        {"name": "Zeon - Salem Highway Junction", "provider": "Zeon Charging", "state": "Tamil Nadu", "status": "Upcoming", "lat": 11.6643, "lon": 78.1460, "corridor": "NH44 Salem Axis", "kw": "120kW Dual DC", "address": "Salem NH44 Expressway Hub"},
        {"name": "Tata Power - Trichy Airport Road", "provider": "Tata Power", "state": "Tamil Nadu", "status": "Upcoming", "lat": 10.7654, "lon": 78.7090, "corridor": "NH38 Central Axis", "kw": "60kW DC", "address": "Trichy Airport Road Plaza"}
    ])

df = load_data()

# --- National Highway Tagging ---
def extract_highway(corridor):
    """Pulls a clean 'NH65' style tag out of a messy corridor string.
    Returns None for corridors that aren't tagged to a numbered NH
    (local/urban hubs, named expressways, state highways)."""
    match = re.search(r'NH\s*-?\s*(\d+)', str(corridor), re.IGNORECASE)
    return f"NH{match.group(1)}" if match else None

df['highway'] = df['corridor'].apply(extract_highway)

# --- Order stations along a highway using geographic distance from one end ---
@st.cache_data
def order_along_highway(hw_df):
    hw_df = hw_df.reset_index(drop=True).copy()
    if len(hw_df) < 2:
        hw_df['position_km'] = 0.0
        return hw_df
    # Find the two most geographically distant stations -> treat as the
    # two "ends" of the highway stretch covered by this dataset.
    max_dist, anchor_idx = -1, 0
    for i in range(len(hw_df)):
        for j in range(i + 1, len(hw_df)):
            d = haversine(hw_df.loc[i, 'lat'], hw_df.loc[i, 'lon'],
                          hw_df.loc[j, 'lat'], hw_df.loc[j, 'lon'])
            if d > max_dist:
                max_dist, anchor_idx = d, i
    anchor = hw_df.loc[anchor_idx]
    hw_df['position_km'] = hw_df.apply(
        lambda r: haversine(anchor['lat'], anchor['lon'], r['lat'], r['lon']), axis=1
    )
    return hw_df.sort_values('position_km').reset_index(drop=True)

# --- Provider Color Palette ---
PROVIDER_COLORS = {
    "Voltran": "green",
    "Tata Power": "blue",
    "Statiq": "darkgreen",
    "Zeon Charging": "cadetblue",
    "ChargeZone": "purple",
    "Jio-bp pulse": "red",
    "GLIDA": "orange",
    "Ather Grid": "darkred"
}

# --- Distance Calculation Matrix ---
def compute_nearest_neighbors(dataset):
    if len(dataset) < 2:
        return pd.DataFrame()
    results = []
    for i, row in dataset.iterrows():
        distances = []
        for j, target in dataset.iterrows():
            if i != j:
                dist = haversine(row['lat'], row['lon'], target['lat'], target['lon'])
                distances.append((target['name'], target['provider'], target['state'], target['status'], dist))
        distances.sort(key=lambda x: x[4])
        results.append({
            "Station": row['name'],
            "Provider": row['provider'],
            "State": row['state'],
            "Status": row['status'],
            "Nearest Neighbor": distances[0][0],
            "Nearest Provider": distances[0][1],
            "Neighbor Status": distances[0][3],
            "Distance to Next Station (km)": round(distances[0][4], 1)
        })
    return pd.DataFrame(results)

# --- Sidebar Controls ---
st.sidebar.image("https://www.voltran.in/assets/img/logo.png", width=180)
st.sidebar.markdown("---")
st.sidebar.title("🎛️ Search & Filters")

# Search Bar
search_query = st.sidebar.text_input("🔎 Search by City, Station, or Address:", "")

# Status Filter Options
status_option = st.sidebar.radio(
    "⚡ Station Deployment Status:",
    options=["All Stations", "Operational Only", "Upcoming / Coming Soon Only"],
    index=0
)

# State Multi-Select
all_states = sorted(list(df['state'].unique()))
selected_states = st.sidebar.multiselect("Filter by State:", options=all_states, default=all_states)

# Provider Multi-Select
all_providers = sorted(list(PROVIDER_COLORS.keys()))
selected_providers = st.sidebar.multiselect("Filter by EV Provider:", options=all_providers, default=all_providers)

# Map Style Selector
map_theme = st.sidebar.selectbox(
    "Map Visual Theme:",
    options=["Dark Canvas (CartoDB Dark)", "Light / Clean (CartoDB Voyager)", "OpenStreetMap"],
    index=0
)

# Filtering Data
filtered_df = df[(df['state'].isin(selected_states)) & (df['provider'].isin(selected_providers))].reset_index(drop=True)

if status_option == "Operational Only":
    filtered_df = filtered_df[filtered_df['status'] == "Operational"].reset_index(drop=True)
elif status_option == "Upcoming / Coming Soon Only":
    filtered_df = filtered_df[filtered_df['status'] == "Upcoming"].reset_index(drop=True)

if search_query:
    filtered_df = filtered_df[
        filtered_df['name'].str.contains(search_query, case=False) | 
        filtered_df['address'].str.contains(search_query, case=False) |
        filtered_df['corridor'].str.contains(search_query, case=False)
    ].reset_index(drop=True)

# --- Header & Metrics ---
st.title("⚡ Multi-Provider EV Network Dashboard")
st.markdown("Track operational stations alongside **upcoming / coming soon EV hubs** across **Voltran, Tata Power, Statiq, Zeon, ChargeZone, Jio-bp, and Ather**.")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Visible Stations", len(filtered_df))
m2.metric("Operational Stations", len(filtered_df[filtered_df['status'] == 'Operational']))
m3.metric("Upcoming / Coming Soon", len(filtered_df[filtered_df['status'] == 'Upcoming']))
m4.metric("Voltran Hubs (All)", len(filtered_df[filtered_df['provider'] == 'Voltran']))

# --- Interactive Map ---
st.subheader("📍 Interactive EV Charging Station Map")

# Map Legend Note
st.markdown("""
<div style="margin-bottom: 10px;">
    <b>Map Indicators:</b> 
    <span style="color:#10B981; font-weight:bold;">📍 Solid Pins = Active / Operational Hubs</span> &nbsp;|&nbsp;
    <span style="color:orange; font-weight:bold;">⭐ Orange Stars = Upcoming / Coming Soon Hubs</span>
</div>
""", unsafe_allow_html=True)

# Map Tile Selection
tile_provider = "CartoDB dark_matter"
if "Voyager" in map_theme:
    tile_provider = "CartoDB voyager"
elif "OpenStreetMap" in map_theme:
    tile_provider = "OpenStreetMap"

m = folium.Map(location=[15.2, 77.5], zoom_start=6, tiles=tile_provider)

for _, row in filtered_df.iterrows():
    base_color = PROVIDER_COLORS.get(row['provider'], 'gray')
    
    # Custom icon for upcoming vs operational
    if row['status'] == "Upcoming":
        icon_type = folium.Icon(color="orange", icon="star", prefix="fa")
        status_tag = "<span style='color:orange; font-weight:bold;'>⭐ COMING SOON</span>"
    else:
        icon_type = folium.Icon(color=base_color, icon="bolt", prefix="fa")
        status_tag = "<span style='color:#10B981; font-weight:bold;'>🟢 OPERATIONAL</span>"
    
    popup_content = f"""
    <div style='font-family: Arial, sans-serif; width: 220px;'>
        <h4 style='margin-bottom: 5px; color: #10B981;'>{row['name']}</h4>
        <b>Status:</b> {status_tag}<br>
        <b>Provider:</b> {row['provider']}<br>
        <b>State:</b> {row['state']}<br>
        <b>Capacity:</b> {row['kw']}<br>
        <b>Address:</b> {row['address']}<br>
    </div>
    """
    
    folium.Marker(
        location=[row['lat'], row['lon']],
        popup=folium.Popup(popup_content, max_width=250),
        tooltip=f"{row['provider']} ({row['status']}): {row['name']}",
        icon=icon_type
    ).add_to(m)

st_folium(m, width=1300, height=520)

# --- Analysis Tabs ---
tab1, tab2, tab3 = st.tabs([
    "📏 Distance to Next Charging Station",
    "📋 Full Searchable Directory",
    "🛣️ Highway Corridor View"
])

with tab1:
    st.subheader("Inter-Station Proximity & Next Station Distance Analysis")
    st.markdown("Calculates the exact distance (in km) from every selected station to its nearest neighboring charger.")
    nn_df = compute_nearest_neighbors(filtered_df)
    if not nn_df.empty:
        st.dataframe(nn_df, use_container_width=True)
    else:
        st.info("Select at least 2 stations to calculate distances.")

with tab2:
    st.subheader("Searchable Station Directory by State & Network")
    st.dataframe(filtered_df[['name', 'provider', 'state', 'status', 'corridor', 'kw', 'address', 'lat', 'lon']], use_container_width=True)

with tab3:
    st.subheader("🛣️ Plan Your Route on a Single National Highway")
    st.markdown(
        "Pick a highway to see every charging station along it, in order. "
        "Click a marker to see the next station in **both directions**, how far it is, "
        "and everything you need for the leg ahead."
    )

    available_highways = sorted(df['highway'].dropna().unique())

    if not available_highways:
        st.info("No stations in the current dataset are tagged to a numbered national highway.")
    else:
        selected_highway = st.selectbox("Choose a National Highway:", options=available_highways)

        hw_df = df[df['highway'] == selected_highway]
        hw_df = order_along_highway(hw_df)
        total_on_highway = len(hw_df)

        st.markdown(
            f"**{selected_highway}** has **{total_on_highway} charging station(s)** in this dataset, "
            f"spanning roughly **{hw_df['position_km'].max():.0f} km** end to end."
        )

        # --- Highway Map: markers in travel order, connected by a route line ---
        hw_center_lat = hw_df['lat'].mean()
        hw_center_lon = hw_df['lon'].mean()
        hm = folium.Map(location=[hw_center_lat, hw_center_lon], zoom_start=7, tiles="CartoDB dark_matter")

        route_points = list(zip(hw_df['lat'], hw_df['lon']))
        folium.PolyLine(route_points, color="#10B981", weight=3, opacity=0.6, dash_array="6").add_to(hm)

        for idx, row in hw_df.iterrows():
            is_upcoming = row['status'] == "Upcoming"
            icon_type = folium.Icon(
                color="orange" if is_upcoming else PROVIDER_COLORS.get(row['provider'], 'gray'),
                icon="star" if is_upcoming else "bolt",
                prefix="fa"
            )
            folium.Marker(
                location=[row['lat'], row['lon']],
                tooltip=row['name'],
                popup=f"Stop {idx + 1} of {total_on_highway} on {selected_highway}",
                icon=icon_type
            ).add_to(hm)

        hw_map_data = st_folium(hm, width=1300, height=520, key=f"highway_map_{selected_highway}")

        # --- Detail panel for the clicked station ---
        clicked_name = None
        if hw_map_data and hw_map_data.get("last_object_clicked_tooltip"):
            clicked_name = hw_map_data["last_object_clicked_tooltip"]

        if clicked_name and clicked_name in hw_df['name'].values:
            pos = hw_df.index[hw_df['name'] == clicked_name][0]
            station = hw_df.loc[pos]

            st.markdown("---")
            st.markdown(f"### 📍 {station['name']}  &nbsp; <span style='font-size:14px; color:#94A3B8;'>(Stop {pos + 1} of {total_on_highway} on {selected_highway})</span>", unsafe_allow_html=True)

            c1, c2, c3 = st.columns(3)

            # Previous station (toward the anchor / one direction)
            with c1:
                st.markdown("**⬅️ Previous Station**")
                if pos > 0:
                    prev = hw_df.loc[pos - 1]
                    dist = station['position_km'] - prev['position_km']
                    st.markdown(f"**{prev['name']}**")
                    st.markdown(f"📏 {dist:.1f} km away")
                    st.markdown(f"⚡ {prev['kw']} · {prev['provider']}")
                    st.markdown(f"🟢 {prev['status']}" if prev['status'] == "Operational" else f"⭐ {prev['status']}")
                else:
                    st.markdown("_This is the first station on this highway._")

            # Current station details
            with c2:
                st.markdown("**🔌 This Station**")
                st.markdown(f"**Provider:** {station['provider']}")
                st.markdown(f"**Status:** {'🟢 Operational' if station['status'] == 'Operational' else '⭐ Upcoming'}")
                st.markdown(f"**Charging Speed:** {station['kw']}")
                st.markdown(f"**State:** {station['state']}")
                st.markdown(f"**Address:** {station['address']}")

            # Next station (the other direction)
            with c3:
                st.markdown("**➡️ Next Station**")
                if pos < total_on_highway - 1:
                    nxt = hw_df.loc[pos + 1]
                    dist = nxt['position_km'] - station['position_km']
                    st.markdown(f"**{nxt['name']}**")
                    st.markdown(f"📏 {dist:.1f} km away")
                    st.markdown(f"⚡ {nxt['kw']} · {nxt['provider']}")
                    st.markdown(f"🟢 {nxt['status']}" if nxt['status'] == "Operational" else f"⭐ {nxt['status']}")
                else:
                    st.markdown("_This is the last station on this highway._")

            if station['status'] == "Upcoming":
                st.warning("⚠️ This station is not yet operational — plan your charging stop around the previous/next active hub instead.")
        else:
            st.info("👆 Click any marker on the map above to see its next station in both directions.")
