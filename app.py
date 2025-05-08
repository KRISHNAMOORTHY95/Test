import pandas as pd
import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import os
!pip install streamlit

DB_NAME = 'food_waste.db'
DATA_DIR = 'data'  # Directory to store CSV data files

def execute_query(query, params=None):
    """Executes an SQL query and fetches the results."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)
    results = cursor.fetchall()
    conn.commit()
    conn.close()
    return results

def create_database():
    """Creates the SQLite database and tables."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Create Providers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Providers (
            Provider_ID INTEGER PRIMARY KEY,
            Name TEXT,
            Type TEXT,
            Address TEXT,
            City TEXT,
            Contact TEXT
        )
    ''')

    # Create Receivers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Receivers (
            Receiver_ID INTEGER PRIMARY KEY,
            Name TEXT,
            Type TEXT,
            City TEXT,
            Contact TEXT
        )
    ''')

    # Create FoodListings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS FoodListings (
            Food_ID INTEGER PRIMARY KEY,
            Food_Name TEXT,
            Quantity INTEGER,
            Expiry_Date DATE,
            Provider_ID INTEGER,
            Provider_Type TEXT,
            Location TEXT,
            Food_Type TEXT,
            Meal_Type TEXT,
            FOREIGN KEY (Provider_ID) REFERENCES Providers(Provider_ID)
        )
    ''')

    # Create Claims table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Claims (
            Claim_ID INTEGER PRIMARY KEY,
            Food_ID INTEGER,
            Receiver_ID INTEGER,
            Status TEXT,
            Timestamp DATETIME,
            FOREIGN KEY (Food_ID) REFERENCES FoodListings(Food_ID),
            FOREIGN KEY (Receiver_ID) REFERENCES Receivers(Receiver_ID)
        )
    ''')

    conn.commit()
    conn.close()
    print(f"Database '{DB_NAME}' created successfully.")


