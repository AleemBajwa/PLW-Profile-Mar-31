import streamlit as st
import pandas as pd
import plotly.express as px

# List of Google Sheets to load
sheet_sources = [
    {"id": "1wDFVz6RH2Yen67dxJgeSFL9LJATFNyy-", "name": "Bahawalnagar", "type": "Project"},
    {"id": "1WOjoGRwvhsMWfHimQco7R2ZGj81vYaJC", "name": "Bahawalpur", "type": "Project"},
    {"id": "1cSVCe-3v9yMq-Y1HhCalK9lU41_CvPSa", "name": "Bhakkar", "type": "Project"},
    {"id": "1GEusgw8Xnqn7b1RBmoT9HakntJG8NZef", "name": "Dera Ghazi Khan", "type": "Project"},
    {"id": "1SOnYnhUBjO7W3jtJBgd73uxXoZOehqGA", "name": "Khushab", "type": "Project"},
    {"id": "1SdEVber4AmHz_7QhZ5wqsYfgq36t1OFX", "name": "Layyah", "type": "Project"},
    {"id": "10Fr6lODWFBQSln3pFuG9Y02rewOXj7Ui", "name": "Lodhran", "type": "Project"},
    {"id": "1JQXPz7o3oigjrjBvYl_Lh_WbrHWp9Qvc", "name": "Mianwali", "type": "Project"},
    {"id": "1ptxHDbhb1UfhXAa1ql0HqbjdXV0oZPCf", "name": "Muzaffargarh", "type": "Project"},
    {"id": "1pCfwd6NmgcSvwSc6m2FUwq-bQRiD2Nrs", "name": "Rahim Yar Khan", "type": "Project"},
    {"id": "13sY2ZV-dBxYnNliQfUn3A6YhsPCKblQJ", "name": "Rajanpur", "type": "Project"},
    {"id": "1z7OErHOz4VjF_Pz8YfZwNRSYPyLsE2Uo", "name": "Non-Project", "type": "Non-Project"}
]

# Load all sheets from Google Sheets
@st.cache_data
def load_all_data():
    dfs = []
    for src in sheet_sources:
        try:
            url = f"https://docs.google.com/spreadsheets/d/{src['id']}/export?format=csv"
            df = pd.read_csv(url)
            df['District'] = src['name']
            df['District_Type'] = src['type']
            dfs.append(df)
        except Exception as e:
            st.warning(f"Failed to load {src['name']}: {e}")
    df = pd.concat(dfs, ignore_index=True)
    df.rename(columns={'Mother_CNIC_No': 'PLW'}, inplace=True)
    df['Is_Paid'] = pd.to_numeric(df.get('Is_Paid', 0), errors='coerce').fillna(0).astype(int)
    df['Total Credit'] = pd.to_numeric(df.get('Total Credit', 0), errors='coerce')
    df['Visit_Date_Time'] = pd.to_datetime(df.get('Visit_Date_Time'), errors='coerce')
    return df

# Load data
st.title("📊 District Dashboard")
df = load_all_data()

# KPIs
st.header("📌 Summary")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total PLWs", df['PLW'].nunique())
col2.metric("Total Visits", len(df))
col3.metric("Paid Visits", df[df['Is_Paid'] == 1].shape[0])
col4.metric("Unpaid Visits", df[df['Is_Paid'] == 0].shape[0])

# Sidebar Filters
st.sidebar.header("🔍 Filters")
district_type = st.sidebar.multiselect("District Type", df['District_Type'].unique())
districts = st.sidebar.multiselect("District", df['District'].unique())
stage_codes = st.sidebar.multiselect("Stage Code", df['Stage_Code'].dropna().unique())
account_status = st.sidebar.multiselect("Account Status", df['AC STATUS'].dropna().unique())

if district_type:
    df = df[df['District_Type'].isin(district_type)]
if districts:
    df = df[df['District'].isin(districts)]
if stage_codes:
    df = df[df['Stage_Code'].isin(stage_codes)]
if account_status:
    df = df[df['AC STATUS'].isin(account_status)]

# Charts
st.subheader("📈 Visits Over Time")
if 'Visit_Date_Time' in df.columns and not df['Visit_Date_Time'].isna().all():
    visits = df.groupby(df['Visit_Date_Time'].dt.date).size().reset_index(name='Visits')
    st.plotly_chart(px.line(visits, x='Visit_Date_Time', y='Visits'))

st.subheader("📊 Account Status")
status_counts = df['AC STATUS'].value_counts().reset_index()
status_counts.columns = ['Status', 'Count']
st.plotly_chart(px.pie(status_counts, names='Status', values='Count'))

st.subheader("💰 Top PLWs by Credit")
top_credit = df.groupby('PLW')['Total Credit'].sum().reset_index().sort_values(by='Total Credit', ascending=False).head(10)
st.plotly_chart(px.bar(top_credit, x='PLW', y='Total Credit'))

# Data Table
st.subheader("📋 Data Table")
st.dataframe(df)

# Download
@st.cache_data
def convert_df(df):
    return df.to_csv(index=False).encode("utf-8")

csv = convert_df(df)
st.download_button("📥 Download Data", csv, "filtered_data.csv", "text/csv")
