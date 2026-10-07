import streamlit as st
import pandas as pd

# 1. Page Configuration (Force sidebar to start expanded)
st.set_page_config(page_title="HEINEKEN Rep Dashboard", layout="wide", initial_sidebar_state="expanded")

# --- CUSTOM CSS: MAKE THE SIDEBAR GREEN ---
st.markdown("""
    <style>
        /* Target the sidebar background */
        [data-testid="stSidebar"] {
            background-color: #007A33 !important; /* Heineken Green */
        }
        /* Make sidebar text white for contrast */
        [data-testid="stSidebar"] p, 
        [data-testid="stSidebar"] span, 
        [data-testid="stSidebar"] div, 
        [data-testid="stSidebar"] h1 {
            color: white !important;
        }
    </style>
""", unsafe_allow_html=True)

# Force the sidebar to appear even if the 'pages' folder is acting up
st.sidebar.title("🍺 Menu")
st.sidebar.write("*(Native pages will appear below)*")

# 2. Data Loading
@st.cache_data
def load_app_data():
    try:
        risks_df = pd.read_csv('Analysis/current_at_risk_accounts.csv')
    except FileNotFoundError:
        st.error("Missing Analysis/current_at_risk_accounts.csv.")
        risks_df = pd.DataFrame(columns=['account_id', 'churn_probability', 'total_spend', 'risk_score'])
        
    lines_df = pd.read_csv('Analysis/order_lines.csv', dtype={'account_id': str, 'order_id': str})
    lines_df['order_date'] = pd.to_datetime(lines_df['order_date'])
    
    reviews_df = pd.read_csv('Analysis/order_reviews.csv', dtype={'order_id': str})
    
    return risks_df, lines_df, reviews_df

risks_df, lines_df, reviews_df = load_app_data()

st.title("Dashboard: Today's Route")

# 3. Two-Column Layout
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### TOP 10 risks")
    st.write("*Click on an account to see their latest activity*")
    
    top_accounts = risks_df.head(10)
    
    for index, row in top_accounts.iterrows():
        account_id = row['account_id']
        risk_score = row['risk_score']
        
        account_history = lines_df[lines_df['account_id'] == account_id].sort_values('order_date', ascending=False)
        
        if not account_history.empty:
            latest_order_id = account_history.iloc[0]['order_id']
            latest_date = account_history.iloc[0]['order_date'].strftime('%d %b %Y')
            
            latest_order_lines = account_history[account_history['order_id'] == latest_order_id]
            order_total = latest_order_lines['price'].sum()
            freight_total = latest_order_lines['freight_value'].sum()
            was_late = latest_order_lines['is_late'].any()
            
            order_review = reviews_df[reviews_df['order_id'] == latest_order_id]
            comment = "No written feedback provided."
            if not order_review.empty:
                msg = order_review.iloc[0]['review_comment_message']
                if pd.notna(msg):
                    comment = f'"{msg}"'
        else:
            latest_date, order_total, freight_total, was_late, comment = "Unknown", 0, 0, False, "No data"

        with st.expander(f"🚨 RISK: {account_id} | Score: {risk_score:.0f}"):
            st.markdown(f"**Last Order Date:** {latest_date}")
            st.markdown(f"**Order Total:** ${order_total:.2f} (Freight: ${freight_total:.2f})")
            
            if was_late:
                st.error("⚠️ The last delivery was LATE.")
            else:
                st.success("✅ The last delivery was ON TIME.")
                
            st.markdown(f"**Customer Comment:**\n{comment}")
            
            if st.button(f"Generate AIDDA Action for {account_id}", key=f"btn_{account_id}"):
                st.info(f"AIDDA Suggestion: Offer freight discount to {account_id} to repair relationship.")

with col2:
    st.markdown("### agenda")
    
    with st.container(border=True):
        st.write("**today:**")
        if not top_accounts.empty:
            st.write(f"- Visit **{top_accounts.iloc[0]['account_id']}** (Highest churn risk)")
            if len(top_accounts) > 1:
                st.write(f"- Visit **{top_accounts.iloc[1]['account_id']}** (Check on order rhythm)")
        
        st.write("**tomorrow:**")
        st.write("- Follow up on remaining high-risk accounts")
        
        st.write("**suggested route for today:**")
        
        st.markdown(
            """
            <div style='height: 300px; background-color: #e0e0e0; display: flex; align-items: center; justify-content: center; border-radius: 10px; margin-top: 15px;'>
                <b>🗺️ [ GEOLOCATION MAP SCRIPT GOES HERE ]</b>
            </div>
            """, 
            unsafe_allow_html=True
        )