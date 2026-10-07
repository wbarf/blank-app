import streamlit as st

st.set_page_config(
    page_title="HEINEKEN Rep Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        [data-testid="stSidebar"] {
            background-color: #007A33 !important;
        }
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] div,
        [data-testid="stSidebar"] h1 {
            color: white !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

st.sidebar.title("Menu")

pages = [
    st.Page("pages/0_Dashboard.py", title="Today's Route", default=True),
    st.Page("pages/1_Risks.py", title="Risks"),
    st.Page("pages/2_Comments.py", title="Comments"),
    st.Page("pages/3_Actions.py", title="Actions"),
    st.Page("pages/4_Map.py", title="Map"),
]

navigation = st.navigation(pages)
navigation.run()
