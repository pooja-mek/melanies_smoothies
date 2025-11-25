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

if ingredients_list and name_on_order:
    ingredients_string = ' '.join(ingredients_list)
    st.write(ingredients_string)

    my_insert_stmt = (
        f"insert into smoothies.public.orders(ingredients, name_on_order) "
        f"values ('{ingredients_string}', '{name_on_order}')"
    )
    st.write(my_insert_stmt)

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
