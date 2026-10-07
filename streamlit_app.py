from pathlib import Path

import streamlit as st


# --------------------------------------------------
# PATHS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
LOGO_PATH = BASE_DIR / "assets" / "heineken_logo.png"


# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title="Heineken AI Sales Advisor",
    page_icon=str(LOGO_PATH),
    layout="wide",
    initial_sidebar_state="expanded",
)


# --------------------------------------------------
# GLOBAL STYLING
# --------------------------------------------------

st.markdown(
    """
    <style>

    /* ==================================================
       GENERAL APP
    ================================================== */

    .stApp {
        background-color: #eef2f0;
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 1400px;
    }

    h1 {
        font-weight: 700;
        letter-spacing: -0.02em;
        color: #202124;
    }

    h2,
    h3 {
        color: #202124;
    }

    p {
        color: #333333;
    }


    /* ==================================================
       STREAMLIT HEADER
    ================================================== */

    [data-testid="stHeader"] {
        background-color: #eef2f0 !important;
        border-bottom: none !important;
    }

    /*
    Keep the toolbar alive because Streamlit uses it
    for the collapsed-sidebar control.
    */
    [data-testid="stToolbar"] {
        visibility: visible !important;
        background: transparent !important;
    }

    /*
    Make sure the button to reopen the sidebar
    stays visible.
    */
    [data-testid="stSidebarCollapsedControl"] {
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
    }

    [data-testid="stSidebarCollapsedControl"] button {
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
    }

    /*
    Hide Streamlit deploy control.
    */
    [data-testid="stAppDeployButton"] {
        display: none !important;
    }

    #MainMenu {
        visibility: hidden;
    }

    footer {
        visibility: hidden;
    }


    /* ==================================================
       SIDEBAR
    ================================================== */

    [data-testid="stSidebar"] {
        background-color: #e2eee7;
        border-right: 1px solid #cbdcd2;
    }

    [data-testid="stSidebar"] > div:first-child {
        padding-top: 1.2rem;
    }

    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label {
        color: #242424 !important;
    }

    [data-testid="stSidebar"] a {
        color: #242424 !important;
        text-decoration: none;
    }


    /* ==================================================
       NAVIGATION
    ================================================== */

    [data-testid="stSidebarNav"] a {
        border-radius: 8px;
        margin: 4px 10px;
        padding-top: 10px;
        padding-bottom: 10px;
    }

    [data-testid="stSidebarNav"] a:hover {
        background-color: #d3e4da;
    }

    [data-testid="stSidebarNav"] a[aria-current="page"] {
        background-color: #007A33;
    }

    [data-testid="stSidebarNav"] a[aria-current="page"] span {
        color: #ffffff !important;
        font-weight: 600;
    }


    /* ==================================================
       METRICS
    ================================================== */

    [data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #d3ddd7;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.06);
    }

    [data-testid="stMetricLabel"] {
        color: #555555;
    }

    [data-testid="stMetricValue"] {
        color: #202124;
        font-weight: 700;
    }


    /* ==================================================
       BUTTONS - HEINEKEN RED
    ================================================== */

    div.stButton > button {
        background-color: #E3001B;
        color: #ffffff;
        border: none;
        border-radius: 8px;
        font-weight: 650;
        padding: 0.6rem 1.1rem;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
    }

    div.stButton > button:hover {
        background-color: #c80018;
        color: #ffffff;
        border: none;
    }

    div.stButton > button:focus {
        background-color: #c80018;
        color: #ffffff;
        border: none;
        box-shadow: none;
    }


    /* ==================================================
       SELECTBOXES
    ================================================== */

    div[data-baseweb="select"] > div {
        border-radius: 8px;
        background-color: #ffffff;
    }


    /* ==================================================
       CARDS / CONTAINERS
    ================================================== */

    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #ffffff;
        border-radius: 10px;
        border: 1px solid #d3ddd7;
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.05);
    }

    [data-testid="stExpander"] {
        background-color: #ffffff;
        border-radius: 10px;
        border-color: #d3ddd7;
    }

    [data-testid="stAlert"] {
        border-radius: 9px;
    }


    /* ==================================================
       TABLES
    ================================================== */

    [data-testid="stDataFrame"] {
        background-color: #ffffff;
        border: 1px solid #d3ddd7;
        border-radius: 9px;
        overflow: hidden;
    }


    /* ==================================================
       DIVIDERS
    ================================================== */

    hr {
        border-color: #d3ddd7;
    }


    /* ==================================================
       HIDE STREAMLIT RUNNING / STOP INDICATOR
    ================================================== */

    [data-testid="stStatusWidget"] {
        display: none !important;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# SIDEBAR BRANDING
# --------------------------------------------------

with st.sidebar:

    if LOGO_PATH.exists():

        spacer_left, logo_col, spacer_right = st.columns(
            [1, 3, 1]
        )

        with logo_col:
            st.image(
                str(LOGO_PATH),
                use_container_width=True,
            )

    else:

        st.markdown(
            """
            <div style="
                color:#007A33;
                font-size:28px;
                font-weight:700;
                text-align:center;
                margin-bottom:6px;
            ">
                Heineken
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        """
        <div style="
            text-align:center;
            color:#666666;
            font-size:13px;
            font-weight:500;
            margin-top:-8px;
            margin-bottom:20px;
        ">
            AI Sales Advisor
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()


# --------------------------------------------------
# NAVIGATION
# --------------------------------------------------

pages = [
    st.Page(
        "pages/0_Dashboard.py",
        title="Today's Route",
        default=True,
    ),

    st.Page(
        "pages/1_Risks.py",
        title="At-Risk Accounts",
    ),

    st.Page(
        "pages/4_Map.py",
        title="Risk Map",
    ),
]

navigation = st.navigation(pages)

navigation.run()