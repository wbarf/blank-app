from pathlib import Path

import pandas as pd
import pydeck as pdk
import streamlit as st

st.title("Risk Map Across Brazil")
st.write(
    "Each bubble represents a risk account. Higher risk scores produce larger "
    "bubbles; colors show relative risk within the accounts listed."
)


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
        usecols=["account_id", "lat", "lng", "city", "state"],
    )

    return risks.merge(
        locations,
        on="account_id",
        how="left",
        validate="one_to_one",
    )


try:
    risks = load_risk_locations()
except FileNotFoundError as exc:
    st.error(f"Map data file not found: {exc.filename}")
    st.stop()

if risks.empty:
    st.info("There are no risk accounts to display.")
    st.stop()

risks["lat"] = pd.to_numeric(risks["lat"], errors="coerce")
risks["lng"] = pd.to_numeric(risks["lng"], errors="coerce")
risks["risk_score"] = pd.to_numeric(risks["risk_score"], errors="coerce")
risks["churn_probability"] = pd.to_numeric(
    risks["churn_probability"], errors="coerce"
)
risks["total_spend"] = pd.to_numeric(risks["total_spend"], errors="coerce")

mapped_risks = risks.dropna(subset=["lat", "lng", "risk_score"]).copy()
missing_coordinates = len(risks) - len(mapped_risks)

if mapped_risks.empty:
    st.error("No risk accounts have valid coordinates and risk scores.")
    st.stop()

low_cut = mapped_risks["risk_score"].quantile(1 / 3)
high_cut = mapped_risks["risk_score"].quantile(2 / 3)

mapped_risks["risk_band"] = "Medium"
mapped_risks.loc[mapped_risks["risk_score"] < low_cut, "risk_band"] = "Lower"
mapped_risks.loc[mapped_risks["risk_score"] >= high_cut, "risk_band"] = "Higher"

band_colors = {
    "Lower": [42, 157, 143],
    "Medium": [244, 162, 97],
    "Higher": [214, 40, 40],
}
mapped_risks["color"] = mapped_risks["risk_band"].map(band_colors)

score_min = mapped_risks["risk_score"].min()
score_range = mapped_risks["risk_score"].max() - score_min
if score_range == 0:
    mapped_risks["radius_px"] = 16.0
else:
    mapped_risks["radius_px"] = (
        8 + (mapped_risks["risk_score"] - score_min) / score_range * 24
    )

mapped_risks["churn_pct"] = (
    mapped_risks["churn_probability"].mul(100).round(1).fillna(0)
)
mapped_risks["risk_score"] = mapped_risks["risk_score"].round(0).astype(int)
mapped_risks["total_spend"] = mapped_risks["total_spend"].round(2).fillna(0)

col1, col2, col3 = st.columns(3)
col1.metric("Risk accounts plotted", f"{len(mapped_risks):,}")
col2.metric("Highest risk score", f"{mapped_risks['risk_score'].max():,.0f}")
col3.metric("Missing coordinates", f"{missing_coordinates:,}")

st.markdown(
    """
    <div style="display:flex;gap:1.5rem;align-items:center;margin:0.5rem 0 1rem;">
      <span><span style="color:#2a9d8f;">●</span> Lower relative risk</span>
      <span><span style="color:#f4a261;">●</span> Medium relative risk</span>
      <span><span style="color:#d62828;">●</span> Higher relative risk</span>
    </div>
    """,
    unsafe_allow_html=True,
)

layer = pdk.Layer(
    "ScatterplotLayer",
    data=mapped_risks,
    get_position="[lng, lat]",
    get_radius="radius_px",
    radius_units="pixels",
    radius_min_pixels=6,
    radius_max_pixels=34,
    get_fill_color="color",
    get_line_color=[255, 255, 255, 220],
    line_width_min_pixels=1,
    stroked=True,
    opacity=0.78,
    pickable=True,
)

deck = pdk.Deck(
    layers=[layer],
    initial_view_state=pdk.ViewState(
        latitude=-14.235,
        longitude=-51.925,
        zoom=3.1,
        pitch=0,
    ),
    map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
    tooltip={
        "html": (
            "<b>{account_id}</b><br/>"
            "{city}, {state}<br/>"
            "Risk score: {risk_score}<br/>"
            "Churn probability: {churn_pct}%<br/>"
            "Total spend: {total_spend}"
        ),
        "style": {"backgroundColor": "white", "color": "#222"},
    },
)

st.pydeck_chart(deck, use_container_width=True, height=680)