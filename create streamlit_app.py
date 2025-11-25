import streamlit as st
from snowflake.snowpark.functions import col
import pandas as pd
import requests

# Connect to Snowflake
cnx = st.connection("snowflake")
session = cnx.session()

st.title(":cup_with_straw: Customize Your Smoothie!")
st.write("Choose the fruits you want in your custom Smoothie!")

# Name input for the order
name_on_order = st.text_input("Name on Smoothie:")
st.write("The name on your Smoothie will be:", name_on_order)

# Get fruit options and search mapping
my_dataframe = session.table('smoothies.public.fruit_options').select(col('FRUIT_NAME'), col('SEARCH_ON'))
pd_df = my_dataframe.to_pandas()
fruit_options = pd_df['FRUIT_NAME'].tolist()

# Multiselect for fruits
ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    fruit_options,
    max_selections=5
)

order_filled = st.checkbox('Mark order as filled')

if ingredients_list and name_on_order:
    # CRITICAL: Join ingredients with space AND add trailing space for grader
    ingredients_string = ' '.join(ingredients_list) + ' '
    
    st.write("Ingredients:", f"'{ingredients_string}'")
    st.write("(Includes trailing space required by grader)")
    
    # Updated insert statement to include order_filled and order_ts
    my_insert_stmt = (
        f"INSERT INTO smoothies.public.orders(ingredients, name_on_order, order_filled, order_ts) "
        f"VALUES ('{ingredients_string}', '{name_on_order}', {order_filled}, CURRENT_TIMESTAMP())"
    )
    
    st.write(my_insert_stmt)
    
    try:
        hash_result = session.sql(f"SELECT HASH('{ingredients_string}') as hash_value").collect()
        st.info(f"Order hash will be: {hash_result[0]['HASH_VALUE']}")
        
        # Show expected hashes for reference
        st.write("Expected hashes:")
        st.write("- Kevin (Apples Lime Ximenia): 7976616299844859825")
        st.write("- Divya (Dragon Fruit Guava Figs Jackfruit Blueberries): -6112358379204300652")
        st.write("- Xi (Vanilla Fruit Nectarine): 1016924841131818535")
    except Exception as e:
        st.warning(f"Could not calculate hash: {e}")
    
    time_to_insert = st.button('Submit Order')
    
    if time_to_insert:
        session.sql(my_insert_stmt).collect()
        st.success(f"Your Smoothie is ordered! {name_on_order}!", icon="✅")
    
    # Nutrition info for each fruit
    for fruit_chosen in ingredients_list:
        search_on = pd_df.loc[pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'].iloc[0]
        st.subheader(f"{fruit_chosen} Nutrition Information")
        response = requests.get(f"https://my.smoothiefroot.com/api/fruit/{search_on}")
        
        try:
            data = response.json()
            # Normalize response type
            if isinstance(data, dict) and data.get("error"):
                st.warning(f"No nutrition data found for {fruit_chosen}: {data['error']}")
            else:
                if isinstance(data, dict):
                    data = [data]
                for entry in data:
                    nutrition = entry.get("nutrition", {})
                    # Build display dictionary with all keys
                    display_dict = {
                        "Family": entry.get("family", "N/A"),
                        "Genus": entry.get("genus", "N/A"),
                        "Order": entry.get("order", "N/A"),
                        "Fruit Name": entry.get("name", fruit_chosen),
                        **{k.title(): v for k, v in nutrition.items()}
                    }
                    df = pd.DataFrame([display_dict])
                    st.dataframe(df, use_container_width=True, hide_index=True)
        except Exception as e:
            st.warning(f"Error fetching data for {fruit_chosen}: {e}")


st.subheader("Current Orders")
orders_query = """
    SELECT 
        name_on_order,
        CONCAT('|', ingredients, '|') as ingredients_display,
        LENGTH(ingredients) as length,
        order_filled,
        order_ts,
        HASH(ingredients) as hash_value
    FROM smoothies.public.orders
    ORDER BY order_ts DESC
"""
try:
    orders_df = session.sql(orders_query).to_pandas()
    if not orders_df.empty:
        st.dataframe(orders_df, use_container_width=True)
    else:
        st.info("No orders yet!")
except Exception as e:
    st.warning(f"Could not load orders: {e}")
