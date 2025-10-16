import openai
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy import text
from google.cloud import bigquery
import chardet
import os
import plotly.express as px
from pandas_profiling import ProfileReport
from streamlit_pandas_profiling import st_profile_report

# Set up OpenAI API key
openai.api_key = st.secrets["sk-a62sffWL2i723Xn4UKKSGG3JLtI1aC0tgApeKjl6d1T3BlbkFJxcLPWUetO7FONb3M0TQPW5B7QmG0XLVHSVBgmaeoEA"]

# Streamlit app interface
st.set_page_config(page_title="AI SQL Query Tool", layout="wide")

# Add dark mode
st.markdown("""
<style>
    .stApp {
        background-color: #2b2b2b;
        color: #ffffff;
    }
</style>
""", unsafe_allow_html=True)

st.title("AI SQL Query Tool")

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(["Local File", "Other SQL Database", "Azure SQL", "Google BigQuery"])

# Function to generate SQL query
def generate_sql_query(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an SQL expert. Generate only the SQL query without any explanations."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        st.error(f"Error generating SQL query: {e}")
        return None

# Function to execute query and display results
def execute_query_and_display(engine, sql_query):
    try:
        with st.spinner("Executing query..."):
            result_df = pd.read_sql_query(text(sql_query), con=engine)
        st.write("### Query Results")
        st.dataframe(result_df.reset_index(drop=True))
        
        # Data Visualization
        if not result_df.empty:
            st.subheader("Data Visualization")
            chart_type = st.selectbox("Select chart type", ["Bar", "Line", "Scatter"])
            x_column = st.selectbox("Select X-axis", result_df.columns)
            y_column = st.selectbox("Select Y-axis", result_df.columns)
            
            if chart_type == "Bar":
                fig = px.bar(result_df, x=x_column, y=y_column)
            elif chart_type == "Line":
                fig = px.line(result_df, x=x_column, y=y_column)
            else:
                fig = px.scatter(result_df, x=x_column, y=y_column)
            
            st.plotly_chart(fig)
    except Exception as e:
        st.error(f"Error executing SQL query: {e}")

# Tab 1: Local File Upload
with tab1:
    st.subheader("Upload CSV or Excel File")
    uploaded_file = st.file_uploader("Choose a CSV or Excel file", type=["csv", "xlsx"])
    if uploaded_file:
        if uploaded_file.name.endswith(".csv"):
            raw_data = uploaded_file.read(1024)
            result = chardet.detect(raw_data)
            detected_encoding = result['encoding']
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, encoding=detected_encoding, encoding_errors='ignore')
        else:
            df = pd.read_excel(uploaded_file, engine='openpyxl')
        
        st.write("### Data Preview", df.head())
        
        # Data Profiling
        if st.button("Generate Data Profile"):
            profile = ProfileReport(df, explorative=True)
            st_profile_report(profile)
        
        engine = create_engine("sqlite://", echo=False)
        df.to_sql("uploaded_data", con=engine, if_exists="replace", index=False)
        
        query_text = st.text_area("Enter your question about the data", placeholder="E.g., 'Show total sales by region'")
        if query_text:
            prompt = f"""
            Based on the following database schema, create an SQL query:
            Schema:
            {df.dtypes}
            
            Question: {query_text}
            
            Table name: 'uploaded_data'
            
            Example of a good query:
            SELECT region, SUM(sales) as total_sales
            FROM uploaded_data
            GROUP BY region
            ORDER BY total_sales DESC
            
            Provide only the SQL query, without any explanations.
            """
            
            sql_query = generate_sql_query(prompt)
            if sql_query:
                st.write("### SQL Query")
                st.code(sql_query, language='sql')
                execute_query_and_display(engine, sql_query)

# Tab 2: Other SQL Database Connection
with tab2:
    st.subheader("Connect to Other SQL Database")
    connection_string = st.text_input("Custom Connection String", placeholder="Enter your SQL connection string here")
    table_name_other = st.text_input("Enter the table name to query", placeholder="e.g., sales_data")
    query_text_other = st.text_area("Enter your question about the data", placeholder="E.g., 'Show total sales by region'")
    
    if connection_string and table_name_other and query_text_other:
        other_engine = create_engine(connection_string)
        try:
            with other_engine.connect() as conn:
                st.success("Connected to SQL Database!")
                prompt_other = f"""
                Based on the database schema in the '{table_name_other}' table, create an SQL query:
                
                Question: {query_text_other}
                
                Table name: '{table_name_other}'
                
                Example of a good query:
                SELECT region, SUM(sales) as total_sales
                FROM {table_name_other}
                GROUP BY region
                ORDER BY total_sales DESC
                
                Provide only the SQL query, without any explanations.
                """
                
                sql_query_other = generate_sql_query(prompt_other)
                if sql_query_other:
                    st.write("### SQL Query")
                    st.code(sql_query_other, language='sql')
                    execute_query_and_display(other_engine, sql_query_other)
        except Exception as e:
            st.error(f"Could not connect to the SQL Database: {e}")

# Tab 3 and Tab 4 can be implemented similarly with the improvements

# Add a sidebar for saved queries
st.sidebar.header("Saved Queries")
saved_queries = st.sidebar.text_area("Enter queries to save (one per line)")
if st.sidebar.button("Save Queries"):
    st.sidebar.success("Queries saved successfully!")

if saved_queries:
    selected_query = st.sidebar.selectbox("Select a saved query", saved_queries.split("\n"))
    if st.sidebar.button("Load Query"):
        st.experimental_set_query_params(query=selected_query)