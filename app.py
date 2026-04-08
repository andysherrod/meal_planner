import streamlit as st
import pandas as pd
from datetime import date
import os
import json
from logic import calculate_dashboard_stats

st.set_page_config(page_title="Grocery Tracker", layout="wide")

# -- MVP Data Setup --
DATA_FILE = "data.csv"
BUDGETS_FILE = "budgets.json"

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

def load_budgets():
    if os.path.exists(BUDGETS_FILE):
        with open(BUDGETS_FILE, 'r') as f:
            return json.load(f)
    else:
        default = {
            'weekday_lunch': 100.0,
            'weekend_lunch': 80.0,
            'dinner': 300.0
        }
        save_budgets(default)
        return default

def save_budgets(budgets):
    with open(BUDGETS_FILE, 'w') as f:
        json.dump(budgets, f, indent=4)

# -- Settings --
budgets = load_budgets()

# -- UI Layout --
st.title("Family Grocery Tracker\n\n")

total_budget = sum(budgets.values())
st.metric("Total Monthly Budget", f"£{total_budget:.2f}")

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

    st.divider()

    st.header("Manage Budgets")
    with st.expander("Edit Existing Budgets"):
        updated_budgets = {}
        for cat, budg in budgets.items():
            col1, col2 = st.columns([4, 1])
            with col1:
                updated_budgets[cat] = st.number_input(f"{cat.replace('_', ' ').title()} Budget (£)", value=budg, min_value=0.0, step=1.0, format="%.2f", key=f"edit_{cat}")
            with col2:
                if st.button(" 🗑️ ", key=f"del_{cat}", help=f"Delete {cat.replace('_', ' ').title()} category"):
                    del budgets[cat]
                    save_budgets(budgets)
                    st.success(f"Category '{cat}' deleted!")
                    st.rerun()
        if st.button("Save Budget Changes", use_container_width=True):
            save_budgets(updated_budgets)
            st.success("Budgets updated!")
            st.rerun()

    with st.expander("Add New Category"):
        new_cat = st.text_input("New Category Name (use underscores for spaces)", key="new_cat")
        new_budget = st.number_input("Budget (£)", min_value=0.0, step=1.0, format="%.2f", key="new_budget")
        if st.button("Add Category", use_container_width=True):
            if new_cat and new_cat not in budgets:
                budgets[new_cat] = new_budget
                save_budgets(budgets)
                st.success(f"Category '{new_cat}' added!")
                st.rerun()
            elif new_cat in budgets:
                st.error("Category already exists!")
            else:
                st.error("Please enter a category name!")

# 2. Dashboard (Main Page)
df = load_data()
current_date = date.today()

# Run the math engine
stats = calculate_dashboard_stats(current_date, budgets, df)

st.header("Current Week Overview")
categories = list(budgets.keys())
for i in range(0, len(categories), 4):
    row_cats = categories[i:i+4]
    cols = st.columns(len(row_cats))
    for j, cat in enumerate(row_cats):
        stat = stats[cat]
        with cols[j]:
            st.subheader(cat.replace("_", " ").title())
            st.write("")  # Spacer for consistent row height
            
            # Display Adjusted Daily Target
            st.metric("Adjusted Daily Target", f"£{stat['daily_target']:.2f}")
            
            # Display Week Status
            st.metric("Remaining for this Week", f"£{stat['weekly_remaining']:.2f}", 
                      delta=f"-£{stat['week_spend']:.2f} spent", delta_color="inverse")

st.divider()

# 3. Raw Ledger (Optional check to ensure data is saving)
with st.expander("View Raw Transactions"):
    st.dataframe(df)
    if not df.empty:
        selected_indices = st.multiselect(
            "Select transactions to delete", 
            df.index.tolist(), 
            format_func=lambda x: f"Row {x+1}: {df.loc[x, 'Date']} - {df.loc[x, 'Category']} - £{df.loc[x, 'Amount']:.2f}"
        )
        if st.button("Delete Selected Transactions"):
            if selected_indices:
                df = df.drop(selected_indices)
                df.to_csv(DATA_FILE, index=False)
                st.success("Transactions deleted!")
                st.rerun()
            else:
                st.warning("No transactions selected.")
