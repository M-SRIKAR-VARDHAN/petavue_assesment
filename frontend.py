
import streamlit as st
import requests
from pathlib import Path


API_URL = "http://127.0.0.1:8000/analyze" 

st.set_page_config(page_title="Excel AI Engine", layout="wide")

st.title("📊 Excel AI Engine — Natural Language Data Analyst")

st.markdown(
    """
This app connects to your **FastAPI backend** powered by Google's Gemini model.

**Instructions:**
1. Upload an Excel file with sheets named **`Employees`** and **`Projects`**
2. Type a natural language question (e.g., *"show average salary by department"*)
3. Click **Analyze**
4. View the result or generated visualization below.
"""
)

with st.form("query_form"):
    excel_file = st.file_uploader("📁 Upload Excel (.xlsx)", type=["xlsx"], accept_multiple_files=False)
    query = st.text_input("💬 Enter your question")
    submit = st.form_submit_button("Analyze")


if submit:
    if not excel_file:
        st.warning("Please upload an Excel file before analyzing.")
    elif not query.strip():
        st.warning("Please enter a query to analyze.")
    else:
        try:
            files = {
                "excel_file": (
                    excel_file.name,
                    excel_file.getbuffer(),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            }
            data = {"query": query}

            with st.spinner("⏳ Sending request to backend..."):
                response = requests.post(API_URL, data=data, files=files, timeout=120)


            if response.status_code != 200:
                st.error(f"❌ API Error {response.status_code}: {response.text}")
            else:
                result = response.json()

                st.success("✅ Analysis completed successfully!")

                st.subheader("📈 Result")
                st.code(result.get("result", ""), language="text")

                st.subheader("🧠 AI-Generated Code")
                st.code(result.get("executed_code", ""), language="python")

               
                if result.get("is_plot"):
                    plot_path = result.get("plot_path")
                    if plot_path:
                        plot_filename = Path(plot_path).name
                        plot_url = f"http://127.0.0.1:8000/plots/{plot_filename}"
                        st.subheader("🎨 Generated Plot")
                        st.image(plot_url, use_column_width=True)
                    else:
                        st.info("The AI indicated a plot was generated, but no file path was returned.")
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
