import streamlit as st
import streamlit_authenticator as stauth
from streamlit_gsheets import GSheetsConnection

# from forms.routeform import route_planner
from forms.newrouterform import new_route_planner
from forms.dailyform import daily_reporting_form
from forms.hcpformexisting import hcp_form_existing
from forms.hcpform import hcp_form

from filters.routeplanfilters import filter_modal, get_filtered_data


# --------------------AUTHENTICATION CHECK---------------------------------------------------------------
if not st.session_state.get("authenticated"):
    st.error("Please login to access this page")
    st.stop()

# --------------------GET USER SPECIFIC DATA(Signed in user)---------------------------------------------------------------
username = st.session_state["username"]
user_credentials = st.session_state["user_credentials"]
# user_credentials = st.session_state["credentials"]["usernames"][username]
user_territory = user_credentials["Territory_ID"]


# --------------------REDUCE HEADER HEIGHT---------------------------------------------------------------

reduce_header_height_style = """
    <style>
        div.block-container {padding-top:1rem;}
    </style>
"""
st.markdown(reduce_header_height_style, unsafe_allow_html=True)


# --------------------CUSTOM CSS---------------------------------------------------------------
# Load the CSS at the beginning of the page
def load_custom_css():
    with open("assets/css/style.css", "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_custom_css()

# create a connection to the Google Sheet
conn = st.connection("gsheets", type=GSheetsConnection)

# --------------------LOAD DATA---------------------------------------------------------------


@st.cache_data(ttl=300)
def load_route_data():
    data = conn.read(worksheet="RoutePlan")
    return data


@st.cache_data(ttl=300)
def load_daily_data():
    return conn.read(worksheet="DailyReport")


@st.cache_data(ttl=300)
def load_hcp_clients_data():
    return conn.read(worksheet="ClientsDatabase")


@st.cache_data(ttl=300)
def load_pending_clients_data():
    return conn.read(worksheet="PendingClients")


# --------TABS FOR DIFFERENT FORMS---------------------------------------------------------------

tab = st.tabs(["Route Planner", "Daily Reporting", "HCP / Retailers"])
# tab = st.tabs(["Route Planner", "Daily Reporting"])

# Route Planner Form Tab
with tab[0]:
    # --------------------ROUTE PLANNER TAB----------------------------------------------------------------
    # Define button container
    with st.container(key="route_buttons_container"):
        col1, col2 = st.columns([1.5, 1], gap="small")

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

                with col3:

                    # Refresh Button
                    if st.button(
                        "refresh",
                        help="Click to Refresh Data",
                        type="secondary",
                        icon=":material/refresh:",
                        key="refresh_route_planner",
                    ):
                        st.cache_data.clear()  # Clear the cache
                        st.toast("Cache cleared. Reloading data...", icon="✅")

    # Create empty container for dynamic table
    route_table_container = st.empty()

    # Load data
    Route_data = load_route_data()
    display_data = None

    # Check if data exists and process it
    if Route_data is not None and not Route_data.empty:
        try:
            # Filter by territory for non-admin users
            if user_territory != "admin":
                Route_data = Route_data[Route_data["Territory"] == user_territory]
                if not Route_data.empty:
                    display_data = Route_data.drop(
                        # columns=["Territory", "Agent", "TimeStamp"]
                        columns=["TimeStamp", "Agent"]
                    )
            else:
                display_data = Route_data.drop(columns=["Month"])
        except Exception as e:
            st.error(f"Error processing data: {str(e)}")
            display_data = None

    # Display data or show empty state
    with route_table_container:
        if display_data is None or display_data.empty:
            col1, col2, col3 = st.columns(3, gap="small")
            with col2:
                st.image(
                    "assets/images/alert.png",
                    caption="No data available. Please add a route plan to the spreadsheet.",
                )
        else:
            st.dataframe(display_data, hide_index=True)

# --------------------DAILY REPORTING TAB----------------------------------------------------------------
with tab[1]:
    data = {
        "Appointment / Follow-Up": "Scheduled future visits or calls with a contact to discuss the product or check on stock levels. OR required to for a follow-up.",
        "Closed": "The institution/store/shop wasn't open or permanently closed down.",
        "Codes inactive": "Products were inactive or out of stock, No further action or stocking.",
        "Commitment": "A commitment made by a contact (e.g., nurse, pharmacist) to order, recommend, or prescribe Alpha.",
        "Complaint": "Feedback provided that raises issues or concerns about the product, stock, or service.",
        "Confirm to Order": "Confirmation from the contact that they will place an order for the product.",
        "Contact HQ": "Action item to reach out to headquarters for additional support or information.",
        "Delivered": "The product was delivered to the facility and confirmed as received.",
        "Introduction-Product Discussion": "Conversation introducing the product or discussing its benefits or use cases.",
        "No Discussions": "No meaningful discussion or engagement took place during the visit./couldn't reach the contact person.",
        "Not Stocking": "The facility or pharmacy is not currently or in the near future planning to stock the product.",
        "Ordered": "The facility placed an order for the product.",
        "Other Supplier": "The contact is sourcing products from another supplier (e.g., Citylink, Veteran).",
        "Promise": "The verbal promise from the contact to place an order or recommend or prescribe the product in the future.",
        "Sample": "A request for or delivery of product samples to the contact or facility.",
        "Stocked": "The facility already has the product in stock.",
        "Unavailable": "The contact/decision-maker of the facility was not available during the visit.",
    }

    with st.container(key="daily_buttons_container"):
        col1, col2 = st.columns([2, 1], gap="small")

        with col1:
            # Expander for Action
            with st.expander("Action", expanded=False, icon=":material/ads_click:"):
                col1, col2, col3, col4 = st.columns(4, gap="small")
                with col1:

                    @st.dialog("Daily Activity Form")
                    def show_daily_form():
                        daily_reporting_form()

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
                        "refresh",
                        help="Click to Refresh Data",
                        type="secondary",
                        icon=":material/refresh:",
                        key="refresh_daily_form",
                    ):
                        st.cache_data.clear()  # Clear the cache
                        st.toast("Cache cleared. Reloading data...", icon="✅")

                with col4:

                    @st.dialog("Outcome Explanations")
                    def show_outcomes():
                        st.write(
                            "Explore the various outcomes and their explanations below:"
                        )

                        for outcome, explanation in data.items():
                            st.markdown(f"- **{outcome}**: {explanation}")

                    if st.button(
                        "outcomes",
                        icon=":material/info:",
                        key="outcomes_button",
                        help="Click to view outcomes",
                    ):
                        show_outcomes()

    # Create empty container for dynamic table
    daily_table_container = st.empty()

    # Load and filter data
    Daily_data = load_daily_data()
    display_daily_data = None

    if not Daily_data.empty:
        # Only filter by territory if user is not admin
        if user_territory != "admin":
            Daily_data = Daily_data[Daily_data["Territory"] == user_territory]
            # For regular users, drop specified columns
            display_daily_data = Daily_data.drop(
                columns=[
                    "TimeStamp",
                    "Agent_Name",
                    "Territory",
                ]
            )
        else:
            # For admin, show all data
            display_daily_data = Daily_data.copy()

    # Check if either initial data was empty or filtered data is empty
    if Daily_data.empty or display_daily_data.empty:
        with daily_table_container:
            col1, col2, col3 = st.columns(3, gap="small")
            with col2:
                st.image(
                    "assets/images/alert.png",
                    caption="No data available. Please add to view.",
                )
    else:
        # Display filtered data in the empty container
        with daily_table_container:
            st.dataframe(display_daily_data, hide_index=True)


