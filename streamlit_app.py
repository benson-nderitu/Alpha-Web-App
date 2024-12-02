import time
import pandas as pd
import math
from datetime import datetime
import streamlit as st
import streamlit_shadcn_ui as ui
import streamlit_antd_components as sac
import streamlit_authenticator as stauth
from streamlit_gsheets import GSheetsConnection

# --------------------SETUP THE STREAMLIT PAGE CONFIGURATION---------------------------------------------------------------
st.set_page_config(
    page_title="AlphaPlus",
    page_icon=":material/home:",
    initial_sidebar_state="collapsed",
    layout="wide",
)
# --------------------REDUCE HEADER HEIGHT---------------------------------------------------------------
reduce_header_height_style = """
    <style>
        div.block-container {padding-top:1rem;}
    </style>
"""
st.markdown(reduce_header_height_style, unsafe_allow_html=True)

# --------------------CUSTOM CSS TO REMOVE PADDING---------------------------------------------------------------
st.markdown(
    """
            <style>
            .st-emotion-cache-1jicfl2 {
    width: 100%;
    padding: 6rem 1rem 10rem;
    min-width: auto;
    max-width: initial;
}
            """,
    unsafe_allow_html=True,
)

# --------------------LOAD USER DATA FROM GOOGLE SHEETS---------------------------------------------------------------
from data import credentials

# --------------------SETUP THE STREAMLIT AUTHENTICATOR---------------------------------------------------------------
Authenticator = stauth.Authenticate(
    credentials,
    cookie_name="alphaplus",
    key="AUTH_SECRET_KEY",
    cookie_expiry_days=30,
)

# --------------------LOGIN FORM---------------------------------------------------------------
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    try:
        with st.spinner("    Fetching ..."):
            name_or_status = Authenticator.login(
                fields={
                    "Form name": "Login to Alpa + ",
                    "Login": "Get Access",
                },
                location="main",
            )
            if st.session_state.get("authentication_status"):
                time.sleep(2)  # Short delay for smooth transition
    except Exception as e:
        st.error(e)

