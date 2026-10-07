import streamlit as st

st.set_page_config(page_title="HEINEKEN Rep Dashboard", layout="wide")

st.title("Home: Dashboard")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### TOP 10 risks?")
    
    with st.container(border=True):
        st.write("🚨 **RISK 1** - A78850")
        st.write("🚨 **RISK 2** - A32280")
        st.write("🚨 **RISK 3** - A24020")
        st.write("🚨 **RISK 4** - A89190")
        st.write("*Click on risk for more information*")
        
with col2:
    st.markdown("### agenda")
    
    with st.container(border=True):
        st.write("**today:**")
        st.write("- visit this client, place they are based")
        st.write("- and this client, place they are based")
        
        st.write("**tomorrow:**")
        st.write("- visit this client, and shit one")
        
        st.write("**suggested route for today:**")
        
        st.markdown(
            """
            <div style='height: 250px; background-color: #e0e0e0; display: flex; align-items: center; justify-content: center; border-radius: 10px; margin-top: 15px;'>
                <b>🗺️ [ INTERACTIVE MAP PLACEHOLDER ]</b>
            </div>
            """, 
            unsafe_allow_html=True
        )