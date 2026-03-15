import streamlit as st
import psycopg2
import pandas as pd

conn = psycopg2.connect(
    host=st.secrets["DB_HOST"],
    database=st.secrets["DB_NAME"],
    user=st.secrets["DB_USER"],
    password=st.secrets["DB_PASS"],
    port=st.secrets["DB_PORT"]
)

query = "SELECT * FROM devices ORDER BY created_at DESC"

df = pd.read_sql(query, conn)

st.title("SIEM Solution")

st.dataframe(df)