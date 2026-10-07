from pathlib import Path

import pandas as pd
import pydeck as pdk
import streamlit as st
from google import genai


# --------------------------------------------------
# DATA
# --------------------------------------------------

@st.cache_data
def load_app_data():
    data_dir = Path(__file__).resolve().parents[1] / "Analysis"

    risks = pd.read_csv(
        data_dir / "current_at_risk_accounts.csv",
        dtype={"account_id": str},
    )

    lines = pd.read_csv(
        data_dir / "order_lines.csv",
        dtype={"account_id": str, "order_id": str},
    )
    lines["order_date"] = pd.to_datetime(lines["order_date"])

    reviews = pd.read_csv(
        data_dir / "order_reviews.csv",
        dtype={"order_id": str},
    )

    locations = pd.read_csv(
        data_dir / "geolocation.csv",
        dtype={"account_id": str},
        usecols=["account_id", "lat", "lng", "city", "state"],
    )

    risks = risks.merge(
        locations,
        on="account_id",
        how="left",
    )

    return risks, lines, reviews


risks_df, lines_df, reviews_df = load_app_data()

risks_df = risks_df.sort_values(
    "risk_score",
    ascending=False,
).reset_index(drop=True)

top_accounts = risks_df.head(10).copy()


# --------------------------------------------------
# PAGE HEADER
# --------------------------------------------------

st.title("Today's Route")

st.write(
    "Focus on the highest-priority at-risk accounts. "
    "Priority Score combines predicted churn risk with customer value."
)

st.divider()


# --------------------------------------------------
# SUMMARY METRICS
# --------------------------------------------------

metric1, metric2, metric3 = st.columns(3)

metric1.metric(
    "At-risk accounts",
    len(risks_df),
)

metric2.metric(
    "Highest predicted churn risk",
    f"{risks_df['churn_probability'].max() * 100:.1f}%",
)

metric3.metric(
    "Highest priority score",
    f"{risks_df['risk_score'].max():,.0f}",
)

st.divider()


# --------------------------------------------------
# TOP SECTION
# --------------------------------------------------

left, right = st.columns([1, 1.2])


# --------------------------------------------------
# TOP 10 LIST
# --------------------------------------------------

with left:

    st.subheader("Top 10 Priority Accounts")

    st.caption(
        "These accounts should receive attention first."
    )

    with st.container(height=540):

        for _, row in top_accounts.iterrows():

            account_id = row["account_id"]
            churn_risk = row["churn_probability"] * 100
            risk_score = row["risk_score"]
            customer_value = row["total_spend"]

            with st.container(border=True):

                st.markdown(
                    f"### {account_id}"
                )

                c1, c2 = st.columns(2)

                c1.metric(
                    "Churn risk",
                    f"{churn_risk:.1f}%",
                )

                c2.metric(
                    "Priority score",
                    f"{risk_score:,.0f}",
                )

                st.write(
                    f"**Customer value:** ${customer_value:,.2f}"
                )

                if pd.notna(row["city"]):
                    st.write(
                        f"**Location:** {str(row['city']).title()}, {row['state']}"
                    )


# --------------------------------------------------
# GEOLOCATION MAP
# --------------------------------------------------

with right:

    st.subheader("Suggested Route Area")

    st.caption(
        "The map shows today's 10 highest-priority accounts."
    )

    map_data = top_accounts.dropna(
        subset=["lat", "lng"]
    ).copy()

    map_data["lat"] = pd.to_numeric(
        map_data["lat"],
        errors="coerce",
    )

    map_data["lng"] = pd.to_numeric(
        map_data["lng"],
        errors="coerce",
    )

    map_data["churn_pct"] = (
        map_data["churn_probability"] * 100
    ).round(1)

    map_data["risk_score_display"] = (
        map_data["risk_score"]
        .round(0)
        .astype(int)
    )

    score_min = map_data["risk_score"].min()
    score_max = map_data["risk_score"].max()

    if score_max == score_min:
        map_data["radius"] = 18
    else:
        map_data["radius"] = (
            12
            + (
                (map_data["risk_score"] - score_min)
                / (score_max - score_min)
            )
            * 18
        )

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=map_data,
        get_position="[lng, lat]",
        get_radius="radius",
        radius_units="pixels",
        radius_min_pixels=10,
        radius_max_pixels=32,
        get_fill_color=[0, 122, 51, 190],
        get_line_color=[255, 255, 255],
        line_width_min_pixels=1,
        stroked=True,
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
        map_style=(
            "https://basemaps.cartocdn.com/gl/"
            "positron-gl-style/style.json"
        ),
        tooltip={
            "html": (
                "<b>{account_id}</b><br/>"
                "{city}, {state}<br/>"
                "Churn risk: {churn_pct}%<br/>"
                "Priority score: {risk_score_display}"
            )
        },
    )

    st.pydeck_chart(
        deck,
        use_container_width=True,
        height=540,
    )

    st.caption(
        "Use the Risk Map page for the full overview of all at-risk accounts."
    )


st.divider()


# --------------------------------------------------
# ACCOUNT ACTION SECTION
# --------------------------------------------------

st.header("Account Action")

