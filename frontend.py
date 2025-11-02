import streamlit as st
import requests
from pathlib import Path


API_URL = "https://srikar-excel-backend.onrender.com/analyze"
BASE_URL = "https://srikar-excel-backend.onrender.com"


st.set_page_config(page_title="Excel AI Engine", layout="wide")
st.title("📊 Excel AI Engine — Natural Language Data Analyst")

st.markdown(
    """
This app connects to your **FastAPI backend** powered by Google's Gemini model.

**Instructions:**
1. Upload one or more Excel files.
2. Type a natural language question (e.g., *"show average salary by department"* or *"join file1_sheet1 and file2_sheet1 on the 'ID' column"*).
3. Click **Analyze**
4. View the result or generated visualization below.
"""
)


with st.form("query_form"):
    excel_files = st.file_uploader(
        "📁 Upload Excel (.xlsx)", 
        type=["xlsx"], 
        accept_multiple_files=True 
    )
    query = st.text_input("💬 Enter your question")
    submit = st.form_submit_button("Analyze")


if submit:
    if not excel_files:
        st.warning("Please upload at least one Excel file before analyzing.")
    elif not query.strip():
        st.warning("Please enter a query to analyze.")
    else:
        try:
      
            files_list = [
                ("excel_files", (
                    file.name, 
                    file.getbuffer(), 
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )) for file in excel_files
            ]
            
            data = {"query": query}

       
            with st.spinner("⏳ Analyzing... Contacting AI engine..."):
                response = requests.post(
                    API_URL.strip(), 
                    data=data, 
                    files=files_list,  
                    timeout=180 
                )

         
            if response.status_code != 200:
                st.error(f"❌ API Error {response.status_code}: {response.text}")
            
         
            else:
                result = response.json()
                st.success("✅ Analysis completed successfully!")

         
                result_text = result.get("result", "No text result returned.")
                executed_code = result.get("executed_code", "No code returned.")
                is_plot = result.get("is_plot", False)
                plot_filename = result.get("plot_path")
                csv_data = result.get("csv_data") 

              
                if is_plot and plot_filename:
                 
                    st.subheader("🎨 Generated Plot")
                    plot_url = f"{BASE_URL.strip()}/plots/{plot_filename}"
                    st.image(plot_url, use_column_width=True)
                    st.markdown(f"*(Plot served from: {plot_url})*")
                    
                    st.subheader("📈 Result Text")
                    st.code(result_text, language="text") 
                
                else:
               
                    st.subheader("📈 Result")
                    st.code(result_text, language="text")
                    
                  
                    if csv_data:
                        st.download_button(
                            label="Download results as CSV",
                            data=csv_data,
                            file_name="analysis_results.csv",
                            mime="text/csv",
                        )
                  

                
                st.subheader("🧠 AI-Generated Code")
                st.code(executed_code, language="python")

        except requests.exceptions.RequestException as e:
            st.error(f"🚨 Connection error: {e}")

st.markdown(
    """
---
**Excel AI Engine v1.0**
  
Backend: FastAPI + Gemini  
Frontend: Streamlit  
"""
)