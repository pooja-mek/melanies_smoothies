import streamlit as st
from snowflake.snowpark.functions import col
import requests

cnx = st.connection("snowflake")
session = cnx.session()

st.title(":cup_with_straw: Customize Your Smoothie!")
st.write("Choose the fruits you want in your custom Smoothie!")

name_on_order = st.text_input("Name on Smoothie:")
st.write("The name on your Smoothie will be:", name_on_order)

fruit_options_df = session.table("smoothies.public.fruit_options").select('FRUIT_NAME', 'SEARCH_ON').to_pandas()
fruit_options = fruit_options_df['FRUIT_NAME'].tolist()

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

    for fruit_chosen in ingredients_list:
        search_term = fruit_options_df.loc[
            fruit_options_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'
        ].values[0]
        st.subheader(f"{fruit_chosen} Nutrition Information")
        response = requests.get(f"https://my.smoothiefroot.com/api/fruit/{search_term}")
        try:
            data = response.json()
            if isinstance(data, list) and data:
                st.dataframe(data=data, use_container_width=True)
            elif isinstance(data, dict) and "error" in data:
                st.dataframe(data)
            else:
                st.warning(f"No nutrition data found for {fruit_chosen}")
        except Exception as e:
            st.warning(f"Error fetching data for {fruit_chosen}: {e}")
