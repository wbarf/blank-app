import pandas as pd
import streamlit as st
from google import genai

st.title("AI Action Generator")

st.write(
    "Select an at-risk account to generate a personalised recommendation "
    "for the sales representative."
)

# --------------------------------------------------
# Load data
# --------------------------------------------------

risks = pd.read_csv(
    "Analysis/current_at_risk_accounts.csv",
    dtype={"account_id": str}
)

orders = pd.read_csv(
    "Analysis/order_lines.csv",
    dtype={"account_id": str, "order_id": str}
)

orders["order_date"] = pd.to_datetime(orders["order_date"])

# Highest-priority accounts first
risks = risks.sort_values(
    "risk_score",
    ascending=False
)

# --------------------------------------------------
# Select account
# --------------------------------------------------

selected_account = st.selectbox(
    "Select an at-risk account",
    risks["account_id"].tolist()
)

risk_row = risks[
    risks["account_id"] == selected_account
].iloc[0]

account_orders = orders[
    orders["account_id"] == selected_account
].copy()

account_orders = account_orders.sort_values(
    "order_date",
    ascending=False
)

# --------------------------------------------------
# Calculate account information
# --------------------------------------------------

latest_order_date = account_orders["order_date"].max()

number_of_orders = account_orders["order_id"].nunique()

average_review = account_orders["review_score"].mean()

late_deliveries = account_orders[
    account_orders["is_late"] == True
]["order_id"].nunique()

churn_probability = risk_row["churn_probability"] * 100

customer_value = risk_row["total_spend"]

priority_score = risk_row["risk_score"]

city = account_orders["city"].dropna().iloc[0]

state = account_orders["state"].dropna().iloc[0]

# --------------------------------------------------
# Show account summary
# --------------------------------------------------

st.subheader(f"Account {selected_account}")

st.caption(
    f"{city.title()}, {state}"
)

col1, col2, col3 = st.columns(3)

col1.metric(
    "Churn risk",
    f"{churn_probability:.1f}%"
)

col2.metric(
    "Customer value",
    f"${customer_value:,.2f}"
)

col3.metric(
    "Priority score",
    f"{priority_score:,.0f}"
)

st.markdown("### Account information")

st.write(
    f"**Last order:** {latest_order_date.strftime('%d %B %Y')}"
)

st.write(
    f"**Historical orders:** {number_of_orders}"
)

if pd.notna(average_review):
    st.write(
        f"**Average review score:** {average_review:.1f} / 5"
    )
else:
    st.write(
        "**Average review score:** No review data available"
    )

st.write(
    f"**Late deliveries:** {late_deliveries}"
)

# --------------------------------------------------
# AI recommendation
# --------------------------------------------------

st.markdown("### AI Recommendation")

st.write(
    "Gemini uses the account data above to create a concrete next step "
    "for the sales representative."
)

if st.button(
    "Generate AI Recommendation",
    type="primary"
):

    try:
        client = genai.Client(
            api_key=st.secrets["GEMINI_API_KEY"]
        )

        review_text = (
            f"{average_review:.1f} out of 5"
            if pd.notna(average_review)
            else "No review data available"
        )

        prompt = f"""
You are an AI sales advisor supporting a Heineken sales representative.

Your job is to turn customer risk information into a practical next action.

The account has already been identified and prioritised by a churn prediction model.

ACCOUNT DATA

Account ID: {selected_account}
Location: {city.title()}, {state}
Predicted churn risk: {churn_probability:.1f}%
Historical customer value: ${customer_value:,.2f}
Priority score: {priority_score:,.0f}
Last order date: {latest_order_date.strftime('%d %B %Y')}
Historical number of orders: {number_of_orders}
Average review score: {review_text}
Number of late deliveries: {late_deliveries}

INSTRUCTIONS

Create a short, practical recommendation for the sales representative.

Use exactly these four headings:

### Recommended action
Give one clear action the sales representative should take next.

### Why this account needs attention
Explain the recommendation in 2 or 3 sentences using the supplied data.

### Talking points
Give exactly 3 short talking points the representative can use during a call or visit.

### Suggested win-back message
Write a short message that the representative could send directly to the customer.

IMPORTANT RULES

- Only use information provided above.
- Do not invent facts.
- Do not invent products, discounts or promotions.
- Do not claim that a late delivery caused the churn risk.
- A churn prediction is a risk estimate, not a certainty.
- Do not make up reasons why the customer stopped ordering.
- Keep the recommendation concise.
- Use professional but natural English.
- Refer to the company as Heineken, never HEINEKEN.
"""

        with st.spinner(
            "Generating recommendation..."
        ):

            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt,
                config={
                    "max_output_tokens": 500
                }
            )

        st.markdown(response.text)

    except KeyError:
        st.error(
            "Gemini API key not found. Add GEMINI_API_KEY to "
            ".streamlit/secrets.toml."
        )

    except Exception as e:
        st.error(
            f"Could not generate the AI recommendation: {e}"
        )