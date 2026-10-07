from pathlib import Path

import pandas as pd
import pydeck as pdk
import streamlit as st

st.markdown(

    """

    <style>

    h1, h2, h3 {

        color: #00843D !important;

    }

    </style>

    """,

    unsafe_allow_html=True,

)

# --------------------------------------------------
# DATA
# --------------------------------------------------

@st.cache_data
def load_risk_locations():
    data_dir = Path(__file__).resolve().parents[1] / "Analysis"

    risks = pd.read_csv(
        data_dir / "current_at_risk_accounts.csv",
        dtype={"account_id": str},
    )

    locations = pd.read_csv(
        data_dir / "geolocation.csv",
        dtype={"account_id": str},
        usecols=[
            "account_id",
            "lat",
            "lng",
            "city",
            "state",
        ],
    )

    return risks.merge(
        locations,
        on="account_id",
        how="left",
    )


try:
    risks = load_risk_locations()

except FileNotFoundError as exc:
    st.error(
        f"Map data file not found: {exc.filename}"
    )
    st.stop()


# --------------------------------------------------
# PREPARE DATA
# --------------------------------------------------

risks["lat"] = pd.to_numeric(
    risks["lat"],
    errors="coerce",
)

risks["lng"] = pd.to_numeric(
    risks["lng"],
    errors="coerce",
)

risks["risk_score"] = pd.to_numeric(
    risks["risk_score"],
    errors="coerce",
)

risks["churn_probability"] = pd.to_numeric(
    risks["churn_probability"],
    errors="coerce",
)

risks["total_spend"] = pd.to_numeric(
    risks["total_spend"],
    errors="coerce",
)

risks["churn_pct"] = (
    risks["churn_probability"] * 100
)

mapped_risks = risks.dropna(
    subset=["lat", "lng", "risk_score"]
).copy()

missing_coordinates = (
    len(risks) - len(mapped_risks)
)

if mapped_risks.empty:
    st.error(
        "No at-risk accounts have valid map coordinates."
    )
    st.stop()


# --------------------------------------------------
# PAGE HEADER
# --------------------------------------------------

st.title("Risk Map")

st.write(
    "Explore where the identified at-risk accounts are located. "
    "Marker colour represents predicted churn risk, while marker size "
    "represents Priority Score."
)

st.divider()


# --------------------------------------------------
# SUMMARY METRICS
# --------------------------------------------------

m1, m2, m3 = st.columns(3)

m1.metric(
    "Accounts on map",
    len(mapped_risks),
)

m2.metric(
    "Highest priority score",
    f"{mapped_risks['risk_score'].max():,.0f}",
)

m3.metric(
    "Missing coordinates",
    missing_coordinates,
)

st.divider()


# --------------------------------------------------
# FILTERS
# --------------------------------------------------

st.subheader("Filter map")

filter1, filter2 = st.columns(2)

with filter1:
    minimum_risk = st.slider(
        "Minimum predicted churn risk",
        min_value=0,
        max_value=100,
        value=0,
        step=5,
        format="%d%%",
    )

with filter2:
    minimum_value = st.number_input(
        "Minimum customer value ($)",
        min_value=0,
        value=0,
        step=500,
    )


filtered = mapped_risks[
    (
        mapped_risks["churn_pct"]
        >= minimum_risk
    )
    &
    (
        mapped_risks["total_spend"]
        >= minimum_value
    )
].copy()


st.caption(
    f"Showing {len(filtered)} of "
    f"{len(mapped_risks)} mapped at-risk accounts."
)

if filtered.empty:
    st.info(
        "No accounts match the selected filters."
    )
    st.stop()


# --------------------------------------------------
# MAP VISUAL VARIABLES
# --------------------------------------------------

score_min = filtered["risk_score"].min()
score_max = filtered["risk_score"].max()

if score_max == score_min:
    filtered["radius"] = 13
else:
    filtered["radius"] = (
        8
        + (
            (
                filtered["risk_score"]
                - score_min
            )
            /
            (
                score_max
                - score_min
            )
        )
        * 14
    )


def risk_color(churn_probability):

    if churn_probability >= 0.80:
        return [227, 0, 27, 205]

    elif churn_probability >= 0.50:
        return [240, 130, 30, 195]

    return [0, 122, 51, 190]


filtered["color"] = (
    filtered["churn_probability"]
    .apply(risk_color)
)

filtered["churn_display"] = (
    filtered["churn_pct"]
    .round(1)
)

filtered["priority_display"] = (
    filtered["risk_score"]
    .round(0)
    .astype(int)
)

filtered["value_display"] = (
    filtered["total_spend"]
    .round(2)
)


# --------------------------------------------------
# LEGEND
# --------------------------------------------------

legend1, legend2, legend3 = st.columns(3)

with legend1:
    st.markdown(
        "🟢 **Below 50%** predicted churn risk"
    )

with legend2:
    st.markdown(
        "🟠 **50–79.9%** predicted churn risk"
    )

with legend3:
    st.markdown(
        "🔴 **80%+** predicted churn risk"
    )

st.caption(
    "Marker size reflects Priority Score, which combines predicted churn risk "
    "with customer value."
)


# --------------------------------------------------
# MAP
# --------------------------------------------------

layer = pdk.Layer(
    "ScatterplotLayer",
    data=filtered,
    get_position="[lng, lat]",
    get_radius="radius",
    radius_units="pixels",
    radius_min_pixels=7,
    radius_max_pixels=24,
    get_fill_color="color",
    get_line_color=[255, 255, 255],
    line_width_min_pixels=1,
    stroked=True,
    pickable=True,
)


deck = pdk.Deck(
    layers=[layer],

    initial_view_state=pdk.ViewState(
        latitude=-15.5,
        longitude=-51.5,
        zoom=3.25,
        pitch=0,
    ),

    map_style=(
        "https://basemaps.cartocdn.com/gl/"
        "positron-gl-style/style.json"
    ),

    tooltip={
        "html": (
            "<b>{account_id}</b><br/>"
            "{city}, {state}<br/><br/>"
            "Predicted churn risk: "
            "<b>{churn_display}%</b><br/>"
            "Customer value: "
            "<b>${value_display}</b><br/>"
            "Priority score: "
            "<b>{priority_display}</b>"
        ),

        "style": {
            "backgroundColor": "white",
            "color": "#222222",
        },
    },
)


st.pydeck_chart(
    deck,
    use_container_width=True,
    height=650,
)


# --------------------------------------------------
# EXPLANATION
# --------------------------------------------------

st.info(
    "The map helps the sales representative identify clusters of "
    "high-priority accounts that could be combined into the same visit route. "
    "Today's Route focuses on the 10 accounts that should receive attention first."
)
