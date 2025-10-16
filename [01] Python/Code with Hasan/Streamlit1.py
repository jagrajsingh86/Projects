import streamlit as st
st.title('My First Streamlit App')
# User input
user_name = st.text_input("Enter your name", "Type Here")
# Displaying input
if st.button("Greet"):
    st.write(f"Hello, {user_name}!")
# Chart
chart_data = {
    'Days': ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    'Productivity': [50, 60, 55, 67, 80]
}
st.bar_chart(chart_data)