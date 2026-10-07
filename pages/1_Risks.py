from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st


# --------------------------------------------------
# STYLING
# --------------------------------------------------

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
def load_data():
    data_dir = Path(__file__).resolve().parents[1] / "Analysis"

    risks = pd.read_csv(
        data_dir / "current_at_risk_accounts.csv",
        dtype={"account_id": str},
    )

    orders = pd.read_csv(
        data_dir / "order_lines.csv",
        dtype={
            "account_id": str,
            "order_id": str,
        },
    )

    orders["order_date"] = pd.to_datetime(
        orders["order_date"]
    )

    return risks, orders


risks, orders = load_data()

risks = risks.sort_values(
    "risk_score",
    ascending=False,
).reset_index(drop=True)

risks["churn_risk_pct"] = (
    risks["churn_probability"] * 100
)


# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.title("At-Risk Accounts")

st.write(
    "Explore the 50 highest-priority at-risk accounts. "
    "Accounts are ranked by Priority Score: "
    "predicted churn risk × customer value."
)

st.divider()


# --------------------------------------------------
# SUMMARY
# --------------------------------------------------

c1, c2, c3 = st.columns(3)

c1.metric(
    "Accounts flagged",
    len(risks),
)

c2.metric(
    "Average predicted churn risk",
    f"{risks['churn_risk_pct'].mean():.1f}%",
)

c3.metric(
    "Combined customer value",
    f"${risks['total_spend'].sum():,.0f}",
)

st.divider()


# --------------------------------------------------
# FILTERS
# --------------------------------------------------

st.subheader("Filter accounts")

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


filtered = risks[
    (risks["churn_risk_pct"] >= minimum_risk)
    & (risks["total_spend"] >= minimum_value)
].copy()


st.caption(
    f"Showing {len(filtered)} of "
    f"{len(risks)} at-risk accounts."
)


# --------------------------------------------------
# TABLE
# --------------------------------------------------

table = filtered[
    [
        "account_id",
        "churn_risk_pct",
        "total_spend",
        "risk_score",
    ]
].copy()

table = table.rename(
    columns={
        "account_id": "Account",
        "churn_risk_pct": "Predicted churn risk (%)",
        "total_spend": "Customer value ($)",
        "risk_score": "Priority score",
    }
)

table["Predicted churn risk (%)"] = (
    table["Predicted churn risk (%)"].round(1)
)

table["Customer value ($)"] = (
    table["Customer value ($)"].round(2)
)

table["Priority score"] = (
    table["Priority score"].round(0)
)

st.dataframe(
    table,
    use_container_width=True,
    hide_index=True,
    height=420,
)

st.caption(
    "A high churn probability alone does not automatically "
    "mean highest priority. Priority also considers the "
    "historical value of the account."
)

st.divider()


# --------------------------------------------------
# ACCOUNT DEEP DIVE
# --------------------------------------------------

st.header(
    "Account Risk Profile"
)

if filtered.empty:

    st.info(
        "No accounts match the selected filters."
    )

    st.stop()


selected_account = st.selectbox(
    "Select an account to investigate",
    filtered["account_id"].tolist(),
)


selected_risk = risks[
    risks["account_id"] == selected_account
].iloc[0]


account_orders = orders[
    orders["account_id"] == selected_account
].copy()

account_orders = account_orders.sort_values(
    "order_date"
)


# --------------------------------------------------
# ACCOUNT METRICS
# --------------------------------------------------

number_of_orders = account_orders[
    "order_id"
].nunique()

average_review = account_orders[
    "review_score"
].mean()

late_orders = account_orders[
    account_orders["is_late"] == True
]["order_id"].nunique()

latest_order_date = account_orders[
    "order_date"
].max()


m1, m2, m3, m4 = st.columns(4)

m1.metric(
    "Predicted churn risk",
    f"{selected_risk['churn_probability'] * 100:.1f}%",
)

m2.metric(
    "Customer value",
    f"${selected_risk['total_spend']:,.2f}",
)

m3.metric(
    "Historical orders",
    number_of_orders,
)

if pd.notna(average_review):

    m4.metric(
        "Average review",
        f"{average_review:.1f} / 5",
    )

else:

    m4.metric(
        "Average review",
        "No data",
    )