# --------------------HCP / RETAILERS TAB----------------------------------------------------------------
with tab[2]:
    # Expander for Action
    with st.expander("Action", expanded=False, icon=":material/ads_click:"):
        with st.container():
            col1, col2, col3 = st.columns(3, gap="small")
            with col1:

                @st.dialog("New HCP/Client/Retailer Form")
                def show_hcp_form():
                    hcp_form()

                if st.button(
                    "Add New Client to New Workplace",
                    help="Click to add new HCP/Client/Retailer",
                    type="primary",
                    icon=":material/library_add:",
                    key="add_hcp_form_button",
                ):
                    show_hcp_form()

            with col2:

                @st.dialog("HCP Form Existing")
                def show_hcp_form_existing():
                    hcp_form_existing()

                if st.button(
                    "Add Client to Existing Workplace",
                    help="Click to add existing HCP",
                    type="secondary",
                    icon=":material/library_add:",
                    key="add_hcp_form_existing_button",
                ):
                    show_hcp_form_existing()

            # with col3:

            #     st.button(
            #         "Filters",
            #         help="Click to add filters",
            #         type="secondary",
            #         icon=":material/tune:",
            #         key="filter_hcp_form_button",
            #     )
            with col3:
                # Refresh Button
                if st.button(
                    "refresh",
                    help="Click to Refresh Data",
                    type="secondary",
                    icon=":material/refresh:",
                    key="refresh_hcp_form",
                ):
                    st.cache_data.clear()  # Clear the cache
                    st.toast("Cache cleared. Reloading data...", icon="✅")

        # ----------PENDING DATA ------------------------------------------------------------
        pending_clients_data = load_pending_clients_data()
        display_pending_data = None

        # Check if data exists and process it
        if pending_clients_data is not None and not pending_clients_data.empty:
            try:
                # Filter by territory for non-admin users
                if user_territory != "admin":
                    pending_clients_data = pending_clients_data[
                        pending_clients_data["Territory"] == user_territory
                    ]
                    if not pending_clients_data.empty:
                        display_pending_data = pending_clients_data.drop(
                            columns=["Territory", "Workplace_Type", "State"]
                        )  # Drop Territory column for non-admin users
                else:
                    display_pending_data = pending_clients_data.copy()
            except Exception as e:
                st.error(f"Error processing data: {str(e)}")
                display_pending_data = None

        # Display data or show empty state
        if display_pending_data is None or display_pending_data.empty:
            col1, col2, col3 = st.columns(3, gap="small")
            with col2:
                st.image(
                    "assets/images/alert.png",
                    caption="No data available. Please add to view.",
                )
        else:
            st.dataframe(display_pending_data, hide_index=True)

    # Create empty container for dynamic table
    hcp_table_container = st.empty()

    # Load data
    HCP_Clients_data = load_hcp_clients_data()
    display_hcp_data = None

    # Check if data exists and process it
    if HCP_Clients_data is not None and not HCP_Clients_data.empty:
        try:
            # Filter by territory for non-admin users
            if user_territory != "admin":
                HCP_Clients_data = HCP_Clients_data[
                    HCP_Clients_data["Territory"] == user_territory
                ]
                if not HCP_Clients_data.empty:
                    display_hcp_data = HCP_Clients_data.drop(
                        columns=["Territory", "Workplace_Type", "State"]
                    )  # Drop Territory column for non-admin users
            else:
                display_hcp_data = HCP_Clients_data.copy()
        except Exception as e:
            st.error(f"Error processing data: {str(e)}")
            display_hcp_data = None

    # Display data or show empty state
    with hcp_table_container:
        if display_hcp_data is None or display_hcp_data.empty:
            col1, col2, col3 = st.columns(3, gap="small")
            with col2:
                st.image(
                    "assets/images/alert.png",
                    caption="No data available. Please add to view.",
                )
        else:
            st.dataframe(display_hcp_data, hide_index=True)
