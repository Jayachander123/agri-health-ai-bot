import streamlit as st
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

# Set page config for mobile and desktop
st.set_page_config(page_title="Telangana Agri-Bot Command Center", page_icon="🚜", layout="wide")

# Load environment variables
load_dotenv()
DB_URL = os.getenv("SUPABASE_DATABASE_URL")

@st.cache_data(ttl=60) # Caches data for 60 seconds
def load_data():
    engine = create_engine(DB_URL)
    
    # Query 1: Interactions (Now including the 'crop' column!)
    interactions_df = pd.read_sql("SELECT intent, crop, source_used, created_at FROM interactions", engine)
    
    # Query 2: Users and Locations (Using your exact column names)
    locations_df = pd.read_sql("SELECT phone_hash, last_lat as lat, last_lon as lon FROM users WHERE last_lat IS NOT NULL AND last_lon IS NOT NULL", engine)
    
    # Query 3: Total Users
    users_df = pd.read_sql("SELECT phone_hash FROM users", engine)
    
    return interactions_df, locations_df, users_df

# --- UI LAYOUT ---
st.title("🚜 Telangana Agri-Bot Command Center")
st.markdown("Real-time AI monitoring for Agriculture and Health across the state.")

try:
    interactions_df, locations_df, users_df = load_data()
    
    # --- KPI METRICS ---
    st.subheader("📊 Live State Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    total_users = len(users_df)
    total_queries = len(interactions_df)
    
    # Safely count intents (converting to uppercase to avoid case-sensitivity issues)
    agri_queries = interactions_df['intent'].str.upper().eq('AGRI').sum() if 'intent' in interactions_df else 0
    health_queries = interactions_df['intent'].str.upper().eq('HEALTH').sum() if 'intent' in interactions_df else 0
    
    col1.metric("Total Farmers (Users)", total_users)
    col2.metric("Total AI Queries", total_queries)
    col3.metric("🌾 Agriculture Queries", agri_queries)
    col4.metric("🏥 Health Queries", health_queries)

    st.divider()

    # --- MAP OF TELANGANA ---
    st.subheader("📍 Live Farmer Locations")
    st.markdown("Displays active farmer locations based on shared WhatsApp GPS data.")
    if not locations_df.empty:
        # Streamlit automatically reads 'lat' and 'lon' columns
        st.map(locations_df, zoom=5, use_container_width=True)
    else:
        st.info("No GPS location data collected yet. Ask users to share their location pin on WhatsApp.")

    st.divider()

    # --- CHARTS ---
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("Query Distribution")
        if not interactions_df.empty and interactions_df['intent'].notna().any():
            intent_counts = interactions_df['intent'].value_counts().reset_index()
            intent_counts.columns = ['Intent', 'Count']
            fig_pie = px.pie(intent_counts, names='Intent', values='Count', hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.write("Waiting for intent data...")

    with col_chart2:
        st.subheader("Top Crops Queried This Week")
        if not interactions_df.empty and 'crop' in interactions_df.columns and interactions_df['crop'].notna().any():
            # Filter out empty crops and count them
            crop_counts = interactions_df['crop'].dropna().value_counts().reset_index().head(10)
            crop_counts.columns = ['Crop', 'Count']
            fig_bar = px.bar(crop_counts, x='Crop', y='Count', color='Crop')
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.write("Waiting for crop data...")

except Exception as e:
    st.error(f"Failed to fetch data: {e}")
