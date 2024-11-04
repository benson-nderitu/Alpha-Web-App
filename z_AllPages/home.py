import os
import streamlit as st
from streamlit_gsheets import GSheetsConnection

# from forms.routeform import route_planner
from forms.newrouterform import new_route_planner
from forms.dailyform import daily_form
from forms.hcpform import hcp_form
from filters.dailyfilters import filter_modal


# Style to reduce header height
reduce_header_height_style = """
    <style>
        div.block-container {padding-top:1rem;}
    </style>
"""
st.markdown(reduce_header_height_style, unsafe_allow_html=True)


# Load custom CSS
def load_custom_css():
    with open("assets/css/style.css", "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


# create a connection to the Google Sheet
conn = st.connection("gsheets", type=GSheetsConnection)


@st.cache_data(ttl=300)
def load_route_data():
    return conn.read(worksheet="RoutePlanner")


@st.cache_data(ttl=300)
def load_daily_data():
    return conn.read(worksheet="DailyData")


@st.cache_data(ttl=300)
def load_hcp_data():
    return conn.read(worksheet="HCPData")


# Load the CSS at the beginning of the page
load_custom_css()


# --------TABS FOR DIFFERENT FORMS--------------------------
tab = st.tabs(["Route Planner", "Daily Reporting", "HCP"])

# Route Planner Form Tab
with tab[0]:

    data = {
        "Appointment / Follow-Up": "Scheduled future visits or calls with a contact to discuss the product or check on stock levels. OR required to for a follow-up.",
        "Closed": "The institution/store/shop wasn’t open or permanently closed down.",
        "Codes inactive": "Products were inactive or out of stock, No further action or stocking.",
        "Commitment": "A commitment made by a contact (e.g., nurse, pharmacist) to order, recommend, or prescribe Alpha.",
        "Complaint": "Feedback provided that raises issues or concerns about the product, stock, or service.",
        "Confirm to Order": "Confirmation from the contact that they will place an order for the product.",
        "Contact HQ": "Action item to reach out to headquarters for additional support or information.",
        "Delivered": "The product was delivered to the facility and confirmed as received.",
        "Introduction-Product Discussion": "Conversation introducing the product or discussing its benefits or use cases.",
        "No Discussions": "No meaningful discussion or engagement took place during the visit./couldn’t reach the contact person.",
        "Not Stocking": "The facility or pharmacy is not currently or in the near future planning to stock the product.",
        "Ordered": "The facility placed an order for the product.",
        "Other Supplier": "The contact is sourcing products from another supplier (e.g., Citylink, Veteran).",
        "Promise": "The verbal promise from the contact to place an order or recommend or prescribe the product in the future.",
        "Sample": "A request for or delivery of product samples to the contact or facility.",
        "Stocked": "The facility already has the product in stock.",
        "Unavailable": "The contact/decision-maker of the facility was not available during the visit.",
    }
    # Expander for Action
    with st.expander("Outcomes Explanations", expanded=False, icon=":material/info:"):
        # Streamlit app layout
        st.title("Outcome Explanations")
        st.write("Explore the various outcomes and their explanations below:")

        for outcome, explanation in data.items():
            st.markdown(f"- **{outcome}**: {explanation}")
    # Define button container
    with st.container(key="route_buttons_container"):
        col1, col2 = st.columns(2, gap="small")

        with col1:
            # Expander for Action
            with st.expander(
                "Action", expanded=False, icon=":material/ads_click:"
            ):  # Set expanded=True if you want it open by default
                col1, col2, col3 = st.columns(3, gap="small")
                with col1:

                    @st.dialog("Route Planner Form")
                    def show_route_form():
                        new_route_planner()

                    if st.button(
                        "Add",
                        help="Click to add route plan",
                        type="primary",
                        icon=":material/library_add:",
                        key="add_route_plan_button",
                    ):
                        show_route_form()

                with col2:

                    @st.dialog("Route Plan Filters")
                    def show_route_form_filters():
                        filter_modal()

                    if st.button(
                        "Filters",
                        help="Click to filter the data",
                        type="secondary",
                        icon=":material/tune:",
                        key="route_filter_button",
                    ):
                        show_route_form_filters()
                    # st.button(
                    #     "Filters",
                    #     help="Click to filter the data",
                    #     type="secondary",
                    #     icon=":material/tune:",
                    #     key="route_filter_button",
                    # )

                with col3:

                    # Refresh Button
                    if st.button(
                        "",
                        help="Click to Refresh Data",
                        type="secondary",
                        icon=":material/refresh:",
                        key="refresh_route_planner",
                    ):
                        st.cache_data.clear()  # Clear the cache
                        st.toast("Cache cleared. Reloading data...", icon="✅")

    # Google Sheets connection and data display
    Route_data = load_route_data()
    if Route_data.empty:
        col1, col2, col3 = st.columns(3, gap="small")
        with col2:
            st.image(
                "assets/images/alert.png",
                caption="No data available. Please add a route plan to the spreadsheet.",
            )
    else:
        st.dataframe(Route_data, hide_index=True)

# Daily Reporting Form Tab
with tab[1]:

    with st.container(key="daily_buttons_container"):
        col1, col2 = st.columns(2, gap="small")

        with col1:
            # Expander for Action
            with st.expander("Action", expanded=False, icon=":material/ads_click:"):
                col1, col2, col3 = st.columns(3, gap="small")
                with col1:

                    @st.dialog("Daily Activity Form")
                    def show_daily_form():
                        daily_form()

                    if st.button(
                        "Add ",
                        help="Click to add activity",
                        type="primary",
                        icon=":material/library_add:",
                        key="add_daily_form_button",
                    ):

                        show_daily_form()

                with col2:

                    st.button(
                        "Filters",
                        help="Click to filter data",
                        type="secondary",
                        icon=":material/tune:",
                        key="filter_daily_form_button",
                    )
                with col3:
                    # Refresh Button
                    if st.button(
                        "",
                        help="Click to Refresh Data",
                        type="secondary",
                        icon=":material/refresh:",
                        key="more_daily_form",
                    ):
                        st.cache_data.clear()  # Clear the cache
                        st.toast("Cache cleared. Reloading data...", icon="✅")

    # Google Sheets connection and data display
    # Use the function to get the data
    Daily_data = load_daily_data()
    if Daily_data.empty:
        col1, col2, col3 = st.columns(3, gap="small")
        with col2:
            st.image(
                "assets/images/alert.png",
                caption="No data available. Please add to view.",
            )
    else:
        st.dataframe(Daily_data, hide_index=True)

# HCP Form Tab
with tab[2]:
    # st.markdown("### HCP Form")
    # st.write("Please fill out the HCP Form below:")

    # establishing a Google Sheets connection
    with st.container(key="hcp_buttons_container"):
        col1, col2 = st.columns(2, gap="small")

        with col1:
            # Expander for Action
            with st.expander("Action", expanded=False, icon=":material/ads_click:"):
                col1, col2, col3 = st.columns(3, gap="small")
                with col1:

                    @st.dialog("HCP Form")
                    def show_hcp_form():
                        hcp_form()

                    if st.button(
                        "Add",
                        help="Click to add HCP",
                        type="primary",
                        icon=":material/library_add:",
                        key="add_hcp_form_button",
                    ):
                        show_hcp_form()

                with col2:

                    st.button(
                        "Filters",
                        help="Click to add filters",
                        type="secondary",
                        icon=":material/tune:",
                        key="filter_hcp_form_button",
                    )
                with col3:
                    # Refresh Button
                    if st.button(
                        "",
                        help="Click to Refresh Data",
                        type="secondary",
                        icon=":material/refresh:",
                        key="more_hcp_form",
                    ):
                        st.cache_data.clear()  # Clear the cache
                        st.toast("Cache cleared. Reloading data...", icon="✅")

    # Google Sheets connection and data display
    HCP_data = load_hcp_data()
    if HCP_data.empty:
        col1, col2, col3 = st.columns(3, gap="small")
        with col2:
            st.image(
                "assets/images/alert.png",
                caption="No data available. Please add to view.",
            )
    else:
        st.dataframe(HCP_data, hide_index=True)
