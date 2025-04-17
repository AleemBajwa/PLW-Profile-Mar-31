import streamlit as st
import pandas as pd
import plotly.express as px
import os
import gdown

# ---- SETTINGS ----
FOLDER_URL = "https://drive.google.com/drive/folders/1MCosDFKr85ukzuXhjuCmR_Eld2ZIv0ey"
DATA_DIR = "district_data"


# ---- DOWNLOAD FROM GOOGLE DRIVE ----
@st.cache_resource
def download_all_files():
    os.makedirs(DATA_DIR, exist_ok=True)
    gdown.download_folder(FOLDER_URL, output=DATA_DIR, quiet=False, use_cookies=False)


# ---- LOAD ALL EXCEL FILES ----
@st.cache_data
def load_all_data():
    download_all_files()
    all_data = []

    for file in os.listdir(DATA_DIR):
        if file.endswith(".xlsx"):
            path = os.path.join(DATA_DIR, file)
            try:
                df = pd.read_excel(path, sheet_name=0)
                df['District'] = os.path.splitext(file)[0]
                all_data.append(df)
            except Exception as e:
                st.warning(f"Could not load {file}: {e}")

    if not all_data:
        return pd.DataFrame()

    df = pd.concat(all_data, ignore_index=True)
    df.rename(columns={'Mother_CNIC_No': 'PLW'}, inplace=True)
    df['Is_Paid'] = pd.to_numeric(df.get('Is_Paid', 0), errors='coerce').fillna(0).astype(int)
    df['Total Credit'] = pd.to_numeric(df.get('Total Credit', 0), errors='coerce')
    df['Visit_Date_Time'] = pd.to_datetime(df.get('Visit_Date_Time'), errors='coerce')
    return df


# ---- MAIN APP ----
st.title("📊 District Dashboard - Project & Non-Project")

df = load_all_data()
if df.empty:
    st.error("No data loaded. Check Google Drive folder or file structure.")
    st.stop()

# ---- KPIs ----
total_plws = df['PLW'].nunique()
total_visits = len(df)
paid_visits = df[df['Is_Paid'] == 1].shape[0]
unpaid_visits = df[df['Is_Paid'] == 0].shape[0]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total PLWs", total_plws)
col2.metric("Total Visits", total_visits)
col3.metric("Paid Visits", paid_visits)
col4.metric("Unpaid Visits", unpaid_visits)

# ---- FILTERS ----
st.sidebar.header("🔍 Filter Data")
selected_districts = st.sidebar.multiselect("District", options=df['District'].unique())
stage_filter = st.sidebar.multiselect("Stage Code", options=df['Stage_Code'].dropna().unique())
account_status_filter = st.sidebar.multiselect("Account Status", options=df['AC STATUS'].dropna().unique())
block_reason_filter = st.sidebar.multiselect("Blocking Reason", options=df['Blocking Reason'].dropna().unique())

if selected_districts:
    df = df[df['District'].isin(selected_districts)]
if stage_filter:
    df = df[df['Stage_Code'].isin(stage_filter)]
if account_status_filter:
    df = df[df['AC STATUS'].isin(account_status_filter)]
if block_reason_filter:
    df = df[df['Blocking Reason'].isin(block_reason_filter)]

# ---- VISITS OVER TIME ----
st.subheader("📈 Visits Over Time")
if 'Visit_Date_Time' in df.columns:
    visits_over_time = df.groupby(df['Visit_Date_Time'].dt.date).size().reset_index(name='Visits')
    if not visits_over_time.empty:
        fig1 = px.line(visits_over_time, x='Visit_Date_Time', y='Visits', title="Visits Over Time")
        st.plotly_chart(fig1)

# ---- ACCOUNT STATUS ----
st.subheader("📊 Account Status Distribution")
if 'AC STATUS' in df.columns:
    ac_counts = df['AC STATUS'].value_counts().reset_index()
    ac_counts.columns = ['Account Status', 'Count']
    fig2 = px.pie(ac_counts, values='Count', names='Account Status', title='Account Status Share')
    st.plotly_chart(fig2)

# ---- TOP CREDIT ----
st.subheader("💰 Total Credit by PLW")
if 'Total Credit' in df.columns:
    credit_data = df.groupby('PLW')['Total Credit'].sum().reset_index()
    top_credit = credit_data.sort_values(by='Total Credit', ascending=False).head(10)
    fig3 = px.bar(top_credit, x='PLW', y='Total Credit', title='Top 10 PLWs by Total Credit')
    st.plotly_chart(fig3)

# ---- DATA TABLE ----
st.subheader("📋 Raw Data")
st.dataframe(df)


# ---- DOWNLOAD CSV ----
@st.cache_data
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')


csv = convert_df(df)
st.download_button("📥 Download Filtered Data", csv, "filtered_data.csv", "text/csv")
