import streamlit as st
import pandas as pd
import plotly.express as px
from fuzzywuzzy import fuzz


# Default datasets
default_users = pd.DataFrame({
    "User_ID": ["U001", "U002", "U003", "U004"],
    "First_Name": ["Alice", "Bob", "Charlie", "David"],
    "Company_Name": ["TechSphere Ltd", "Tech Sphere", "GrowGreen Inc", "Green Growers"],
    "Email_Address": ["alice@techsphere.com", "bob@techsphere.com", "charlie@greengrowers.com", "david@greengrowers.com"]
})

default_addresses = pd.DataFrame({
    "User_ID": ["U001", "U001", "U002", "U003", "U004"],
    "Address": ["123 Main St, NY", "456 Elm St, CA", "123 Main St, NY", "789 Green St, TX", "456 Elm St, CA"]
})


# Function to process data
def process_data(users_df, addresses_df):
    users_df.fillna("", inplace=True)  # Replace NaN with empty strings
    addresses_df.fillna("", inplace=True)  # Replace NaN with empty strings
    
    df_merged = users_df.merge(addresses_df, how="left", on=["User_ID"])
    df_merged["Company_Name"] = df_merged["Company_Name"].str.strip()
    df_merged["Standardized_Company_Name"] = df_merged["Company_Name"]
    df_merged["Company_Domain"] = df_merged["Email_Address"].str.split('@').str[1]
    return df_merged

# Function to create details table
def get_details_table(df_merged):
    df_merged.fillna("", inplace=True)  # Replace NaN with empty strings

    grouped = df_merged.groupby("Standardized_Company_Name").agg({
        "Company_Name": lambda x: ", ".join(x.dropna().unique()),
        "Company_Domain": lambda x: ", ".join(x.dropna().unique()),
        "Address": lambda x: "; ".join(x.dropna().unique()), #Multiple addresses are seperated with a ";"
        "Email_Address": lambda x: "; ".join(x.dropna().unique()),
    }).reset_index()

    grouped.rename(columns={
        "Standardized_Company_Name": "Standardized Company",
        "Company_Name": "Company Name",
        "Company_Domain": "Company Domain",
        "Address": "Addresses",
        "Email_Address": "User Emails",
    }, inplace=True)
    return grouped


# Initialize session state
if "df_users" not in st.session_state:
    st.session_state.df_users = default_users
if "df_addresses" not in st.session_state:
    st.session_state.df_addresses = default_addresses
if "df_merged" not in st.session_state:
    st.session_state.df_merged = process_data(default_users, default_addresses)
if "df_details" not in st.session_state:
    st.session_state.df_details = get_details_table(st.session_state.df_merged)


# Match finding logic
def find_smart_matches(df, threshold=60):
    companies = df["Company_Name"].unique()
    matches = []

    for company in companies:
        for other_company in companies:
            if company == other_company:
                continue
            name_score = fuzz.ratio(company, other_company)
            if name_score >= threshold:
                matches.append({"Company": company, "Match": other_company, "Score": name_score})
    
    return pd.DataFrame(matches)

# Streamlit Layout
st.title("Company Analytics Dashboard")
# tabs = st.tabs(["2. Analytics", "4. Details", "3. Configuration", "1. Input - Upload Data Source"])
tabs = st.tabs(["[1] - Input - Data Source", "[2] - Analytics", "[3] - Configuration", "[4] - Details" ])

# Analytics Tab
# with tabs[0]:
#     st.header("2. Analytics Dashboard")
#     user_counts = st.session_state.df_merged.groupby("Standardized_Company_Name").size().reset_index(name="User_Count")
#     fig_users = px.bar(user_counts, x="Standardized_Company_Name", y="User_Count", title="Users by Company Name",
#                        labels={"User_Count": "Users Count", "Standardized_Company_Name": "Company Name"})
#     st.plotly_chart(fig_users)

#     address_counts = st.session_state.df_merged.groupby("Standardized_Company_Name").size().reset_index(name="Address_Count")
#     fig_addresses = px.bar(address_counts, x="Standardized_Company_Name", y="Address_Count", title="Addresses by Company Name",
#                            labels={"Address_Count": "Addresses Count", "Standardized_Company_Name": "Company Name"})
#     st.plotly_chart(fig_addresses)

# Analytics Tab
with tabs[1]:
    st.header("Analytics Dashboard")

    # Reprocess the analytics data if an update has been flagged
    if st.session_state.get("data_updated", False):
        st.session_state.data_updated = False  # Reset the flag

    # Create user counts chart
    user_counts = st.session_state.df_merged.groupby("Standardized_Company_Name").size().reset_index(name="User_Count")
    fig_users = px.bar(user_counts, x="Standardized_Company_Name", y="User_Count", title="Users by Company Name",
                       labels={"User_Count": "Users Count", "Standardized_Company_Name": "Company Name"})
    st.plotly_chart(fig_users)

    # Create address counts chart
    address_counts = st.session_state.df_merged.groupby("Standardized_Company_Name").size().reset_index(name="Address_Count")
    fig_addresses = px.bar(address_counts, x="Standardized_Company_Name", y="Address_Count", title="Addresses by Company Name",
                           labels={"Address_Count": "Addresses Count", "Standardized_Company_Name": "Company Name"})
    st.plotly_chart(fig_addresses)



