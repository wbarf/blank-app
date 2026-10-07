from pathlib import Path

import pandas as pd
import pydeck as pdk
import streamlit as st
import streamlit.components.v1 as components
from google import genai
from google.genai import types


# --------------------------------------------------
# STYLING
# --------------------------------------------------

st.markdown(
    """
    <style>
    h1, h2, h3 {
        color: #00843D !important;
    }

    /* White text on primary/red buttons */
    button[kind="primary"],
    button[kind="primary"] p,
    button[kind="primary"] span {
        color: white !important;
    }

    /* Green "View on map" buttons */
    div[class*="st-key-map_"] button {
        background-color: #00843D !important;
        border-color: #00843D !important;
        color: white !important;
    }

    div[class*="st-key-map_"] button p,
    div[class*="st-key-map_"] button span {
        color: white !important;
    }

    div[class*="st-key-map_"] button:hover {
        background-color: #006B31 !important;
        border-color: #006B31 !important;
        color: white !important;
    }

    /* Green "Show all accounts" button */
    div[class*="st-key-show_all_accounts"] button {
        background-color: #00843D !important;
        border-color: #00843D !important;
        color: white !important;
    }

    div[class*="st-key-show_all_accounts"] button p,
    div[class*="st-key-show_all_accounts"] button span {
        color: white !important;
    }

    div[class*="st-key-show_all_accounts"] button:hover {
        background-color: #006B31 !important;
        border-color: #006B31 !important;
        color: white !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


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

    lines["order_date"] = pd.to_datetime(
        lines["order_date"]
    )

    reviews = pd.read_csv(
        data_dir / "order_reviews.csv",
        dtype={"order_id": str},
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

    risks = risks.merge(
        locations,
        on="account_id",
        how="left",
    )

    return risks, lines, reviews


# --------------------------------------------------
# COMMENT TRANSLATION
# --------------------------------------------------

@st.cache_data
def translate_comment(comment):

    if comment == "No written feedback provided.":
        return comment

    try:

        client = genai.Client(
            api_key=st.secrets["GEMINI_API_KEY"],
            http_options=types.HttpOptions(
                timeout=10_000
            ),
        )

        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=(
                "Translate the following Brazilian Portuguese "
                "customer review into natural English. "
                "Return only the English translation. "
                "Do not add an explanation.\n\n"
                f"{comment}"
            ),
            config={
                "max_output_tokens": 100,
                "thinking_config": {
                    "thinking_level": "low",
                },
            },
        )

        return response.text.strip()

    except Exception:

        return comment


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

risks_df, lines_df, reviews_df = load_app_data()

risks_df = risks_df.sort_values(
    "risk_score",
    ascending=False,
).reset_index(drop=True)

top_accounts = risks_df.head(10).copy()

account_options = (
    top_accounts["account_id"].tolist()
)


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "selected_account" not in st.session_state:
    st.session_state.selected_account = (
        account_options[0]
    )

if "map_account" not in st.session_state:
    st.session_state.map_account = None

if "scroll_request" not in st.session_state:
    st.session_state.scroll_request = 0

if "last_scroll_request" not in st.session_state:
    st.session_state.last_scroll_request = 0

if "map_scroll_request" not in st.session_state:
    st.session_state.map_scroll_request = 0

if "last_map_scroll_request" not in st.session_state:
    st.session_state.last_map_scroll_request = 0


# --------------------------------------------------
# PAGE HEADER
# --------------------------------------------------

st.title("Today's Route")

st.write(
    "Focus on the highest-priority at-risk accounts. "
    "Priority Score combines predicted churn risk "
    "with customer value."
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

left, right = st.columns(
    [1, 1.2]
)


# --------------------------------------------------
# TOP 10 LIST
# --------------------------------------------------

with left:

    st.subheader(
        "Top 10 Priority Accounts"
    )

    st.caption(
        "Select an account to view its details "
        "or location."
    )

    with st.container(
        height=540
    ):

        for _, row in top_accounts.iterrows():

            account_id = row["account_id"]

            churn_risk = (
                row["churn_probability"] * 100
            )

            risk_score = row["risk_score"]

            customer_value = (
                row["total_spend"]
            )

            with st.container(
                border=True
            ):

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
                    f"**Customer value:** "
                    f"${customer_value:,.2f}"
                )

                if pd.notna(
                    row["city"]
                ):

                    st.write(
                        f"**Location:** "
                        f"{str(row['city']).title()}, "
                        f"{row['state']}"
                    )

                button_left, button_right = (
                    st.columns(2)
                )

                # ------------------------------
                # VIEW DETAILS
                # ------------------------------

                with button_left:

                    if st.button(
                        "View details →",
                        key=f"view_{account_id}",
                        use_container_width=True,
                        type="primary",
                    ):

                        st.session_state.selected_account = (
                            account_id
                        )

                        st.session_state.scroll_request += 1

                        st.rerun()

                # ------------------------------
                # VIEW ON MAP
                # ------------------------------

                with button_right:

                    location_available = (
                        pd.notna(row["lat"])
                        and pd.notna(row["lng"])
                    )

                    if st.button(
                        "View on map",
                        key=f"map_{account_id}",
                        use_container_width=True,
                        disabled=not location_available,
                    ):

                        st.session_state.map_account = (
                            account_id
                        )

                        st.session_state.map_scroll_request += 1

                        st.rerun()


# --------------------------------------------------
# GEOLOCATION MAP
# --------------------------------------------------

with right:

    st.subheader(
        "Suggested Route Area",
        anchor="route-map",
    )


    # --------------------------------------------------
    # AUTOMATIC SCROLL TO MAP
    # --------------------------------------------------

    if (
        st.session_state.map_scroll_request
        != st.session_state.last_map_scroll_request
    ):

        map_scroll_number = (
            st.session_state.map_scroll_request
        )

        components.html(
            f"""
            <script>
            (function() {{

                const requestId = {map_scroll_number};

                function scrollToMap() {{

                    const doc =
                        window.parent.document;

                    const target =
                        doc.getElementById(
                            "route-map"
                        );

                    if (target) {{

                        target.scrollIntoView({{
                            behavior: "smooth",
                            block: "start"
                        }});

                        return;
                    }}

                    setTimeout(
                        scrollToMap,
                        100
                    );
                }}

                setTimeout(
                    scrollToMap,
                    250
                );

            }})();
            </script>
            """,
            height=0,
        )

        st.session_state.last_map_scroll_request = (
            st.session_state.map_scroll_request
        )


    # --------------------------------------------------
    # MAP HEADER / BACK BUTTON
    # --------------------------------------------------

    if (
        st.session_state.map_account
        is not None
    ):

        map_header_left, map_header_right = (
            st.columns([1.5, 1])
        )

        with map_header_left:

            st.caption(
                f"Showing Account "
                f"{st.session_state.map_account}"
            )

        with map_header_right:

            if st.button(
                "← Show all accounts",
                key="show_all_accounts",
                use_container_width=True,
            ):

                st.session_state.map_account = None

                st.rerun()

    else:

        st.caption(
            "The map shows today's 10 "
            "highest-priority accounts."
        )


    # --------------------------------------------------
    # MAP DATA
    # --------------------------------------------------

    map_data = top_accounts.dropna(
        subset=[
            "lat",
            "lng",
        ]
    ).copy()

    map_data["lat"] = pd.to_numeric(
        map_data["lat"],
        errors="coerce",
    )

    map_data["lng"] = pd.to_numeric(
        map_data["lng"],
        errors="coerce",
    )

    map_data = map_data.dropna(
        subset=[
            "lat",
            "lng",
        ]
    )

    map_data["churn_pct"] = (
        map_data["churn_probability"]
        * 100
    ).round(1)

    map_data["risk_score_display"] = (
        map_data["risk_score"]
        .round(0)
        .astype(int)
    )


    # --------------------------------------------------
    # MARKER SIZE
    # --------------------------------------------------

    score_min = (
        map_data["risk_score"].min()
    )

    score_max = (
        map_data["risk_score"].max()
    )

    if score_max == score_min:

        map_data["radius"] = 18

    else:

        map_data["radius"] = (
            12
            + (
                (
                    map_data["risk_score"]
                    - score_min
                )
                / (
                    score_max
                    - score_min
                )
            )
            * 18
        )


    # --------------------------------------------------
    # MAP VIEW
    # --------------------------------------------------

    map_latitude = -14.235
    map_longitude = -51.925
    map_zoom = 3.1

    if (
        st.session_state.map_account
        is not None
    ):

        selected_map_row = map_data[
            map_data["account_id"]
            == st.session_state.map_account
        ]

        if not selected_map_row.empty:

            selected_map_row = (
                selected_map_row.iloc[0]
            )

            map_latitude = float(
                selected_map_row["lat"]
            )

            map_longitude = float(
                selected_map_row["lng"]
            )

            map_zoom = 11


    # --------------------------------------------------
    # NORMAL ACCOUNT MARKERS
    # --------------------------------------------------

    normal_map_data = (
        map_data.copy()
    )

    if (
        st.session_state.map_account
        is not None
    ):

        normal_map_data = (
            normal_map_data[
                normal_map_data[
                    "account_id"
                ]
                != st.session_state.map_account
            ]
        )

    normal_layer = pdk.Layer(
        "ScatterplotLayer",
        data=normal_map_data,
        get_position="[lng, lat]",
        get_radius="radius",
        radius_units="pixels",
        radius_min_pixels=10,
        radius_max_pixels=32,
        get_fill_color=[
            0,
            122,
            51,
            190,
        ],
        get_line_color=[
            255,
            255,
            255,
        ],
        line_width_min_pixels=1,
        stroked=True,
        pickable=True,
    )


    # --------------------------------------------------
    # SELECTED ACCOUNT MARKER
    # --------------------------------------------------

    layers = [
        normal_layer
    ]

    if (
        st.session_state.map_account
        is not None
    ):

        highlighted_account = map_data[
            map_data["account_id"]
            == st.session_state.map_account
        ]

        if not highlighted_account.empty:

            highlight_layer = pdk.Layer(
                "ScatterplotLayer",
                data=highlighted_account,
                get_position="[lng, lat]",
                get_radius=26,
                radius_units="pixels",
                radius_min_pixels=20,
                radius_max_pixels=36,
                get_fill_color=[
                    220,
                    0,
                    0,
                    230,
                ],
                get_line_color=[
                    255,
                    255,
                    255,
                ],
                line_width_min_pixels=3,
                stroked=True,
                pickable=True,
            )

            layers.append(
                highlight_layer
            )


    # --------------------------------------------------
    # CREATE MAP
    # --------------------------------------------------

    deck = pdk.Deck(
        layers=layers,
        initial_view_state=pdk.ViewState(
            latitude=map_latitude,
            longitude=map_longitude,
            zoom=map_zoom,
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
                "Churn risk: "
                "{churn_pct}%<br/>"
                "Priority score: "
                "{risk_score_display}"
            )
        },
    )

    st.pydeck_chart(
        deck,
        use_container_width=True,
        height=540,
    )

    if (
        st.session_state.map_account
        is None
    ):

        st.caption(
            "Use the Risk Map page for the "
            "full overview of all at-risk accounts."
        )


st.divider()


# --------------------------------------------------
# ACCOUNT ACTION SECTION
# --------------------------------------------------

st.header(
    "Account Action",
    anchor="account-action",
)


# --------------------------------------------------
# AUTOMATIC SCROLL TO ACCOUNT
# --------------------------------------------------

if (
    st.session_state.scroll_request
    != st.session_state.last_scroll_request
):

    scroll_number = (
        st.session_state.scroll_request
    )

    components.html(
        f"""
        <script>
        (function() {{

            const requestId =
                {scroll_number};

            function scrollToAccount() {{

                const doc =
                    window.parent.document;

                const target =
                    doc.getElementById(
                        "account-action"
                    );

                if (target) {{

                    target.scrollIntoView({{
                        behavior: "smooth",
                        block: "start"
                    }});

                    return;
                }}

                setTimeout(
                    scrollToAccount,
                    100
                );
            }}

            setTimeout(
                scrollToAccount,
                250
            );

        }})();
        </script>
        """,
        height=0,
    )

    st.session_state.last_scroll_request = (
        st.session_state.scroll_request
    )


st.write(
    "Review recent account activity and "
    "generate an AI-supported next action."
)


# --------------------------------------------------
# ACCOUNT SELECTOR
# --------------------------------------------------

selected_index = (
    account_options.index(
        st.session_state.selected_account
    )
)

selected_account = st.selectbox(
    "Account",
    account_options,
    index=selected_index,
)

st.session_state.selected_account = (
    selected_account
)


# --------------------------------------------------
# SELECTED ACCOUNT DATA
# --------------------------------------------------

selected_risk = top_accounts[
    top_accounts["account_id"]
    == selected_account
].iloc[0]

account_orders = lines_df[
    lines_df["account_id"]
    == selected_account
].copy()

account_orders = (
    account_orders.sort_values(
        "order_date",
        ascending=False,
    )
)


# --------------------------------------------------
# ACCOUNT INFORMATION
# --------------------------------------------------

latest_order = (
    account_orders.iloc[0]
)

latest_order_id = (
    latest_order["order_id"]
)

latest_order_lines = account_orders[
    account_orders["order_id"]
    == latest_order_id
]

latest_order_date = (
    latest_order["order_date"]
    .strftime("%d %B %Y")
)

latest_order_total = (
    latest_order_lines["price"]
    .sum()
)

freight_total = (
    latest_order_lines["freight_value"]
    .sum()
)

was_late = (
    latest_order_lines["is_late"]
    .any()
)

number_of_orders = (
    account_orders["order_id"]
    .nunique()
)

average_review = (
    account_orders["review_score"]
    .mean()
)

order_review = reviews_df[
    reviews_df["order_id"]
    == latest_order_id
]

comment = (
    "No written feedback provided."
)

if not order_review.empty:

    msg = order_review.iloc[0][
        "review_comment_message"
    ]

    if pd.notna(msg):

        comment = str(msg)


# --------------------------------------------------
# TRANSLATE CUSTOMER COMMENT
# --------------------------------------------------

translated_comment = (
    translate_comment(
        comment
    )
)


# --------------------------------------------------
# ACCOUNT SUMMARY
# --------------------------------------------------

st.subheader(
    f"Account {selected_account}"
)

a, b, c = st.columns(3)

a.metric(
    "Churn risk",
    (
        f"{selected_risk['churn_probability'] * 100:.1f}%"
    ),
)

b.metric(
    "Customer value",
    f"${selected_risk['total_spend']:,.2f}",
)

c.metric(
    "Priority score",
    f"{selected_risk['risk_score']:,.0f}",
)


# --------------------------------------------------
# ACCOUNT DETAILS
# --------------------------------------------------

detail_left, detail_right = (
    st.columns(2)
)


with detail_left:

    st.markdown(
        "### Recent activity"
    )

    st.write(
        f"**Last order:** "
        f"{latest_order_date}"
    )

    st.write(
        f"**Historical orders:** "
        f"{number_of_orders}"
    )

    st.write(
        f"**Latest order value:** "
        f"${latest_order_total:,.2f}"
    )

    st.write(
        f"**Freight:** "
        f"${freight_total:,.2f}"
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

    st.markdown(
        "### Customer experience"
    )

    if pd.notna(
        average_review
    ):

        st.write(
            f"**Average review score:** "
            f"{average_review:.1f} / 5"
        )

    else:

        st.write(
            "**Average review score:** "
            "No review data"
        )

    st.write(
        "**Latest customer comment:**"
    )

    st.write(
        translated_comment
    )


# --------------------------------------------------
# AI RECOMMENDATION
# --------------------------------------------------

st.markdown(
    "### AI Recommendation"
)

st.write(
    "Gemini turns the churn prediction and "
    "account history into a practical next "
    "step for the sales representative."
)

if st.button(
    "Generate AI Recommendation",
    type="primary",
):

    try:

        client = genai.Client(
            api_key=st.secrets[
                "GEMINI_API_KEY"
            ],
            http_options=types.HttpOptions(
                timeout=30_000
            ),
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
Latest written feedback: {translated_comment}

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

            try:

                response = (
                    client.models.generate_content(
                        model="gemini-3.8-flash",
                        contents=prompt,
                        config={
                            "max_output_tokens": 300,
                            "thinking_config": {
                                "thinking_level": "low",
                            },
                        },
                    )
                )

            except Exception:

                response = (
                    client.models.generate_content(
                        model="gemini-3.7-flash",
                        contents=prompt,
                        config={
                            "max_output_tokens": 300,
                            "thinking_config": {
                                "thinking_level": "low",
                            },
                        },
                    )
                )

        st.markdown(
            response.text
        )

    except KeyError:

        st.error(
            "Gemini API key not found."
        )

    except Exception as e:

        st.error(
            "Could not generate the AI "
            f"recommendation: {e}"
        )
