"""Streamlit app"""
import pandas as pd
import streamlit as st
from camp_dashboard.etl import AirtableData

API_KEY = st.secrets["api_key"]
APP_KEY = st.secrets["app_key"]
TABLE = st.secrets["table"]
URL = f"https://api.airtable.com/v0/{APP_KEY}/{TABLE}"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

etl = AirtableData(url=URL, headers=HEADERS)
dataset = etl.run()
del etl

# Dasboard setup
st.set_page_config(
    page_title="Retiro Nacional de Jóvenes",
    page_icon="✅",
    layout="wide",
)