# Details Tab
with tabs[3]:
    st.header("Company Details")
    st.dataframe(st.session_state.df_details)

    csv = st.session_state.df_details.to_csv(index=False).encode('utf-8')
    st.download_button("Download CSV", data=csv, file_name="company_details.csv", mime="text/csv")

# Configuration Tab

# Configuration Tab
# Configuration Tab
with tabs[2]:
    st.header("Review Potential Matches")

    # Slider to adjust the match confidence threshold
    threshold = st.slider("Match Confidence Threshold", min_value=0, max_value=100, value=60)

    # Find potential matches
    potential_matches = find_smart_matches(st.session_state.df_merged, threshold)

    # Filter companies with duplicates
    duplicate_companies = potential_matches["Company"].unique()

    # Display the total number of unique companies needing updates
    st.write(f"Total Unique Companies Needing Review: {len(duplicate_companies)}")

    # Display the unique companies and their duplicates
    selected_company = st.selectbox(
        "Select a Company to View Matches:", 
        options=duplicate_companies,
        help="Choose a company to see its potential duplicate matches."
    )

    if selected_company:
        # Filter matches for the selected company
        matches_for_selected = potential_matches[potential_matches["Company"] == selected_company]
        
        st.subheader(f"Matches for {selected_company}:")
        for index, row in matches_for_selected.iterrows():
            st.checkbox(f"Match: {row['Match']} (Score: {row['Score']})", key=f"match_{index}")

    # Input for new standardized name
    st.subheader("Update Standardized Company Name")
    new_name = st.text_input("Enter New Standardized Name:", selected_company)

    # Update button to apply changes
    if st.button("Update Standardized Name"):
        # Get selected matches
        selected_matches = [
            row["Match"] for index, row in matches_for_selected.iterrows()
            if st.session_state.get(f"match_{index}", False)
        ]
        
        if selected_matches:
            # Update the standardized company name in the merged dataframe
            st.session_state.df_merged.loc[
                st.session_state.df_merged["Company_Name"].isin(selected_matches + [selected_company]),
                "Standardized_Company_Name"
            ] = new_name
            
            # Update the details dataframe to reflect changes
            st.session_state.df_details = get_details_table(st.session_state.df_merged)
            
            # Flag that the data has been updated
            st.session_state.data_updated = True  # Set this flag to trigger reactivity in analytics tab
            
            st.success(f"Updated standardized name for {selected_company} and its matches to '{new_name}'!")
        else:
            st.warning("No matches selected for updating.")



# Upload Data Source Tab
# with tabs[0]:
#     st.header("Input - Upload Data Source")
    
#     # Helper message for allowed columns
#     st.info("""
#     **Allowed Columns for Uploads:**
#     - Users Dataset: `User_ID`, `First_Name`, `Company_Name`, `Email_Address`
#     - Addresses Dataset: `User_ID`, `Address`
#     """)
    
#     # File uploaders for datasets
#     uploaded_users = st.file_uploader("Upload Users Dataset (CSV):", type="csv")
#     uploaded_addresses = st.file_uploader("Upload Addresses Dataset (CSV):", type="csv")

#     # Check if files are uploaded
#     if uploaded_users or uploaded_addresses:
#         if uploaded_users:
#             new_users_df = pd.read_csv(uploaded_users)
#             st.subheader("Preview of Uploaded Users Dataset:")
#             st.write(new_users_df.head())
            
#             # Validate column names
#             expected_users_columns = {"User_ID", "First_Name", "Company_Name", "Email_Address"}
#             users_columns_diff = expected_users_columns - set(new_users_df.columns)
            
#             if users_columns_diff:
#                 st.warning(f"Missing columns in Users Dataset: {users_columns_diff}")
#                 new_columns = st.text_area("Enter correct column names (comma-separated):", ", ".join(new_users_df.columns))
#                 if st.button("Update Users Column Names"):
#                     try:
#                         new_users_df.columns = [col.strip() for col in new_columns.split(",")]
#                         st.success("Users dataset column names updated!")
#                         st.write(new_users_df.head())
#                     except Exception as e:
#                         st.error(f"Error updating column names: {e}")
        
#         if uploaded_addresses:
#             new_addresses_df = pd.read_csv(uploaded_addresses)
#             st.subheader("Preview of Uploaded Addresses Dataset:")
#             st.write(new_addresses_df.head())
            
#             # Validate column names
#             expected_addresses_columns = {"User_ID", "Address"}
#             addresses_columns_diff = expected_addresses_columns - set(new_addresses_df.columns)
            
#             if addresses_columns_diff:
#                 st.warning(f"Missing columns in Addresses Dataset: {addresses_columns_diff}")
#                 new_columns = st.text_area("Enter correct column names (comma-separated):", ", ".join(new_addresses_df.columns), key="addresses_columns")
#                 if st.button("Update Addresses Column Names"):
#                     try:
#                         new_addresses_df.columns = [col.strip() for col in new_columns.split(",")]
#                         st.success("Addresses dataset column names updated!")
#                         st.write(new_addresses_df.head())
#                     except Exception as e:
#                         st.error(f"Error updating column names: {e}")