def load_data_to_db():
    """Loads data from CSV files into the SQLite database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Load Providers data
    try:
        providers_df = pd.read_csv(os.path.join(DATA_DIR, 'providers_data.csv'))
        providers_df.to_sql('Providers', conn, if_exists='replace', index=False)
    except FileNotFoundError:
        print(f"File not found: {os.path.join(DATA_DIR, 'providers_data.csv')}.  Please ensure the file exists or create a dummy file.")

    # Load Receivers data
    try:
        receivers_df = pd.read_csv(os.path.join(DATA_DIR, 'receivers_data.csv'))
        receivers_df.to_sql('Receivers', conn, if_exists='replace', index=False)
    except FileNotFoundError:
        print(f"File not found: {os.path.join(DATA_DIR, 'receivers_data.csv')}.  Please ensure the file exists or create a dummy file.")
    # Load FoodListings data
    try:
        food_listings_df = pd.read_csv(os.path.join(DATA_DIR, 'food_listings_data.csv'))
        food_listings_df.to_sql('FoodListings', conn, if_exists='replace', index=False)
    except FileNotFoundError:
        print(f"File not found: {os.path.join(DATA_DIR, 'food_listings_data.csv')}.  Please ensure the file exists or create a dummy file.")

    # Load Claims data
    try:
        claims_df = pd.read_csv(os.path.join(DATA_DIR, 'claims_data.csv'))
        claims_df.to_sql('Claims', conn, if_exists='replace', index=False)
    except FileNotFoundError:
        print(f"File not found: {os.path.join(DATA_DIR, 'claims_data.csv')}.  Please ensure the file exists or create a dummy file.")

    conn.commit()
    conn.close()
    print("Data loaded successfully into the database.")



def display_food_listings():
    """Displays the food listings with filtering, update, and delete options."""

    st.header("Food Listings")

    # Filtering options
    city_filter = st.selectbox("Filter by City", ["All"] + get_unique_values("FoodListings", "Location"))
    food_type_filter = st.selectbox("Filter by Food Type", ["All"] + get_unique_values("FoodListings", "Food_Type"))
    meal_type_filter = st.selectbox("Filter by Meal Type", ["All"] + get_unique_values("FoodListings", "Meal_Type"))

    query = """
        SELECT
            fl.Food_ID,
            fl.Food_Name,
            fl.Quantity,
            fl.Expiry_Date,
            p.Name as Provider_Name,
            p.Contact as Provider_Contact,
            fl.Location,
            fl.Food_Type,
            fl.Meal_Type
        FROM FoodListings fl
        JOIN Providers p ON fl.Provider_ID = p.Provider_ID
        WHERE 1=1  -- Base condition to easily add filters
    """
    filters = []
    params = []

    if city_filter != "All":
        filters.append("fl.Location = ?")
        params.append(city_filter)
    if food_type_filter != "All":
        filters.append("fl.Food_Type = ?")
        params.append(food_type_filter)
    if meal_type_filter != "All":
        filters.append("fl.Meal_Type = ?")
        params.append(meal_type_filter)

    if filters:
        query += " AND " + " AND ".join(filters)

    results = execute_query(query, params)
    df = pd.DataFrame(results, columns=[
        "Food_ID", "Food_Name", "Quantity", "Expiry_Date", "Provider_Name",
        "Provider_Contact", "Location", "Food_Type", "Meal_Type"
    ])

    st.dataframe(df)

    # Update and Delete Functionality
    st.subheader("Update/Delete Food Listing")
    selected_food_id = st.selectbox("Select Food Listing to Update/Delete", ["None"] + list(df["Food_ID"]))

    if selected_food_id != "None":
        update_delete_food_listing(selected_food_id)


def update_delete_food_listing(food_id):
    """Updates or deletes a selected food listing."""

    query = "SELECT * FROM FoodListings WHERE Food_ID = ?"
    result = execute_query(query, (food_id,))
    if result:
        listing = result[0]  # Get the first (and only) row
        food_name, quantity, expiry_date, provider_id, location, food_type, meal_type = listing[1:]

        # Update
        st.subheader("Update Listing")
        new_food_name = st.text_input("Food Name", food_name)
        new_quantity = st.number_input("Quantity", value=quantity, min_value=1, step=1)
        new_expiry_date = st.date_input("Expiry Date", datetime.strptime(expiry_date, '%Y-%m-%d'))
        new_location = st.text_input("Location", location)
        new_food_type = st.selectbox("Food Type", get_unique_values("FoodListings", "Food_Type"),
                                    index=get_unique_values("FoodListings", "Food_Type").index(food_type))
        new_meal_type = st.selectbox("Meal Type", get_unique_values("FoodListings", "Meal_Type"),
                                    index=get_unique_values("FoodListings", "Meal_Type").index(meal_type))

        if st.button("Update"):
            update_query = """
                UPDATE FoodListings
                SET Food_Name = ?, Quantity = ?, Expiry_Date = ?, Location = ?, Food_Type = ?, Meal_Type = ?
                WHERE Food_ID = ?
            """
            execute_query(update_query, (new_food_name, new_quantity, new_expiry_date, new_location, new_food_type, new_meal_type, food_id))
            st.success("Food listing updated successfully!")
            st.rerun()  # Refresh the page to show updated data

        # Delete
        st.subheader("Delete Listing")
        if st.button("Delete"):
            delete_query = "DELETE FROM FoodListings WHERE Food_ID = ?"
            execute_query(delete_query, (food_id,))
            st.success("Food listing deleted successfully!")
            st.rerun()


def add_food_listing():
    """Adds a new food listing."""
    st.header("Add Food Listing")
    food_name = st.text_input("Food Name")
    quantity = st.number_input("Quantity", min_value=1, step=1)
    expiry_date = st.date_input("Expiry Date", datetime.now().date())
    provider_id = st.selectbox("Provider", get_unique_values("Providers", "Provider_ID"))
    location = st.text_input("Location")
    food_type = st.selectbox("Food Type", get_unique_values("FoodListings", "Food_Type"))
    meal_type = st.selectbox("Meal Type", get_unique_values("FoodListings", "Meal_Type"))

    if st.button("Add Listing"):
        query = """
            INSERT INTO FoodListings (Food_Name, Quantity, Expiry_Date, Provider_ID, Location, Food_Type, Meal_Type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        params = (food_name, quantity, expiry_date, provider_id, location, food_type, meal_type)
        execute_query(query, params)
        st.success("Food listing added successfully!")



def get_unique_values(table, column):
    """Gets unique values from a table column for filter/dropdown options."""
    query = f"SELECT DISTINCT {column} FROM {table}"
    results = execute_query(query)
    return [row[0] for row in results]



def display_data(table_name):
    """Displays data from a given table."""
    st.header(f"View {table_name}")
    query = f"SELECT * FROM {table_name}"
    results = execute_query(query)
    df = pd.DataFrame(results, columns=[description[0] for description in execute_query(f"PRAGMA table_info({table_name})")])
    st.dataframe(df)



def display_sql_queries():
    """Displays and executes SQL queries."""

    st.header("Execute SQL Queries")

    query_choice = st.selectbox("Select a Query", [
        "How many food providers and receivers are there in each city?",
        "Which type of food provider contributes the most food?",
        "What is the contact information of food providers in a specific city?",
        "Which receivers have claimed the most food?",
        "What is the total quantity of food available from all providers?",
        "What percentage of food claims are completed?",
        "What is the average quantity of food claimed per receiver?",
        "Providers with highest success rate in fulfilling claims",
        "Food type with the highest demand",
        "Quantity of food claimed over time",
        "Locations with the most expired food",
        "Distribution of claims status",
        "Providers who have provided food claimed by NGOs"
    ])

    if st.button("Execute Query"):
        if query_choice == "How many food providers and receivers are there in each city?":
            query = """
                SELECT
                    City,
                    COUNT(DISTINCT CASE WHEN table_name = 'Providers' THEN Provider_ID ELSE NULL END) as num_providers,
                    COUNT(DISTINCT CASE WHEN table_name = 'Receivers' THEN Receiver_ID ELSE NULL END) as num_receivers
                FROM (
                    SELECT City, Provider_ID, 'Providers' as table_name FROM Providers
                    UNION ALL
                    SELECT City, Receiver_ID, 'Receivers' as table_name FROM Receivers
                )
                GROUP BY City
            """
        elif query_choice == "Which type of food provider contributes the most food?":
            query = """
                SELECT
                    Provider_Type,
                    SUM(Quantity) as total_quantity
                FROM FoodListings
                GROUP BY Provider_Type
                ORDER BY total_quantity DESC
                LIMIT 1
            """
        elif query_choice == "What is the contact information of food providers in a specific city?":
            city = st.text_input("Enter City Name")
            if city:
                query = f"""
                    SELECT
                        Name,
                        Contact
                    FROM Providers
                    WHERE City = '{city}'
                """
            else:
                st.warning("Please enter a city name.")
                return
        elif query_choice == "Which receivers have claimed the most food?":
            query = """
                SELECT
                    r.Name,
                    COUNT(c.Receiver_ID) as num_claims
                FROM Receivers r
                JOIN Claims c ON r.Receiver_ID = c.Receiver_ID
                GROUP BY r.Name
                ORDER BY num_claims DESC
            """
        elif query_choice == "What is the total quantity of food available from all providers?":
            query = "SELECT SUM(Quantity) FROM FoodListings"
        elif query_choice == "What percentage of food claims are completed?":
            query = """
                SELECT
                    CAST(SUM(CASE WHEN Status = 'Completed' THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(*)
                FROM Claims
            """
        elif query_choice == "What is the average quantity of food claimed per receiver?":
            query = """
                SELECT
                    r.Name,
                    AVG(fl.Quantity)
                FROM Claims c
                JOIN Receivers r ON c.Receiver_ID = r.Receiver_ID
                JOIN FoodListings fl ON c.Food_ID = fl.Food_ID
                GROUP BY r.Name
            """
        elif query_choice == "Providers with highest success rate in fulfilling claims":
            query = """
                SELECT
                    p.Name AS ProviderName,
                    CAST(SUM(CASE WHEN c.Status = 'Completed' THEN 1 ELSE 0 END) AS REAL) / COUNT(c.Claim_ID) AS SuccessRate
                FROM
                    Providers p
                JOIN
                    FoodListings fl ON p.Provider_ID = fl.Provider_ID
                JOIN
                    Claims c ON fl.Food_ID = c.Food_ID
                GROUP BY
                    p.Provider_ID, p.Name
                ORDER BY
                    SuccessRate DESC;
                """
        elif query_choice == "Food type with the highest demand":
            query = """
                SELECT
                    Food_Type,
                    COUNT(c.Food_ID) AS ClaimCount
                FROM
                    FoodListings fl
                JOIN
                    Claims c ON fl.Food_ID = c.Food_ID
                GROUP BY
                    Food_Type
                ORDER BY
                    ClaimCount DESC
                LIMIT 1;
                """
        elif query_choice == "Quantity of food claimed over time":
            query = """
                SELECT
                    DATE(Timestamp) AS ClaimDate,
                    SUM(fl.Quantity) AS TotalQuantityClaimed
                FROM
                    Claims c
                JOIN
                    FoodListings fl ON c.Food_ID = fl.Food_ID
                GROUP BY
                    DATE(Timestamp)
                ORDER BY
                    ClaimDate;
                """
        elif query_choice == "Locations with the most expired food":
            query = """
                SELECT
                    Location,
                    COUNT(*) AS ExpiredFoodCount
                FROM
                    FoodListings
                WHERE
                    Expiry_Date < DATE('now')
                GROUP BY
                    Location
                ORDER BY
                    ExpiredFoodCount DESC;
                """
        elif query_choice == "Distribution of claims status":
            query = """
                SELECT
                    Status,
                    COUNT(*) AS ClaimCount,
                    (COUNT(*) * 100.0 / (SELECT COUNT(*) FROM Claims)) AS Percentage
                FROM
                    Claims
                GROUP BY
                    Status;
                """
        elif query_choice == "Providers who have provided food claimed by NGOs":
            query = """
                SELECT DISTINCT
                    p.Name AS ProviderName
                FROM
                    Providers p
                JOIN
                    FoodListings fl ON p.Provider_ID = fl.Provider_ID
                JOIN
                    Claims c ON fl.Food_ID = c.Food_ID
                JOIN
                    Receivers r ON c.Receiver_ID = r.Receiver_ID
                WHERE
                    r.Type = 'NGO';
                """
        else:
            query = ""

        if query:
            results = execute_query(query)
            st.subheader("Query Results")
            st.dataframe(results)


def display_food_wastage_by_type_chart():
    """Displays a bar chart of food wastage by food type."""

    st.header("Food Wastage by Food Type")

    query = """
        SELECT
            Food_Type,
            SUM(Quantity) as Total_Quantity
        FROM FoodListings
        GROUP BY Food_Type
        ORDER BY Total_Quantity DESC
    """
    results = execute_query(query)
    df = pd.DataFrame(results, columns=["Food_Type", "Total_Quantity"])

    # Create the bar chart
    plt.figure(figsize=(10, 6))
    sns.barplot(x="Food_Type", y="Total_Quantity", data=df)
    plt.xlabel("Food Type")
    plt.ylabel("Total Quantity")
    plt.title("Total Quantity of Food by Type")
    st.pyplot(plt)  # Display the chart in Streamlit



def create_dummy_csv_files():
    """
    Creates dummy CSV files for testing purposes if they don't exist.
    """
    # Ensure the data directory exists
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    # Create dummy data for providers
    providers_data = {
        'Provider_ID': [1, 2, 3],
        'Name': ['Provider A', 'Provider B', 'Provider C'],
        'Type': ['Restaurant', 'Supermarket', 'Cafe'],
        'Address': ['123 Main St', '456 Oak Ave', '789 Pine Ln'],
        'City': ['Anytown', 'Anytown', 'Otherville'],
        'Contact': ['555-1234', '555-5678', '555-9012']
    }
    providers_df = pd.DataFrame(providers_data)
    providers_df.to_csv(os.path.join(DATA_DIR, 'providers_data.csv'), index=False)

    # Create dummy data for receivers
    receivers_data = {
        'Receiver_ID': [101, 102, 103],
        'Name': ['Receiver X', 'Receiver Y', 'Receiver Z'],
        'Type': ['NGO', 'Shelter', 'Individual'],
        'City': ['Anytown', 'Otherville', 'Anytown'],
        'Contact': ['555-2468', '555-1357', '555-8023']
    }
    receivers_df = pd.DataFrame(receivers_data)
    receivers_df.to_csv(os.path.join(DATA_DIR, 'receivers_data.csv'), index=False)

    # Create dummy data for food listings
    food_listings_data = {
        'Food_ID': [1001, 1002, 1003, 1004, 1005],
        'Food_Name': ['Pizza', 'Bread', 'Soup', 'Salad', 'Fruits'],
        'Quantity': [10, 20, 15, 8, 25],
        'Expiry_Date': ['2024-05-10', '2024-05-11', '2024-05-12', '2024-05-13', '2024-05-14'],
        'Provider_ID': [1, 2, 1, 3, 2],
        'Provider_Type': ['Restaurant', 'Supermarket', 'Restaurant', 'Cafe', 'Supermarket'],
        'Location': ['Anytown', 'Anytown', 'Anytown', 'Otherville', 'Otherville'],
        'Food_Type': ['Prepared', 'Bakery', 'Prepared', 'Produce', 'Produce'],
        'Meal_Type': ['Dinner', 'Breakfast', 'Lunch', 'Lunch', 'Snack']
    }
    food_listings_df = pd.DataFrame(food_listings_data)
    food_listings_df.to_csv(os.path.join(DATA_DIR, 'food_listings_data.csv'), index=False)

    # Create dummy data for claims
    claims_data = {
        'Claim_ID': [2001, 2002, 2003, 2004],
        'Food_ID': [1001, 1002, 1003, 1005],
        'Receiver_ID': [101, 102, 101, 103],
        'Status': ['Completed', 'Pending', 'Completed', 'Cancelled'],
        'Timestamp': ['2024-05-08 12:00:00', '2024-05-08 14:30:00', '2024-05-09 09:00:00', '2024-05-09 11:00:00']
    }
    claims_df = pd.DataFrame(claims_data)
    claims_df.to_csv(os.path.join(DATA_DIR, 'claims_data.csv'), index=False)

def main():
    """Main function to run the Streamlit app."""
    # Create and load data if the database doesn't exist
    if not os.path.exists(DB_NAME):
        create_database()
        # Create a dummy data directory if it doesn't exist.
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
        # Create dummy CSV files.
        create_dummy_csv_files()
        load_data_to_db()
conn.close()