# --------------------AUTHENTICATION CHECK---------------------------------------------------------------
if st.session_state["authentication_status"]:
    st.session_state["credentials"] = credentials
    st.session_state["authenticated"] = True
    st.session_state["username"] = st.session_state["username"]
    st.session_state["name"] = st.session_state["name"]
    st.session_state["user_credentials"] = credentials["usernames"][
        st.session_state["username"]
    ]

    # --- SHARED ON ALL AllPages ---------------------------------------------------------------------------------
    st.logo("static/logo.png", size="large")
    # ---- Display content after login ---------------------------------------------------------------
    primary_color = st.get_option("theme.primaryColor")
    username = st.session_state["username"]
    user_credentials = credentials["usernames"][username]
    user_role = user_credentials["role"]

    with st.container(key="my_header_container"):
        sac.alert(
            label="**Welcome**",
            description=f"""  <span style='color: {primary_color};'><strong>{user_credentials['fullname']}</strong></span>&nbsp;&nbsp;&nbsp;
                    (Territory: <span style='color:#000;'><strong>{user_credentials['Territory_ID']}</strong></span>)
            """,
            color="pink",
            icon="emoji-smile",
        )
    from forms.newrouterform import new_route_planner
    from forms.dailyform import daily_reporting_form
    from forms.institutionform import institution_scorecard_report
    from forms.hcpformexistingworkplace import hcp_form_existing_workplace
    from forms.hcpformexistingaddress import hcp_form_existing_address
    from forms.hcpformnewclient import hcp_form_new_client

    # --------------------GET USER SPECIFIC DATA(Signed in user)---------------------------------------------------------------
    username = st.session_state["username"]
    user_credentials = st.session_state["user_credentials"]
    user_territory = user_credentials["Territory_ID"]

    # --------------------CUSTOM CSS---------------------------------------------------------------
    def load_custom_css():
        with open("assets/css/style.css", "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    load_custom_css()
    # -----------LOAD DATA---------------------------------------------------------------
    from data import (
        load_route_data,
        load_daily_data,
        load_hcp_clients_data,
        load_institution_data,
        load_pending_clients_data,
    )
    from dashboard import admin_dashboard, user_dashboard

    # admin_dashboard()

    # --------TABS FOR DIFFERENT FORMS---------------------------------------------------------------
    with st.container(key="my_body_container"):
        tab = st.tabs(
            ["Route Planner", "Daily Reporting", "HCP / Retailers", "Dashboard"]
        )
        # Route Planner Form Tab
        with tab[0]:
            # --------------------ROUTE PLANNER TAB----------------------------------------------------------------
            # Define button container
            with st.container(key="route_buttons_container"):
                # Expander for Action
                with st.expander("Action", expanded=True, icon=":material/ads_click:"):
                    col1, col2, col3, col4 = st.columns(
                        [1, 2.5, 0.5, 1], vertical_alignment="bottom"
                    )
                    # Add Route Planner Button
                    with col1:

                        @st.dialog("Route Planner Form")
                        def show_route_form():
                            new_route_planner()

                        if st.button(
                            "Add Route",
                            help="Click to add route plan",
                            type="primary",
                            icon=":material/map:",
                            key="add_route_plan_button",
                            use_container_width=True,
                        ):
                            show_route_form()
                    # Refresh Button
                    with col3:
                        if st.button(
                            "",
                            help="Reload the data and clear cache.",
                            type="secondary",
                            icon=":material/refresh:",
                            key="refresh_route_planner",
                            use_container_width=True,
                        ):
                            st.cache_data.clear()  # Clear cached data
                            Route_data = load_route_data()  # Reload data
                            st.toast("Data refreshed successfully.", icon="✅")
                    with col4:
                        route_filters_section = st.empty()

            # Create empty container for dynamic table
            route_table_container = st.empty()
            Route_data = load_route_data()
            display_data = None
            route_filters = [
                "Today",
                "Current Week",
                "Last Week",
                "Current Month",
                "Next Month",
                "Last Month",
                "Last 2 Months",
                "Last 6 Months",
                "Current Year",
            ]
            # Add "Select All" at the beginning
            route_filters.insert(0, "Select All")
            filter_selection = route_filters_section.selectbox(
                "Filter by",
                options=route_filters,
                index=1,
                key="route_filter_select",
            )
            if "Select All" in filter_selection:
                filter_selection = route_filters[1:]  # Exclude "Select All" itself

            # Function to apply filters dynamically
            def apply_filters(data, selected_filter):
                # Ensure the TimeStamp column is in datetime format
                if "TimeStamp" in data.columns:
                    data["TimeStamp"] = pd.to_datetime(
                        data["TimeStamp"], errors="coerce", format="%d-%m-%Y %H:%M:%S"
                    )
                    now = pd.Timestamp.now()
                    current_week = now.isocalendar().week
                    current_year = now.year
                    if selected_filter == "Today":
                        today = (
                            pd.Timestamp.now().normalize()
                        )  # Normalize to remove time
                        filtered_data = data[data["TimeStamp"].dt.date == today.date()]
                    elif selected_filter == "Current Week":
                        filtered_data = data[
                            data["TimeStamp"].dt.isocalendar().week
                            == now.isocalendar().week
                        ]
                    elif selected_filter == "Current Month":
                        filtered_data = data[data["TimeStamp"].dt.month == now.month]
                    elif selected_filter == "Last Week":
                        last_week = (
                            current_week - 1
                        ) % 53 or 53  # Handle wraparound for weeks
                        filtered_data = data[
                            (data["TimeStamp"].dt.isocalendar().week == last_week)
                            & (data["TimeStamp"].dt.year == current_year)
                        ]
                    elif selected_filter == "Next Month":
                        next_month = (now.month % 12) + 1
                        filtered_data = data[data["TimeStamp"].dt.month == next_month]
                    elif selected_filter == "Last Month":
                        last_month = now.month - 1 or 12
                        filtered_data = data[data["TimeStamp"].dt.month == last_month]
                    elif selected_filter == "Last 2 Months":
                        last_two_months = [
                            (now.month - i - 1) % 12 + 1 for i in range(2)
                        ]
                        filtered_data = data[
                            data["TimeStamp"].dt.month.isin(last_two_months)
                        ]
                    elif selected_filter == "Last 6 Months":
                        last_six_months = [
                            (now.month - i - 1) % 12 + 1 for i in range(6)
                        ]
                        filtered_data = data[
                            data["TimeStamp"].dt.month.isin(last_six_months)
                        ]
                    elif selected_filter == "Current Year":
                        filtered_data = data[data["TimeStamp"].dt.year == now.year]

                    else:
                        filtered_data = data  # No filtering if selection is invalid
                else:
                    st.error("The 'TimeStamp' column is missing or invalid.")
                    filtered_data = data  # Default to no filtering
                return filtered_data

            # Check if data exists and process it
            if Route_data is not None and not Route_data.empty:
                try:
                    # Filter by territory for non-admin users first
                    if user_territory != "admin":
                        if "Territory" in Route_data.columns:
                            Route_data = Route_data[
                                Route_data["Territory"] == user_territory
                            ]
                        else:
                            st.error("The 'Territory' column is missing in Route data.")
                    # Now apply the selected filter
                    display_data = apply_filters(Route_data, filter_selection)
                    # Drop unnecessary columns based on user type
                    if user_territory != "admin":
                        display_data = display_data.drop(
                            columns=["TimeStamp", "Agent", "Territory"]
                        )
                    else:
                        display_data = display_data.drop(columns=["Month"])

                except Exception as e:
                    st.error(f"Error processing data: {str(e)}")
                    st.exception(e)
                    display_data = None

            # Display data or show empty state
            with route_table_container:
                if display_data is None or display_data.empty:
                    _, col, _ = st.columns([1, 3, 1], gap="small")
                    with col:
                        sac.result(
                            label="Oops! No data available for the selected filter. Please try a different filter.",
                            status="empty",
                            key="router_table_empty_state",
                        )
                else:
                    st.dataframe(
                        display_data,
                        use_container_width=True,
                        height=600,
                        hide_index=True,
                    )

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
                # Expander for Action
                with st.expander("Action", expanded=True, icon=":material/ads_click:"):
                    col1, col2, col3, col4, col5, dailyFilterCol = st.columns(
                        [1.5, 1.5, 2, 0.5, 0.5, 1.5], vertical_alignment="bottom"
                    )
                    with col1:

                        @st.dialog("Daily Activity Form")
                        def show_daily_form():
                            daily_reporting_form()

                        if st.button(
                            "Client Report",
                            help="Click to add activity",
                            type="primary",
                            icon=":material/group_add:",
                            key="add_daily_client_report_form_button",
                            use_container_width=True,
                        ):

                            show_daily_form()

                    with col2:

                        @st.dialog("Institution's Scorecard Report")
                        def show_institution_scorecard_report():
                            institution_scorecard_report()

                        if st.button(
                            "Institution Report",
                            help="Click to add activity",
                            type="primary",
                            icon=":material/add_home_work:",
                            key="add_daily_institution_Report_form_button",
                            use_container_width=True,
                        ):
                            show_institution_scorecard_report()
                    with col4:
                        # Refresh Button
                        if st.button(
                            "",
                            help="Click to Refresh Data",
                            type="secondary",
                            icon=":material/refresh:",
                            key="refresh_daily_form",
                            use_container_width=True,
                        ):
                            st.cache_data.clear()  # Clear the cache
                            st.toast("Cache cleared. Reloading data...", icon="✅")
                    with col5:

                        @st.dialog("Outcome Explanations")
                        def show_outcomes():
                            st.write(
                                "Explore the various outcomes and their explanations below:"
                            )
                            for outcome, explanation in data.items():
                                st.markdown(f"- **{outcome}**: {explanation}")

                        if st.button(
                            "",
                            icon=":material/info:",
                            key="outcomes_button",
                            help="Click to view outcomes",
                            use_container_width=True,
                        ):
                            show_outcomes()
                    with dailyFilterCol:
                        filter_section = st.empty()

            with st.expander(
                "CLIENTS DAILY REPORTING", icon=":material/ballot:", expanded=True
            ):
                # Create empty container for dynamic table
                daily_table_container = st.empty()
                Daily_data = load_daily_data()
                display_daily_data = None
                # Convert Timestamp column to datetime with mixed format and then to ISO format
                Daily_data["TimeStamp"] = pd.to_datetime(
                    Daily_data["TimeStamp"],
                    errors="coerce",
                    dayfirst=True,
                    format="%d-%m-%Y %H:%M:%S",
                ).dt.strftime(
                    "%Y-%m-%dT%H:%M:%S"
                )  # Convert to ISO format
                # Select box for filters
                filter_selection = filter_section.selectbox(
                    "Filter by",
                    label_visibility="collapsed",
                    options=route_filters,
                    index=1,
                    key="daily_filter_selection",
                )
                # Check if data exists and process it
                if Daily_data is not None and not Daily_data.empty:
                    try:
                        # Filter by territory for non-admin users first
                        if user_territory != "admin":
                            if "Territory" in Daily_data.columns:
                                Daily_data = Daily_data[
                                    Daily_data["Territory"] == user_territory
                                ]
                            else:
                                st.error(
                                    "The 'Territory' column is missing in Daily data."
                                )
                        # Now apply the selected filter
                        display_daily_data = apply_filters(Daily_data, filter_selection)
                        # Drop unnecessary columns based on user type
                        if user_territory != "admin":
                            display_daily_data = display_daily_data.drop(
                                columns=["TimeStamp", "Agent_Name", "Territory"]
                            )
                        else:
                            display_daily_data = display_daily_data.drop(
                                columns=["Month"]
                            )
                    except Exception as e:
                        st.error(f"Error processing data: {str(e)}")
                        st.exception(e)
                        display_daily_data = None
                # Display data or show empty state
                with daily_table_container:
                    if display_daily_data is None or display_daily_data.empty:
                        _, col, _ = st.columns([1, 3, 1], gap="small")
                        with col:
                            sac.result(
                                label="Oops! No data available for the selected filter. Please try a different filter.",
                                status="empty",
                                key="daily_table_empty_state",
                            )
                    else:
                        st.dataframe(display_daily_data, height=600, hide_index=True)

                # -----------------INSTITUTION DATA---------------------------------------------------
            with st.expander(
                "INSTITUTION SCORECARD", icon=":material/add_home_work:", expanded=True
            ):
                filter_institu_selection = st.empty()
                # Create empty container for dynamic table
                institution_scorecard_table_container = st.empty()
                Institution_data = load_institution_data()
                display_Institution_data = None
                # Select box for filters
                filter_selection = filter_institu_selection.selectbox(
                    "Filter by",
                    options=route_filters,
                    index=1,
                    key="filter_institution_selection",
                )
                # Check if data exists and process it
                if Institution_data is not None and not Institution_data.empty:
                    try:
                        # Filter by territory for non-admin users first
                        if user_territory != "admin":
                            if "Territory" in Institution_data.columns:
                                Institution_data = Institution_data[
                                    Institution_data["Territory"] == user_territory
                                ]
                            else:
                                st.error(
                                    "The 'Territory' column is missing in Daily data."
                                )
                        # Now apply the selected filter
                        display_Institution_data = apply_filters(
                            Institution_data, filter_selection
                        )
                        # Drop unnecessary columns based on user type
                        if user_territory != "admin":
                            display_Institution_data = display_Institution_data.drop(
                                columns=["TimeStamp", "Agent_Name", "Territory"]
                            )
                        else:
                            display_Institution_data = display_Institution_data.drop(
                                columns=["Month"]
                            )
                    except Exception as e:
                        st.error(f"Error processing data: {str(e)}")
                        st.exception(e)
                        display_Institution_data = None
                # Display data or show empty state
                with institution_scorecard_table_container:
                    if (
                        display_Institution_data is None
                        or display_Institution_data.empty
                    ):
                        _, col, _ = st.columns([1, 3, 1], gap="small")
                        with col:
                            sac.result(
                                label="Oops! No data available for the selected filter. Please try a different filter.",
                                status="empty",
                                key="institution_table_empty_state",
                            )
                    else:
                        st.dataframe(
                            display_Institution_data, height=600, hide_index=True
                        )

        # --------------------HCP / RETAILERS TAB----------------------------------------------------------------
        with tab[2]:
            # Expander for Action
            with st.expander("Action", expanded=True, icon=":material/ads_click:"):
                with st.container():
                    col1, col2, col3, col4 = st.columns([1, 1, 1, 0.4], gap="small")
                    with col1:

                        @st.dialog("New HCP/Client/Retailer Form")
                        def show_hcp_form_new_client():
                            hcp_form_new_client()

                        if st.button(
                            # "Add Client (New Workplace & New Address)",
                            "Add Client(Completely New)",
                            help="Click to add new HCP/Client/Retailer",
                            type="primary",
                            icon=":material/person_add:",
                            key="add_hcp_form_button",
                            use_container_width=True,
                        ):
                            show_hcp_form_new_client()

                    with col2:

                        @st.dialog("Add Client to Existing Workplace")
                        def show_hcp_form_existing_workplace():
                            hcp_form_existing_workplace()

                        if st.button(
                            "Add Client (Existing Workplace)",
                            help="Click to new client to an existing workplace",
                            type="primary",
                            icon=":material/add_business:",
                            key="add_hcp_form_existing_button",
                            use_container_width=True,
                        ):
                            show_hcp_form_existing_workplace()
                    with col3:

                        @st.dialog("Add Client to Existing Address")
                        def show_hcp_form_existing_address():
                            hcp_form_existing_address()

                        if st.button(
                            "Add Client (Existing Address)",
                            help="Click to add new Workplace to an existing address",
                            type="primary",
                            icon=":material/add_location:",
                            key="add_hcp_form_existing_address_button",
                            use_container_width=True,
                        ):
                            show_hcp_form_existing_address()
                    with col4:
                        if st.button(
                            "",
                            help="Click to Refresh Data",
                            type="secondary",
                            icon=":material/refresh:",
                            key="refresh_hcp_form",
                            use_container_width=True,
                        ):
                            st.cache_data.clear()
                            st.toast("Cache cleared. Reloading data...", icon="✅")

                # ----------PENDING DATA ------------------------------------------------------------
                # pending_clients_data = load_pending_clients_data()
                # display_pending_data = None
                # # Check if data exists and process it
                # if pending_clients_data is not None and not pending_clients_data.empty:
                #     try:
                #         # Filter by territory for non-admin users
                #         if user_territory != "admin":
                #             pending_clients_data = pending_clients_data[
                #                 pending_clients_data["Territory"] == user_territory
                #             ]
                #             if not pending_clients_data.empty:
                #                 display_pending_data = pending_clients_data.drop(
                #                     columns=["Territory", "Workplace_Type", "State"]
                #                 )  # Drop Territory column for non-admin users
                #         else:
                #             display_pending_data = pending_clients_data.copy()
                #     except Exception as e:
                #         st.error(f"Error processing data: {str(e)}")
                #         display_pending_data = None
                # # Display data or show empty state
                # if display_pending_data is None or display_pending_data.empty:
                #     col1, col2, col3 = st.columns(3, gap="small")
                #     with col2:
                #         sac.result(
                #             label="Oops! No data available. Please add to view.",
                #             status="empty",
                #             key="pending_table_empty_state",
                #         )
                # else:
                #     st.dataframe(display_pending_data, hide_index=True)

            # Create empty container for dynamic table
            hcp_table_container = st.empty()
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
                                columns=[
                                    "Territory",
                                    "Workplace_Type",
                                    "State",
                                    "TimeStamp",
                                ]
                            )  # Drop Territory column for non-admin users
                    else:
                        display_hcp_data = HCP_Clients_data.copy()
                except Exception as e:
                    st.error(f"Error processing data: {str(e)}")
                    display_hcp_data = None
            # Display data or show empty state
            with hcp_table_container:
                if display_hcp_data is None or display_hcp_data.empty:
                    _, col, _ = st.columns([1, 3, 1], gap="small")
                    with col:
                        sac.result(
                            label="Oops! No data available. Please add to view.",
                            status="empty",
                            key="hcp_table_empty_state",
                        )
                else:
                    st.dataframe(display_hcp_data, height=600, hide_index=True)

        # ---- DASHBOARD TAB ---------------------------------------------------------------
        with tab[3]:
            dashboard_container = st.empty()
            if user_role == "Admin":
                with dashboard_container.container():
                    # sac.alert(
                    #     label="",
                    #     description="This is Dashboard is meant to be used to track performance and activities of the team.",
                    #     banner=sac.Banner(
                    #         play=True, direction="right", speed=50, pauseOnHover=True
                    #     ),
                    #     icon=True,
                    #     color="success",
                    #     closable=True,
                    # )

                    admin_dashboard()
            if user_role == "User":
                with dashboard_container.container():
                    with st.expander(
                        "Metrics Summary - (based on clients reports)",
                        icon=":material/bar_chart:",
                        expanded=True,
                    ):
                        st.write(user_territory)
                        # Fetch the user's territory
                        territory = user_territory
                        clientdata = load_daily_data()
                        clientdata["TimeStamp"] = clientdata["TimeStamp"].str.replace(
                            "/", "-"
                        )
                        clientdata["TimeStamp"] = pd.to_datetime(
                            clientdata["TimeStamp"],
                            format="%d-%m-%Y %H:%M:%S",
                            dayfirst=True,
                            errors="coerce",
                        )
                        # Filter the DataFrame based on the user's territory
                        user_data_df = clientdata[
                            clientdata["Territory"].str.strip() == territory
                        ]

                        if user_data_df.empty:
                            st.warning(f"No data available for territory: {territory}")

                        # Calculate metrics for the filtered data
                        current_time = datetime.now()
                        total_reports = len(user_data_df)
                        last_updated = user_data_df["TimeStamp"].max()

                        # Time since the last update
                        if pd.isna(last_updated) or last_updated is pd.NaT:
                            last_updated_str = "N/A"
                            time_since_last_update = "N/A"
                        else:
                            last_updated_str = last_updated.strftime("%d-%m-%Y")
                            time_ago = (current_time - last_updated).total_seconds()
                            days_ago = time_ago // (24 * 3600)
                            hours_ago = (time_ago % (24 * 3600)) // 3600
                            minutes_ago = (time_ago % 3600) // 60
                            seconds_ago = time_ago % 60
                            time_since_last_update = f"{int(days_ago)} Days {int(hours_ago)} hrs {int(minutes_ago)} mins {int(seconds_ago)} secs"

                        # Display metrics in columns
                        cols = st.columns(3)
                        with cols[0]:
                            ui.metric_card(
                                title="Last Updated",
                                content=f"""{last_updated_str}""",
                                description=None,
                                key="user_metric_card1",
                            )
                        with cols[1]:
                            ui.metric_card(
                                title="Time of the last update",
                                content=f"""{time_since_last_update}""",
                                description=None,
                                key="user_metric_card2",
                            )
                        with cols[2]:
                            ui.metric_card(
                                title="Total Reports",
                                content=f"""{total_reports}""",
                                description=None,
                                key="user_metric_card3",
                            )

                    user_dashboard()

        # --------------------------------------------------------s------------------------------------------------------------------

        with st.container(key="divider_logout"):
            st.divider()
        # ---- LOGOUT BUTTON ---------------------------------------------------------------
        _, lgt = st.columns([3, 1])
        with lgt:
            with st.expander("Logout", icon=":material/logout:"):
                if Authenticator.logout("Logout", "main"):
                    with st.spinner("Logging out..."):
                        # Clear all authentication-related session state
                        for key in [
                            "authenticated",
                            "username",
                            "name",
                            "credentials",
                            "user_credentials",
                            "authentication_status",
                        ]:
                            if key in st.session_state:
                                del st.session_state[key]
                        st.write("You have logged out successfully.")

        now = pd.Timestamp.now()
        current_year = now.year
        # Add the copyright line dynamically
        st.markdown(
            f"""
             <div style="margin-left: 20px;">
            &copy; {current_year} Alpha Plus Group. &nbsp;&nbsp;&nbsp; All rights reserved.
            </div>
            """,
            unsafe_allow_html=True,
        )
elif st.session_state["authentication_status"] is False:
    with col2:
        st.error("Username/password is incorrect")
elif st.session_state["authentication_status"] is None:
    with col2:
        st.info("Please enter your username and password")
