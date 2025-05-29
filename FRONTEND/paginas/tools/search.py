import streamlit as st

st.title("🔍 Search")
query = st.text_input("Enter search query:")
if query:
    st.write(f"Searching for: {query}")