if pd.notna(latest_order_date):

    st.write(
        f"**Last order:** "
        f"{latest_order_date.strftime('%d %B %Y')}"
    )

else:

    st.write(
        "**Last order:** No order data"
    )


st.write(
    f"**Late deliveries:** {late_orders}"
)


# --------------------------------------------------
# ORDER HISTORY BY MONTH
# --------------------------------------------------

st.subheader(
    "Ordering behaviour"
)

monthly_orders = (
    account_orders
    .drop_duplicates("order_id")
    .set_index("order_date")
    .resample("MS")
    .size()
    .rename("Orders")
    .reset_index()
)

st.caption(
    "Monthly order count shows whether the customer's "
    "usual ordering rhythm has weakened or stopped."
)


# --------------------------------------------------
# DYNAMIC ORDER HISTORY CHART
# --------------------------------------------------

order_chart = (
    alt.Chart(monthly_orders)
    .mark_line(
        point=True,
        strokeWidth=3,
        color="#00843D",
    )
    .encode(
        x=alt.X(
            "order_date:T",
            title="Month",
            axis=alt.Axis(
                format="%b %Y",
                labelAngle=-45,
            ),
        ),
        y=alt.Y(
            "Orders:Q",
            title="Orders",
            scale=alt.Scale(
                zero=True
            ),
        ),
        tooltip=[
            alt.Tooltip(
                "order_date:T",
                title="Month",
                format="%B %Y",
            ),
            alt.Tooltip(
                "Orders:Q",
                title="Orders",
                format=".0f",
            ),
        ],
    )
    .properties(
        height=320
    )
    .interactive()
)

st.altair_chart(
    order_chart,
    use_container_width=True,
    theme="streamlit",
)


# --------------------------------------------------
# MONTHLY SPEND
# --------------------------------------------------

st.subheader("Monthly spend")

# Keep the original calculation that was already working
monthly_spend = (
    account_orders
    .groupby(
        account_orders["order_date"].dt.to_period("M")
    )["price"]
    .sum()
)

# Convert the result to a dataframe for Altair
monthly_spend_df = monthly_spend.reset_index()

monthly_spend_df.columns = [
    "month",
    "spend",
]

# Convert Period values to simple strings.
# This avoids Altair/Vega-Lite issues with pandas Period objects.
monthly_spend_df["month"] = (
    monthly_spend_df["month"]
    .astype(str)
)

monthly_spend_df["spend"] = pd.to_numeric(
    monthly_spend_df["spend"],
    errors="coerce",
)

monthly_spend_df = monthly_spend_df.dropna(
    subset=["spend"]
)


# --------------------------------------------------
# MONTHLY SPEND CHART
# --------------------------------------------------

spend_chart = (
    alt.Chart(monthly_spend_df)
    .mark_bar(
        color="#00843D",
        cornerRadiusTopLeft=3,
        cornerRadiusTopRight=3,
    )
    .encode(
        x=alt.X(
            "month:N",
            title="Month",
            sort=None,
            axis=alt.Axis(
                labelAngle=-45,
            ),
        ),
        y=alt.Y(
            "spend:Q",
            title="Spend ($)",
            scale=alt.Scale(
                zero=True,
            ),
        ),
        tooltip=[
            alt.Tooltip(
                "month:N",
                title="Month",
            ),
            alt.Tooltip(
                "spend:Q",
                title="Spend",
                format="$,.2f",
            ),
        ],
    )
    .properties(
        height=320
    )
)

st.altair_chart(
    spend_chart,
    use_container_width=True,
    theme="streamlit",
)

# --------------------------------------------------
# CUSTOMER EXPERIENCE
# --------------------------------------------------

st.subheader(
    "Customer experience"
)

experience_left, experience_right = (
    st.columns(2)
)

with experience_left:

    if pd.notna(
        average_review
    ):

        st.metric(
            "Average review score",
            f"{average_review:.1f} / 5",
        )

    else:

        st.write(
            "No review score available."
        )


with experience_right:

    st.metric(
        "Late deliveries",
        late_orders,
    )


# --------------------------------------------------
# EXPLANATION
# --------------------------------------------------

st.info(
    "This page explains the evidence behind the risk flag. "
    "For the recommended next action, use Today's Route."
)
