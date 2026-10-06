import streamlit as st
import pandas as pd

# Set the page layout
st.set_page_config(page_title="HEINEKEN AIDDA: Risk Dashboard", layout="wide")

# 1. LOAD THE DATA
# We load the prioritized list generated from our Random Forest model
@st.cache_data
def load_data():
    try:
        # Load the CSV we created in the previous step
        df = pd.read_csv('current_at_risk_accounts.csv')
        # Format the risk score for better UI readability
        df['risk_score'] = df['risk_score'].round(2)
        df['churn_probability'] = (df['churn_probability'] * 100).round(1).astype(str) + '%'
        return df
    except FileNotFoundError:
        # Fallback dummy data just in case the file is missing during testing
        return pd.DataFrame({
            'account_id': ['A78850', 'A32280', 'A24020'],
            'churn_probability': ['90.0%', '91.3%', '88.7%'],
            'total_spend': [6232.81, 6118.74, 6077.03],
            'risk_score': [5609.52, 5588.44, 5388.29]
        })

df = load_data()

# 2. DASHBOARD HEADER
st.title("🍺 HEINEKEN Sales Rep Proactive Planner")
st.markdown("### Today's Route: High-Priority At-Risk Accounts")
st.write("These accounts have been flagged by the prediction model due to broken order rhythms or recent drops in spend. **Action is required.**")

st.divider()

# 3. THE ACTION LAYER (The core of Part 3)
# We loop through the top accounts and create an actionable "Card" for each
top_accounts = df.head(5) # Just show the top 5 for the rep's daily route

for index, row in top_accounts.iterrows():
    account = row['account_id']
    
    # Create a visual expander box for each account
    with st.expander(f"🚨 Account: {account} | Risk Score: {row['risk_score']} | Value: ${row['total_spend']}"):
        
        # Use columns to split the 'Why' and the 'What to do'
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 🔍 Why are they flagged?")
            # In a fully finished app, these bullets would be pulled dynamically from the account's specific data
            st.write("* **Recency:** Has not ordered in over 45 days (Skipped a month).")
            st.write("* **Spend Drop:** 90-day spend is down 40% compared to the previous quarter.")
            st.write("* **Friction:** High freight delivery costs on their last 3 orders.")
            
        with col2:
            st.markdown("#### 🎯 Next Best Action (AIDDA)")
            st.success("**Recommended Action:** Subsidize Freight & Win-Back Offer")
            st.write("**Talking Point:** *'I noticed your delivery costs crept up last quarter. If you place your standard order today, I can apply a 15% freight discount to get your margins back on track.'*")
            
            # A button to simulate the rep taking action
            if st.button(f"Generate Email Template for {account}", key=account):
                st.info(f"Draft email generated and sent to your outbox for {account}!")