#     # Process and update the datasets
#     if st.button("Process Uploaded Files"):
#         if uploaded_users and uploaded_addresses:
#             try:
#                 # Process and update session state
#                 st.session_state.df_users = new_users_df
#                 st.session_state.df_addresses = new_addresses_df
#                 st.session_state.df_merged = process_data(new_users_df, new_addresses_df)
#                 st.session_state.df_details = get_details_table(st.session_state.df_merged)
#                 st.success("Datasets successfully processed and updated!")
#             except Exception as e:
#                 st.error(f"Error processing files: {e}")
#         else:
#             st.error("Please upload both Users and Addresses datasets.")

#     # Show datasets currently being used
#     if st.button("Show Datasets Being Used"):
#         st.subheader("Users Dataset Being Used:")
#         st.write(st.session_state.df_users.head())  # Show current or default dataset
        
#         st.subheader("Addresses Dataset Being Used:")
#         st.write(st.session_state.df_addresses.head())  # Show current or default dataset

#     # Show default datasets if no files are uploaded
#     if not uploaded_users and not uploaded_addresses:
#         st.subheader("Default Users Dataset:")
#         st.write(default_users.head())
        
#         st.subheader("Default Addresses Dataset:")
#         st.write(default_addresses.head())


# Upload Data Source Tab
with tabs[0]:
    st.header("Input - Data Source")

    # Show datasets currently being used (always at the top)
    st.subheader("Datasets Currently Being Used")
    st.write("Below are the datasets currently being used in the application. If you want to update them, scroll down to the upload section.")

    st.subheader("Users Dataset Being Used:")
    st.write(st.session_state.df_users.head())  # Show current or default dataset

    st.subheader("Addresses Dataset Being Used:")
    st.write(st.session_state.df_addresses.head())  # Show current or default dataset

    # Section to upload new datasets
    st.markdown("---")  # Add a separator for better visual distinction
    st.subheader("Upload New Datasets (Optional)")
    
    # Helper message for allowed columns
    st.info("""
    **Allowed Columns for Uploads:**
    - Users Dataset: `User_ID`, `First_Name`, `Company_Name`, `Email_Address`
    - Addresses Dataset: `User_ID`, `Address`
    """)

    # File uploaders for datasets
    uploaded_users = st.file_uploader("Upload Users Dataset (CSV):", type="csv")
    uploaded_addresses = st.file_uploader("Upload Addresses Dataset (CSV):", type="csv")

    # Check if files are uploaded
    if uploaded_users or uploaded_addresses:
        if uploaded_users:
            new_users_df = pd.read_csv(uploaded_users)
            st.subheader("Preview of Uploaded Users Dataset:")
            st.write(new_users_df.head())

            # Validate column names
            expected_users_columns = {"User_ID", "First_Name", "Company_Name", "Email_Address"}
            users_columns_diff = expected_users_columns - set(new_users_df.columns)

            if users_columns_diff:
                st.warning(f"Missing columns in Users Dataset: {users_columns_diff}")
                new_columns = st.text_area("Enter correct column names (comma-separated):", ", ".join(new_users_df.columns))
                if st.button("Update Users Column Names"):
                    try:
                        new_users_df.columns = [col.strip() for col in new_columns.split(",")]
                        st.success("Users dataset column names updated!")
                        st.write(new_users_df.head())
                    except Exception as e:
                        st.error(f"Error updating column names: {e}")

        if uploaded_addresses:
            new_addresses_df = pd.read_csv(uploaded_addresses)
            st.subheader("Preview of Uploaded Addresses Dataset:")
            st.write(new_addresses_df.head())

            # Validate column names
            expected_addresses_columns = {"User_ID", "Address"}
            addresses_columns_diff = expected_addresses_columns - set(new_addresses_df.columns)

            if addresses_columns_diff:
                st.warning(f"Missing columns in Addresses Dataset: {addresses_columns_diff}")
                new_columns = st.text_area("Enter correct column names (comma-separated):", ", ".join(new_addresses_df.columns), key="addresses_columns")
                if st.button("Update Addresses Column Names"):
                    try:
                        new_addresses_df.columns = [col.strip() for col in new_columns.split(",")]
                        st.success("Addresses dataset column names updated!")
                        st.write(new_addresses_df.head())
                    except Exception as e:
                        st.error(f"Error updating column names: {e}")

    # Process and update the datasets
    if st.button("Process Uploaded Files"):
        if uploaded_users and uploaded_addresses:
            try:
                # Process and update session state
                st.session_state.df_users = new_users_df
                st.session_state.df_addresses = new_addresses_df
                st.session_state.df_merged = process_data(new_users_df, new_addresses_df)
                st.session_state.df_details = get_details_table(st.session_state.df_merged)
                st.success("Datasets successfully processed and updated!")
            except Exception as e:
                st.error(f"Error processing files: {e}")
        else:
            st.error("Please upload both Users and Addresses datasets.")



