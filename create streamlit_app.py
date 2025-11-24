import streamlit as st
from snowflake.snowpark.functions import col
import pandas as pd
import requests

# Set the page configuration for a wider layout (optional but good practice)
st.set_page_config(layout="wide")

# 1. Database Connection and Session Setup
# Assumes 'snowflake' is configured in your Streamlit secrets
cnx = st.connection("snowflake")
session = cnx.session()

st.title(":cup_with_straw: Customize Your Smoothie!")
st.write("Choose the fruits you want in your custom Smoothie!")

# 2. User Input - Name
name_on_order = st.text_input("Name on Smoothie:")

# 3. Data Fetching and Pandas Conversion for Multiselect
# Use st.cache_data to speed up the app by caching the data fetch
@st.cache_data
def get_fruit_data():
    my_dataframe = session.table('smoothies.public.fruit_options').select(
        col('FRUIT_NAME'), col('SEARCH_ON')
    )
    return my_dataframe.to_pandas()

pd_df = get_fruit_data()
fruit_options = pd_df['FRUIT_NAME'].tolist()

# 4. User Input - Ingredients Multiselect
ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    fruit_options,
    max_selections=5
)

# 5. Order Submission and API Fetching
if ingredients_list and name_on_order:
    ingredients_string = ' '.join(ingredients_list)
    
    # --- ORDER SUBMISSION SECTION ---
    time_to_insert = st.button('Submit Order')
    
    if time_to_insert:
        # SECURE INSERT: Use Snowpark's parameter binding (%s) to prevent SQL injection
        sql_insert = (
            "INSERT INTO smoothies.public.orders (ingredients, name_on_order) "
            "VALUES (%s, %s)"
        )
        # Pass the values as a tuple
        session.sql(sql_insert, (ingredients_string, name_on_order)).collect()
        st.success(f"Your Smoothie is ordered! {name_on_order}!", icon="✅")
    
    st.markdown("---")
    
    # --- NUTRITION INFORMATION SECTION ---
    for fruit_chosen in ingredients_list:
        # Get the SEARCH_ON value from the Pandas DataFrame
        search_on = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]
        
        st.subheader(f":apple: {fruit_chosen} Nutrition Information")
        response = requests.get(f"https://my.smoothiefroot.com/api/fruit/{search_on}")
        
        try:
            data = response.json()
            
            # Ensure 'data' is a list for uniform handling
            if not isinstance(data, list):
                data = [data]
            
            if data:
                # Process and display all entries
                for entry in data:
                    nutrition_data = entry.get('nutrition', {})
                    
                    # Create the display dictionary, explicitly including all top-level keys
                    display_dict = {
                        "Fruit Name": entry.get('name', fruit_chosen),
                        "Family": entry.get('family', 'N/A'),
                        "Genus": entry.get('genus', 'N/A'),
                        "Order": entry.get('order', 'N/A'),
                        # Add all the nutrition data, cleaning up the key names
                        **{k.replace('_', ' ').title(): v for k, v in nutrition_data.items()}
                    }
                    
                    df = pd.DataFrame([display_dict])
                    # Use hide_index=True for a cleaner table
                    st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.warning(f"No nutrition data found for {fruit_chosen}")
                
        except Exception as e:
            st.error(f"Error fetching/parsing API data for {fruit_chosen}: {e}")
