import streamlit as st
import pandas as pd
from datetime import date
import os
from logic import calculate_dashboard_stats

st.set_page_config(page_title="Grocery Tracker", layout="wide")

# -- MVP Data Setup --
DATA_FILE = "data.csv"

# Create a local CSV if it doesn't exist yet
if not os.path.exists(DATA_FILE):
    pd.DataFrame(columns=["Date", "Category", "Amount"]).to_csv(DATA_FILE, index=False)

def load_data():
    return pd.read_csv(DATA_FILE)

def save_transaction(trans_date, category, amount):
    df = load_data()
    new_row = pd.DataFrame([{"Date": trans_date, "Category": category, "Amount": amount}])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(DATA_FILE, index=False)

# -- Settings (Hardcoded for MVP) --
budgets = {
    'weekday_lunch': 100.0,
    'weekend_lunch': 80.0,
    'dinner': 300.0
}

# -- UI Layout --
st.title("Family Grocery Tracker")

# 1. Input Panel (Sidebar)
with st.sidebar:
    st.header("Log Expense")
    amount = st.number_input("Amount (£)", min_value=0.0, step=1.0, format="%.2f")
    category = st.selectbox("Category", list(budgets.keys()), format_func=lambda x: x.replace("_", " ").title())
    trans_date = st.date_input("Date", date.today())
    
    if st.button("Add Transaction", use_container_width=True):
        save_transaction(trans_date, category, amount)
        st.success("Logged successfully!")
        st.rerun() # Refresh the page instantly to update dashboard

# 2. Dashboard (Main Page)
df = load_data()
current_date = date.today()

# Run the math engine
stats = calculate_dashboard_stats(current_date, budgets, df)

st.header("Current Week Overview")
cols = st.columns(len(budgets))

# Display the calculated metrics dynamically
for idx, (cat, stat) in enumerate(stats.items()):
    with cols[idx]:
        st.subheader(cat.replace("_", " ").title())
        
        # Display Adjusted Daily Target
        st.metric("Adjusted Daily Target", f"£{stat['daily_target']:.2f}")
        
        # Display Week Status
        st.metric("Remaining for this Week", f"£{stat['weekly_remaining']:.2f}", 
                  delta=f"-£{stat['week_spend']:.2f} spent", delta_color="inverse")

st.divider()

# 3. Raw Ledger (Optional check to ensure data is saving)
with st.expander("View Raw Transactions"):
    st.dataframe(df)
