import streamlit as st
import pandas as pd
import numpy as np
import folium
import re
import requests
from geopy.geocoders import Nominatim
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
    /* --- Highway Corridor View components --- */
    .station-card {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 16px;
        min-height: 168px;
    }
    .station-card.current {
        border: 1px solid #10B981;
        box-shadow: 0 0 0 1px rgba(16,185,129,0.35);
    }
    .station-card h5 {
        margin: 0 0 8px 0;
        color: #F8FAFC;
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        color: #94A3B8;
    }
    .station-card .name { font-weight: 700; font-size: 15px; color: #F8FAFC; margin-bottom: 4px; }
    .station-card .meta { font-size: 13px; color: #CBD5E1; line-height: 1.6; }
    .badge {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 999px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.03em;
    }
    .badge-operational { background: rgba(16,185,129,0.15); color: #10B981; }
    .badge-upcoming { background: rgba(245,158,11,0.15); color: #F59E0B; }
    .badge-safe { background: rgba(16,185,129,0.15); color: #10B981; }
    .badge-caution { background: rgba(245,158,11,0.15); color: #F59E0B; }
    .badge-risk { background: rgba(239,68,68,0.18); color: #EF4444; }
    /* Vertical route timeline */
    .timeline-item {
        display: flex;
        gap: 12px;
        position: relative;
    }
    .timeline-dot {
        width: 30px; height: 30px; min-width: 30px;
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-weight: 700; font-size: 12px; color: white;
        border: 2px solid #0B0F19;
        z-index: 1;
    }
    .timeline-line {
        position: absolute;
        left: 14px; top: 30px;
        width: 2px;
        background: #334155;
    }
    .timeline-content {
        background-color: #1E293B;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 10px 14px;
        flex: 1;
        margin-bottom: 4px;
    }
    .timeline-content.selected { border-color: #10B981; box-shadow: 0 0 0 1px rgba(16,185,129,0.3); }
    .timeline-gap {
        font-size: 12px;
        color: #94A3B8;
        margin: 2px 0 2px 42px;
        padding: 2px 0;
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

# --- City-to-City Route Planner: geocoding, real driving routes, and route-corridor matching ---
@st.cache_data(show_spinner=False)
def geocode_city(city_name):
    """Turns a city name into (lat, lon, display_address) using OpenStreetMap Nominatim."""
    geolocator = Nominatim(user_agent="voltran_ev_dashboard_app")
    try:
        location = geolocator.geocode(f"{city_name}, India", timeout=10)
        if location:
            return (location.latitude, location.longitude, location.address)
    except Exception:
        return None
    return None

@st.cache_data(show_spinner=False)
def get_driving_route(start_lat, start_lon, end_lat, end_lon):
    """Fetches the real driving route geometry between two points via the OSRM demo server."""
    url = f"https://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}"
    params = {"overview": "full", "geometries": "geojson"}
    try:
        resp = requests.get(url, params=params, timeout=15)
        data = resp.json()
        if data.get("code") == "Ok" and data.get("routes"):
            route = data["routes"][0]
            coords = [(c[1], c[0]) for c in route["geometry"]["coordinates"]]  # -> (lat, lon)
            return {
                "coords": coords,
                "distance_km": route["distance"] / 1000.0,
                "duration_min": route["duration"] / 60.0,
            }
    except Exception:
        return None
    return None

def route_cumulative_distances(coords):
    cum = [0.0]
    for i in range(1, len(coords)):
        cum.append(cum[-1] + haversine(coords[i - 1][0], coords[i - 1][1], coords[i][0], coords[i][1]))
    return cum

def nearest_point_on_route(lat, lon, coords, cum, sample_cap=800):
    """Distance from (lat, lon) to the closest point on the route, and that point's
    distance-from-start along the route. Samples the route to keep this fast on long routes."""
    step = max(1, len(coords) // sample_cap)
    best_d, best_i = float('inf'), 0
    for i in range(0, len(coords), step):
        d = haversine(lat, lon, coords[i][0], coords[i][1])
        if d < best_d:
            best_d, best_i = d, i
    return best_d, cum[best_i]

@st.cache_data(show_spinner=False)
def stations_along_route(_coords_tuple, corridor_width_km):
    """Finds every station within corridor_width_km of the route and orders them by
    how far along the route they are. _coords_tuple must be a hashable tuple of (lat,lon)."""
    coords = list(_coords_tuple)
    cum = route_cumulative_distances(coords)
    rows = []
    for _, row in df.iterrows():
        d, pos = nearest_point_on_route(row['lat'], row['lon'], coords, cum)
        if d <= corridor_width_km:
            r = row.to_dict()
            r['position_km'] = pos
            r['dist_from_route_km'] = d
            rows.append(r)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values('position_km').reset_index(drop=True)

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

# --- Hex equivalents of the folium color names above, for custom DivIcons ---
PROVIDER_HEX = {
    "Voltran": "#059669",
    "Tata Power": "#2563EB",
    "Statiq": "#065F46",
    "Zeon Charging": "#5F9EA0",
    "ChargeZone": "#7C3AED",
    "Jio-bp pulse": "#DC2626",
    "GLIDA": "#F97316",
    "Ather Grid": "#991B1B",
}
UPCOMING_HEX = "#F59E0B"

def numbered_icon(number, provider, is_upcoming, is_selected):
    """A numbered circular marker so the map itself shows travel order,
    with a highlighted ring for whichever station is currently selected."""
    bg = UPCOMING_HEX if is_upcoming else PROVIDER_HEX.get(provider, "#64748B")
    size = 34 if is_selected else 26
    ring = "box-shadow: 0 0 0 3px #F8FAFC, 0 0 8px rgba(16,185,129,0.8);" if is_selected else "box-shadow: 0 2px 4px rgba(0,0,0,0.5);"
    html = f"""<div style="
        background:{bg}; color:white; border-radius:50%;
        width:{size}px; height:{size}px; display:flex; align-items:center; justify-content:center;
        font-weight:700; font-size:{13 if is_selected else 11}px; font-family:Arial, sans-serif;
        border:2px solid #0B0F19; {ring}">{number}</div>"""
    return folium.DivIcon(html=html, icon_size=(size, size), icon_anchor=(size // 2, size // 2))

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
tab1, tab2, tab3, tab4 = st.tabs([
    "📏 Distance to Next Charging Station",
    "📋 Full Searchable Directory",
    "🛣️ Highway Corridor View",
    "📍 City-to-City Route Planner"
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
    st.subheader("🛣️ Highway Corridor Planner")
    st.markdown(
        "Pick a national highway to see every charging station along it, in travel order — "
        "then select any stop (click the map or use the dropdown) to see what's before and after it, "
        "how far, and whether the gap is safe for your EV's range."
    )

    available_highways = sorted(df['highway'].dropna().unique())

    if not available_highways:
        st.info("No stations in the current dataset are tagged to a numbered national highway.")
    else:
        ctrl1, ctrl2, ctrl3 = st.columns([2, 1.4, 1.4])
        with ctrl1:
            selected_highway = st.selectbox("🛣️ Choose a National Highway:", options=available_highways)
        with ctrl2:
            operational_only = st.checkbox("Only show operational stations", value=False,
                                            help="Hide 'Upcoming' hubs that aren't chargeable yet — recommended for real trip planning.")
        with ctrl3:
            ev_range_km = st.number_input("🔋 Your EV's range (km)", min_value=50, max_value=800, value=300, step=10)

        # --- Build the ordered station set for this highway ---
        hw_df = df[df['highway'] == selected_highway]
        if operational_only:
            hw_df = hw_df[hw_df['status'] == "Operational"]
        hw_df = order_along_highway(hw_df)
        total_on_highway = len(hw_df)

        if total_on_highway == 0:
            st.warning("No operational stations on this highway yet. Uncheck the filter to see upcoming hubs.")
        else:
            station_names_in_order = hw_df['name'].tolist()

            # A safe usable range: leave a buffer rather than planning to arrive on empty
            safe_range_km = ev_range_km * 0.65

            gaps = hw_df['position_km'].diff().fillna(0)
            max_gap = gaps.max() if total_on_highway > 1 else 0
            avg_gap = gaps[1:].mean() if total_on_highway > 1 else 0
            stops_needed = max(0, int(np.ceil(hw_df['position_km'].max() / safe_range_km))) if total_on_highway > 1 else 0
            risky_gap_count = int((gaps > safe_range_km).sum())

            # --- Summary stat row ---
            s1, s2, s3, s4, s5 = st.columns(5)
            s1.metric("Stations on Route", total_on_highway)
            s2.metric("Highway Span", f"{hw_df['position_km'].max():.0f} km")
            s3.metric("Avg. Gap Between Stops", f"{avg_gap:.0f} km" if total_on_highway > 1 else "—")
            s4.metric("Longest Gap", f"{max_gap:.0f} km" if total_on_highway > 1 else "—")
            s5.metric("Est. Charging Stops Needed", stops_needed if total_on_highway > 1 else "—",
                      help=f"Based on a safe usable range of {safe_range_km:.0f} km (65% of your entered range).")

            if risky_gap_count > 0:
                st.error(f"⚠️ **Range Anxiety Alert:** {risky_gap_count} gap(s) on this highway exceed your safe range "
                          f"of {safe_range_km:.0f} km. Check the flagged segments in the route timeline below before you go.")
            else:
                st.success(f"✅ Every gap on this highway is within your safe range of {safe_range_km:.0f} km.")

            # --- Selection state: keep the currently focused station in sync across reruns ---
            if ("selected_station" not in st.session_state
                    or st.session_state.selected_station not in station_names_in_order):
                st.session_state.selected_station = station_names_in_order[0]

            # --- Map: numbered markers in travel order, current selection highlighted ---
            map_col, list_col = st.columns([1.6, 1])

            with map_col:
                hw_df_bounds = hw_df[['lat', 'lon']].values.tolist()
                hm = folium.Map(tiles="CartoDB dark_matter")
                hm.fit_bounds(hw_df_bounds, padding=(30, 30))

                route_points = list(zip(hw_df['lat'], hw_df['lon']))
                folium.PolyLine(route_points, color="#10B981", weight=3, opacity=0.6, dash_array="6").add_to(hm)

                for idx, row in hw_df.iterrows():
                    is_upcoming = row['status'] == "Upcoming"
                    is_selected = row['name'] == st.session_state.selected_station
                    popup_html = (
                        f"<b>{idx + 1}. {row['name']}</b><br>"
                        f"{row['provider']} · {row['kw']}<br>"
                        f"{'⭐ Upcoming' if is_upcoming else '🟢 Operational'}"
                    )
                    folium.Marker(
                        location=[row['lat'], row['lon']],
                        tooltip=row['name'],
                        popup=folium.Popup(popup_html, max_width=220),
                        icon=numbered_icon(idx + 1, row['provider'], is_upcoming, is_selected)
                    ).add_to(hm)

                hw_map_data = st_folium(hm, width=None, height=480, key=f"highway_map_{selected_highway}_{operational_only}")

                clicked_name = None
                if hw_map_data and hw_map_data.get("last_object_clicked_tooltip"):
                    clicked_name = hw_map_data["last_object_clicked_tooltip"]
                if clicked_name and clicked_name in station_names_in_order:
                    st.session_state.selected_station = clicked_name

            with list_col:
                st.markdown("**Jump to a stop:**")
                dropdown_options = [f"{i+1}. {n}" for i, n in enumerate(station_names_in_order)]
                current_idx = station_names_in_order.index(st.session_state.selected_station)
                picked = st.selectbox(
                    "Jump to a stop", options=dropdown_options, index=current_idx,
                    label_visibility="collapsed", key=f"dropdown_{selected_highway}_{operational_only}"
                )
                picked_name = picked.split(". ", 1)[1]
                if picked_name != st.session_state.selected_station:
                    st.session_state.selected_station = picked_name

                # --- Full ordered route timeline for this highway ---
                st.markdown("**Full route, in order:**")
                timeline_html = "<div>"
                for i, row in hw_df.iterrows():
                    is_upcoming = row['status'] == "Upcoming"
                    is_sel = row['name'] == st.session_state.selected_station
                    dot_bg = UPCOMING_HEX if is_upcoming else PROVIDER_HEX.get(row['provider'], "#64748B")
                    badge = '<span class="badge badge-upcoming">UPCOMING</span>' if is_upcoming else '<span class="badge badge-operational">LIVE</span>'
                    timeline_html += f"""
                    <div class="timeline-item">
                        <div class="timeline-dot" style="background:{dot_bg};">{i+1}</div>
                        <div class="timeline-content {'selected' if is_sel else ''}">
                            <div style="font-weight:600; font-size:13px;">{row['name']}</div>
                            <div style="font-size:11px; color:#94A3B8;">{row['provider']} · {row['kw']} &nbsp; {badge}</div>
                        </div>
                    </div>"""
                    if i < total_on_highway - 1:
                        gap = gaps.iloc[i + 1]
                        if gap > safe_range_km:
                            risk_badge = '<span class="badge badge-risk">⚠ EXCEEDS RANGE</span>'
                        elif gap > safe_range_km * 0.7:
                            risk_badge = '<span class="badge badge-caution">CAUTION</span>'
                        else:
                            risk_badge = '<span class="badge badge-safe">SAFE</span>'
                        timeline_html += f'<div class="timeline-gap">↓ {gap:.0f} km &nbsp; {risk_badge}</div>'
                timeline_html += "</div>"
                st.markdown(
                    f'<div style="max-height:420px; overflow-y:auto; padding-right:6px;">{timeline_html}</div>',
                    unsafe_allow_html=True
                )

            # --- Detail panel: previous / current / next, with "next operational" fallback ---
            pos = station_names_in_order.index(st.session_state.selected_station)
            station = hw_df.iloc[pos]

            st.markdown("---")
            st.markdown(
                f"### 📍 {station['name']} &nbsp; "
                f"<span style='font-size:14px; color:#94A3B8;'>(Stop {pos + 1} of {total_on_highway} on {selected_highway})</span>",
                unsafe_allow_html=True
            )

            def render_neighbor(col, row, label, arrow, dist):
                status_badge = '<span class="badge badge-operational">OPERATIONAL</span>' if row['status'] == "Operational" else '<span class="badge badge-upcoming">UPCOMING</span>'
                col.markdown(f"""
                <div class="station-card">
                    <h5>{arrow} {label}</h5>
                    <div class="name">{row['name']}</div>
                    <div class="meta">
                        📏 {dist:.1f} km away<br>
                        ⚡ {row['kw']}<br>
                        🏢 {row['provider']}<br>
                        {status_badge}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            c1, c2, c3 = st.columns(3)

            with c1:
                if pos > 0:
                    prev = hw_df.iloc[pos - 1]
                    render_neighbor(c1, prev, "Previous Station", "⬅️", station['position_km'] - prev['position_km'])
                    if prev['status'] == "Upcoming":
                        prior_ops = hw_df.iloc[:pos][hw_df.iloc[:pos]['status'] == "Operational"]
                        if not prior_ops.empty:
                            nearest_op = prior_ops.iloc[-1]
                            c1.caption(f"⚡ Next *operational* stop back: **{nearest_op['name']}** "
                                       f"({station['position_km'] - nearest_op['position_km']:.1f} km)")
                else:
                    c1.markdown('<div class="station-card"><h5>⬅️ Previous Station</h5><div class="meta">This is the first station on this highway.</div></div>', unsafe_allow_html=True)

            with c2:
                status_badge = '<span class="badge badge-operational">OPERATIONAL</span>' if station['status'] == "Operational" else '<span class="badge badge-upcoming">UPCOMING</span>'
                c2.markdown(f"""
                <div class="station-card current">
                    <h5>🔌 This Station</h5>
                    <div class="name">{station['name']}</div>
                    <div class="meta">
                        🏢 {station['provider']} &nbsp; {status_badge}<br>
                        ⚡ {station['kw']}<br>
                        📍 {station['state']}<br>
                        🏠 {station['address']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with c3:
                if pos < total_on_highway - 1:
                    nxt = hw_df.iloc[pos + 1]
                    render_neighbor(c3, nxt, "Next Station", "➡️", nxt['position_km'] - station['position_km'])
                    if nxt['status'] == "Upcoming":
                        later_ops = hw_df.iloc[pos + 1:][hw_df.iloc[pos + 1:]['status'] == "Operational"]
                        if not later_ops.empty:
                            nearest_op = later_ops.iloc[0]
                            c3.caption(f"⚡ Next *operational* stop ahead: **{nearest_op['name']}** "
                                       f"({nearest_op['position_km'] - station['position_km']:.1f} km)")
                else:
                    c3.markdown('<div class="station-card"><h5>➡️ Next Station</h5><div class="meta">This is the last station on this highway.</div></div>', unsafe_allow_html=True)

            if station['status'] == "Upcoming":
                st.warning("⚠️ This station is not yet operational — plan your charging stop around the previous/next live hub instead.")

            # --- Export the route ---
            export_df = hw_df[['name', 'provider', 'status', 'kw', 'state', 'address', 'position_km']].copy()
            export_df.insert(0, 'stop_number', range(1, total_on_highway + 1))
            export_df = export_df.rename(columns={'position_km': 'distance_from_start_km'})
            st.download_button(
                "⬇️ Download this route as CSV",
                data=export_df.to_csv(index=False).encode('utf-8'),
                file_name=f"{selected_highway}_charging_route.csv",
                mime="text/csv"
            )

with tab4:
    st.subheader("📍 Plan a Route Between Two Cities")
    st.markdown(
        "Enter where you're starting and where you're headed — we'll pull the real driving route "
        "and show every charging station within reach of it, in the order you'll pass them."
    )

    rc1, rc2, rc3 = st.columns([2, 2, 1])
    with rc1:
        start_city = st.text_input("From", placeholder="e.g. Hyderabad", key="route_start_input")
    with rc2:
        end_city = st.text_input("To", placeholder="e.g. Tirupati", key="route_end_input")
    with rc3:
        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
        find_route_clicked = st.button("🔍 Find Route", use_container_width=True)

    rc4, rc5 = st.columns(2)
    with rc4:
        route_ev_range_km = st.number_input("🔋 Your EV's range (km)", min_value=50, max_value=800, value=300, step=10, key="route_ev_range")
    with rc5:
        corridor_width_km = st.slider(
            "Search width around the route (km)", min_value=5, max_value=50, value=20,
            help="Stations within this distance of the actual driving path count as 'on the way'."
        )

    if find_route_clicked:
        if not start_city.strip() or not end_city.strip():
            st.warning("Enter both a starting city and a destination.")
        else:
            with st.spinner(f"Locating {start_city} and {end_city}..."):
                start_geo = geocode_city(start_city.strip())
                end_geo = geocode_city(end_city.strip())

            if not start_geo:
                st.error(f"Couldn't find '{start_city}'. Try adding the state, e.g. 'Warangal, Telangana'.")
            elif not end_geo:
                st.error(f"Couldn't find '{end_city}'. Try adding the state, e.g. 'Kadapa, Andhra Pradesh'.")
            else:
                with st.spinner("Calculating the driving route..."):
                    route = get_driving_route(start_geo[0], start_geo[1], end_geo[0], end_geo[1])

                if not route:
                    st.error("Couldn't calculate a driving route between these two places right now — the routing "
                              "service may be temporarily unavailable, or they aren't connected by road. Try again in a moment.")
                else:
                    st.session_state.route_data = route
                    st.session_state.route_start_geo = start_geo
                    st.session_state.route_end_geo = end_geo
                    st.session_state.route_start_name = start_city.strip()
                    st.session_state.route_end_name = end_city.strip()
                    st.session_state.route_selected_station = None

    if st.session_state.get("route_data"):
        route = st.session_state.route_data
        coords_tuple = tuple(route["coords"])

        route_df = stations_along_route(coords_tuple, corridor_width_km)
        total_route_stations = len(route_df)

        st.markdown(
            f"**{st.session_state.route_start_name} → {st.session_state.route_end_name}**: "
            f"{route['distance_km']:.0f} km, roughly {route['duration_min']/60:.1f} hr driving. "
            f"**{total_route_stations} charging station(s)** found within {corridor_width_km} km of the route."
        )

        if total_route_stations == 0:
            st.warning("No stations found within this search width. Try widening the 'Search width around the route' slider above.")
        else:
            safe_range_km = route_ev_range_km * 0.65
            gaps = route_df['position_km'].diff().fillna(0)
            max_gap = gaps.max() if total_route_stations > 1 else 0
            avg_gap = gaps[1:].mean() if total_route_stations > 1 else 0
            stops_needed = max(0, int(np.ceil(route_df['position_km'].max() / safe_range_km))) if total_route_stations > 1 else 0
            risky_gap_count = int((gaps > safe_range_km).sum())

            s1, s2, s3, s4, s5 = st.columns(5)
            s1.metric("Stations Along Route", total_route_stations)
            s2.metric("Total Route Distance", f"{route['distance_km']:.0f} km")
            s3.metric("Avg. Gap Between Stops", f"{avg_gap:.0f} km" if total_route_stations > 1 else "—")
            s4.metric("Longest Gap", f"{max_gap:.0f} km" if total_route_stations > 1 else "—")
            s5.metric("Est. Charging Stops Needed", stops_needed if total_route_stations > 1 else "—",
                      help=f"Based on a safe usable range of {safe_range_km:.0f} km (65% of your entered range).")

            if risky_gap_count > 0:
                st.error(f"⚠️ **Range Anxiety Alert:** {risky_gap_count} gap(s) on this route exceed your safe range "
                          f"of {safe_range_km:.0f} km. Check the flagged segments in the route timeline below.")
            else:
                st.success(f"✅ Every gap on this route is within your safe range of {safe_range_km:.0f} km.")

            station_names_in_order = route_df['name'].tolist()
            if ("route_selected_station" not in st.session_state
                    or st.session_state.route_selected_station not in station_names_in_order):
                st.session_state.route_selected_station = station_names_in_order[0]

            map_col, list_col = st.columns([1.6, 1])

            with map_col:
                rm = folium.Map(tiles="CartoDB dark_matter")
                all_pts = route["coords"]
                rm.fit_bounds(all_pts, padding=(30, 30))

                # The actual driving route, in full
                folium.PolyLine(all_pts, color="#3B82F6", weight=4, opacity=0.65).add_to(rm)

                folium.Marker(
                    location=[st.session_state.route_start_geo[0], st.session_state.route_start_geo[1]],
                    tooltip=f"Start: {st.session_state.route_start_name}",
                    icon=folium.Icon(color="lightgray", icon="play", prefix="fa")
                ).add_to(rm)
                folium.Marker(
                    location=[st.session_state.route_end_geo[0], st.session_state.route_end_geo[1]],
                    tooltip=f"Destination: {st.session_state.route_end_name}",
                    icon=folium.Icon(color="lightgray", icon="flag-checkered", prefix="fa")
                ).add_to(rm)

                for idx, row in route_df.iterrows():
                    is_upcoming = row['status'] == "Upcoming"
                    is_selected = row['name'] == st.session_state.route_selected_station
                    popup_html = (
                        f"<b>{idx + 1}. {row['name']}</b><br>"
                        f"{row['provider']} · {row['kw']}<br>"
                        f"{row['dist_from_route_km']:.1f} km off the route<br>"
                        f"{'⭐ Upcoming' if is_upcoming else '🟢 Operational'}"
                    )
                    marker = folium.Marker(
                        location=[row['lat'], row['lon']],
                        tooltip=row['name'],
                        popup=folium.Popup(popup_html, max_width=220),
                        icon=numbered_icon(idx + 1, row['provider'], is_upcoming, is_selected)
                    )
                    marker.add_to(rm)

                route_map_data = st_folium(rm, width=None, height=480,
                                            key=f"route_map_{st.session_state.route_start_name}_{st.session_state.route_end_name}_{corridor_width_km}")

                clicked_name = None
                if route_map_data and route_map_data.get("last_object_clicked_tooltip"):
                    clicked_name = route_map_data["last_object_clicked_tooltip"]
                if clicked_name and clicked_name in station_names_in_order:
                    st.session_state.route_selected_station = clicked_name

            with list_col:
                st.markdown("**Jump to a stop:**")
                dropdown_options = [f"{i+1}. {n}" for i, n in enumerate(station_names_in_order)]
                current_idx = station_names_in_order.index(st.session_state.route_selected_station)
                picked = st.selectbox(
                    "Jump to a stop", options=dropdown_options, index=current_idx,
                    label_visibility="collapsed",
                    key=f"route_dropdown_{st.session_state.route_start_name}_{st.session_state.route_end_name}_{corridor_width_km}"
                )
                picked_name = picked.split(". ", 1)[1]
                if picked_name != st.session_state.route_selected_station:
                    st.session_state.route_selected_station = picked_name

                st.markdown("**Full route, in order:**")
                timeline_html = "<div>"
                for i, row in route_df.iterrows():
                    is_upcoming = row['status'] == "Upcoming"
                    is_sel = row['name'] == st.session_state.route_selected_station
                    dot_bg = UPCOMING_HEX if is_upcoming else PROVIDER_HEX.get(row['provider'], "#64748B")
                    badge = '<span class="badge badge-upcoming">UPCOMING</span>' if is_upcoming else '<span class="badge badge-operational">LIVE</span>'
                    timeline_html += f"""
                    <div class="timeline-item">
                        <div class="timeline-dot" style="background:{dot_bg};">{i+1}</div>
                        <div class="timeline-content {'selected' if is_sel else ''}">
                            <div style="font-weight:600; font-size:13px;">{row['name']}</div>
                            <div style="font-size:11px; color:#94A3B8;">{row['provider']} · {row['kw']} &nbsp; {badge} &nbsp; {row['dist_from_route_km']:.1f} km off route</div>
                        </div>
                    </div>"""
                    if i < total_route_stations - 1:
                        gap = gaps.iloc[i + 1]
                        if gap > safe_range_km:
                            risk_badge = '<span class="badge badge-risk">⚠ EXCEEDS RANGE</span>'
                        elif gap > safe_range_km * 0.7:
                            risk_badge = '<span class="badge badge-caution">CAUTION</span>'
                        else:
                            risk_badge = '<span class="badge badge-safe">SAFE</span>'
                        timeline_html += f'<div class="timeline-gap">↓ {gap:.0f} km &nbsp; {risk_badge}</div>'
                timeline_html += "</div>"
                st.markdown(
                    f'<div style="max-height:420px; overflow-y:auto; padding-right:6px;">{timeline_html}</div>',
                    unsafe_allow_html=True
                )

            pos = station_names_in_order.index(st.session_state.route_selected_station)
            station = route_df.iloc[pos]

            st.markdown("---")
            st.markdown(
                f"### 📍 {station['name']} &nbsp; "
                f"<span style='font-size:14px; color:#94A3B8;'>(Stop {pos + 1} of {total_route_stations} "
                f"between {st.session_state.route_start_name} and {st.session_state.route_end_name})</span>",
                unsafe_allow_html=True
            )

            def render_route_neighbor(col, row, label, arrow, dist):
                status_badge = '<span class="badge badge-operational">OPERATIONAL</span>' if row['status'] == "Operational" else '<span class="badge badge-upcoming">UPCOMING</span>'
                col.markdown(f"""
                <div class="station-card">
                    <h5>{arrow} {label}</h5>
                    <div class="name">{row['name']}</div>
                    <div class="meta">
                        📏 {dist:.1f} km away<br>
                        ⚡ {row['kw']}<br>
                        🏢 {row['provider']}<br>
                        {status_badge}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            c1, c2, c3 = st.columns(3)

            with c1:
                if pos > 0:
                    prev = route_df.iloc[pos - 1]
                    render_route_neighbor(c1, prev, "Previous Station", "⬅️", station['position_km'] - prev['position_km'])
                else:
                    c1.markdown(f'<div class="station-card"><h5>⬅️ Previous Station</h5><div class="meta">This is the first stop after {st.session_state.route_start_name}.</div></div>', unsafe_allow_html=True)

            with c2:
                status_badge = '<span class="badge badge-operational">OPERATIONAL</span>' if station['status'] == "Operational" else '<span class="badge badge-upcoming">UPCOMING</span>'
                c2.markdown(f"""
                <div class="station-card current">
                    <h5>🔌 This Station</h5>
                    <div class="name">{station['name']}</div>
                    <div class="meta">
                        🏢 {station['provider']} &nbsp; {status_badge}<br>
                        ⚡ {station['kw']}<br>
                        📍 {station['state']} &nbsp;·&nbsp; {station['dist_from_route_km']:.1f} km off the route<br>
                        🏠 {station['address']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with c3:
                if pos < total_route_stations - 1:
                    nxt = route_df.iloc[pos + 1]
                    render_route_neighbor(c3, nxt, "Next Station", "➡️", nxt['position_km'] - station['position_km'])
                else:
                    c3.markdown(f'<div class="station-card"><h5>➡️ Next Station</h5><div class="meta">This is the last stop before {st.session_state.route_end_name}.</div></div>', unsafe_allow_html=True)

            if station['status'] == "Upcoming":
                st.warning("⚠️ This station is not yet operational — plan your charging stop around the previous/next live hub instead.")

            export_df = route_df[['name', 'provider', 'status', 'kw', 'state', 'address', 'position_km', 'dist_from_route_km']].copy()
            export_df.insert(0, 'stop_number', range(1, total_route_stations + 1))
            export_df = export_df.rename(columns={'position_km': 'distance_from_start_km', 'dist_from_route_km': 'distance_off_route_km'})
            st.download_button(
                "⬇️ Download this route as CSV",
                data=export_df.to_csv(index=False).encode('utf-8'),
                file_name=f"{st.session_state.route_start_name}_to_{st.session_state.route_end_name}_charging_route.csv",
                mime="text/csv",
                key="route_dl_btn"
            )
    else:
        st.info("👆 Enter a starting city and destination, then click **Find Route** to see the plan.")