st.write(
    "Select one of today's priority accounts to review its recent activity "
    "and generate an AI-supported next action."
)

selected_account = st.selectbox(
    "Select account",
    top_accounts["account_id"].tolist(),
)


selected_risk = top_accounts[
    top_accounts["account_id"] == selected_account
].iloc[0]

account_orders = lines_df[
    lines_df["account_id"] == selected_account
].copy()

account_orders = account_orders.sort_values(
    "order_date",
    ascending=False,
)


# --------------------------------------------------
# ACCOUNT INFORMATION
# --------------------------------------------------

latest_order = account_orders.iloc[0]

latest_order_id = latest_order["order_id"]

latest_order_lines = account_orders[
    account_orders["order_id"] == latest_order_id
]

latest_order_date = latest_order[
    "order_date"
].strftime("%d %B %Y")

latest_order_total = latest_order_lines[
    "price"
].sum()

freight_total = latest_order_lines[
    "freight_value"
].sum()

was_late = latest_order_lines[
    "is_late"
].any()

number_of_orders = account_orders[
    "order_id"
].nunique()

average_review = account_orders[
    "review_score"
].mean()

order_review = reviews_df[
    reviews_df["order_id"] == latest_order_id
]

comment = "No written feedback provided."

if not order_review.empty:

    msg = order_review.iloc[0][
        "review_comment_message"
    ]

    if pd.notna(msg):
        comment = str(msg)


# --------------------------------------------------
# ACCOUNT SUMMARY
# --------------------------------------------------

st.subheader(f"Account {selected_account}")

a, b, c = st.columns(3)

a.metric(
    "Churn risk",
    f"{selected_risk['churn_probability'] * 100:.1f}%",
)

b.metric(
    "Customer value",
    f"${selected_risk['total_spend']:,.2f}",
)

c.metric(
    "Priority score",
    f"{selected_risk['risk_score']:,.0f}",
)


detail_left, detail_right = st.columns(2)

with detail_left:

    st.markdown("### Recent activity")

    st.write(
        f"**Last order:** {latest_order_date}"
    )

    st.write(
        f"**Historical orders:** {number_of_orders}"
    )

    st.write(
        f"**Latest order value:** ${latest_order_total:,.2f}"
    )

    st.write(
        f"**Freight:** ${freight_total:,.2f}"
    )

    if was_late:
        st.warning(
            "The latest delivery was late."
        )
    else:
        st.success(
            "The latest delivery was on time."
        )


with detail_right:

    st.markdown("### Customer experience")

    if pd.notna(average_review):
        st.write(
            f"**Average review score:** "
            f"{average_review:.1f} / 5"
        )
    else:
        st.write(
            "**Average review score:** No review data"
        )

    st.write(
        "**Latest customer comment:**"
    )

    st.write(comment)


# --------------------------------------------------
# GEMINI ACTION GENERATOR
# --------------------------------------------------

st.markdown("### AI Recommendation")

st.write(
    "Gemini turns the churn prediction and account history into a practical "
    "next step for the sales representative."
)

if st.button(
    "Generate AI Recommendation",
    type="primary",
):

    try:

        client = genai.Client(
            api_key=st.secrets["GEMINI_API_KEY"]
        )

        review_value = (
            f"{average_review:.1f} out of 5"
            if pd.notna(average_review)
            else "No review data available"
        )

        prompt = f"""
You are an AI sales advisor supporting a Heineken sales representative.

The account has already been identified as a priority account by a churn
prediction model.

Use the information below to recommend what the sales representative should
do next.

ACCOUNT DATA

Account ID: {selected_account}
Location: {str(selected_risk['city']).title()}, {selected_risk['state']}
Predicted churn risk: {selected_risk['churn_probability'] * 100:.1f}%
Historical customer value: ${selected_risk['total_spend']:,.2f}
Priority score: {selected_risk['risk_score']:,.0f}
Last order date: {latest_order_date}
Historical number of orders: {number_of_orders}
Latest order value: ${latest_order_total:,.2f}
Latest freight cost: ${freight_total:,.2f}
Latest delivery was late: {was_late}
Average review score: {review_value}
Latest written feedback: {comment}

Create a concise sales recommendation using exactly these headings:

### Recommended action
Give one concrete next action for the sales representative.

### Why this account needs attention
Explain in 2 or 3 sentences why this account deserves attention.

### Talking points
Give exactly 3 short talking points for a call or visit.

### Suggested win-back message
Write a short message that could be sent directly to the customer.

RULES

- Only use the information provided above.
- Do not invent facts.
- Do not invent products, discounts or promotions.
- Do not assume that a late delivery caused the churn risk.
- A churn probability is a prediction, not a certainty.
- Do not invent reasons why the customer reduced or stopped ordering.
- Keep the answer concise.
- Use professional, natural English.
- Refer to the company as Heineken.
"""

        with st.spinner(
            "Generating recommendation..."
        ):

            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt,
                config={
                    "max_output_tokens": 500,
                },
            )

        st.markdown(response.text)

    except KeyError:

        st.error(
            "Gemini API key not found."
        )

    except Exception as e:

        st.error(
            f"Could not generate the AI recommendation: {e}"
        )