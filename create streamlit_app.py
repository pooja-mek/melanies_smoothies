import streamlit as st
from snowflake.snowpark.functions import col
import requests  # Required for SmoothieFroot API

# Snowflake connection (for SniS, not SiS)
cnx = st.connection("snowflake")
session = cnx.session()

st.title(":cup_with_straw: Customize Your Smoothie!")
st.write("Choose the fruits you want in your custom Smoothie!")

# Name input for smoothie order
name_on_order = st.text_input("Name on Smoothie:")
st.write("The name on your Smoothie will be:", name_on_order)

my_dataframe = session.table("smoothies.public.fruit_options")
fruit_options = my_dataframe.select('FRUIT_NAME').to_pandas()['FRUIT_NAME'].tolist()

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

# --- SmoothieFroot API Section ---
smoothiefroot_response = requests.get("https://my.smoothiefroot.com/api/fruit/watermelon")

# To just show the JSON raw:
# st.text(smoothiefroot_response.json())

# To show the info as a table:
sf_df = st.dataframe(data=smoothiefroot_response.json(), use_container_width=True)
