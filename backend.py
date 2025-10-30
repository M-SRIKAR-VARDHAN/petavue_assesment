# =============================================================
# Excel AI Engine — FastAPI Backend (v4 - Multi-File & Write Ops)
# =============================================================

import pandas as pd
import google.generativeai as genai
import google.api_core.exceptions
import os
import numpy as np
import sys
import io
import re
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from tabulate import tabulate
import matplotlib.pyplot as plt
import seaborn as sns
import openpyxl
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from pathlib import Path

if not os.path.exists("plots"):
    os.makedirs("plots")
    print("📁 Created 'plots' directory to save visualizations.")

print("[Debug] Configuring API key...")
try:
    GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
    genai.configure(api_key=GOOGLE_API_KEY)
    print("[Debug] API key found and configured.")
except KeyError:
    print("❌ GOOGLE_API_KEY not found in environment variables.")
    sys.exit(1)
except Exception as e:
    print(f"❌ FATAL ERROR during API key setup: {e}")
    sys.exit(1)


try:
    model = genai.GenerativeModel("gemini-pro-latest")
    print("[Debug] Model configured successfully.")
except Exception as e:
    print(f"❌ Could not initialize model. {e}")
    sys.exit(1)


class QueryResponse(BaseModel):
    result: str
    executed_code: str
    is_plot: bool = False
    plot_path: str | None = None


app = FastAPI(title="Excel AI Engine (Multi-File & Write Ops)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/plots", StaticFiles(directory="plots"), name="plots")
print("[Debug] Mounted static path: /plots")


def sanitize_name(name):
    """Cleans a sheet name to be a valid Python variable name."""
    s = re.sub(r'\W|^(?=\d)', '_', name).strip()
    if not s:
        return "sheet"
    return s


@app.post("/analyze", response_model=QueryResponse)
async def analyze_uploaded_data(
    query: str = Form(...),
    excel_files: list[UploadFile] = File(...), # <-- CHANGED
):
    print(f"\n[Request] Query: '{query}' | Files: {[f.filename for f in excel_files]}")

    
    safe_globals = {
        "__builtins__": {
            "print": print, "len": len, "round": round, "abs": abs,
            "sum": sum, "min": min, "max": max, "str": str,
            "int": int, "float": float,
        },
        "pd": pd, "np": np, "plt": plt, "sns": sns,
    }
    
    schema_description = "You have access to the following pandas DataFrames:\n\n"


    try:
        if not excel_files:
             raise HTTPException(status_code=400, detail="No Excel files were uploaded.")

        for i, excel_file in enumerate(excel_files):
            contents = await excel_file.read()
            excel_data = io.BytesIO(contents)
            
            xls = pd.ExcelFile(excel_data, engine="openpyxl")
            sheet_names = xls.sheet_names
            
            if not sheet_names:
                schema_description += f"\n--- File '{excel_file.filename}' is empty. ---\n"
                continue

            print(f"[Debug] Loading file: {excel_file.filename} (Sheets: {sheet_names})")

            for sheet_name in sheet_names:
                # Create a unique var name, e.g., file1_Sheet1
                file_prefix = sanitize_name(Path(excel_file.filename).stem)
                sheet_suffix = sanitize_name(sheet_name)
                var_name = f"{file_prefix}_{sheet_suffix}"

                df = pd.read_excel(xls, sheet_name=sheet_name)
                safe_globals[var_name] = df
                
                # --- Auto-EDA "Cheat Sheet" ---
                info_stream = io.StringIO()
                df.info(buf=info_stream)
                info_string = info_stream.getvalue()
                head_string = df.head(3).to_string()
                
                schema_description += f"--- DataFrame: `{var_name}` (from file '{excel_file.filename}', sheet '{sheet_name}') ---\n"
                schema_description += f"1. Columns, Dtypes, and Non-Null Counts:\n{info_string}\n"
                schema_description += f"2. First 3 Rows of Data:\n{head_string}\n"
                schema_description += "---------------------------------------------------\n\n"
            
        print("[Debug] All files loaded and Auto-EDA complete.")
        print(f"[Debug] Schema for prompt:\n{schema_description}")

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error reading Excel file: {e}. Ensure it's a valid .xlsx file.",
        )

    # --- Master Prompt (FIXED FOR WRITE OPS) ---
    master_prompt = f"""
    You are an expert Python data analyst.
    Here is a summary of the data you have access to:
    
    {schema_description}
    
    You will write a block of Python code to answer the user's query.
    
    --- RULES ---
    1.  **Read-Only Queries (show, plot, what is):**
        -   If the user asks for data (e.g., "show top 5"), assign the final DataFrame or Series to a variable named `result_df`.
        -   If the user asks for a single number (e.g., "what is the average salary"), assign it to `result_value`.
        -   If the user asks for a plot, generate code to save it to 'plots/' and print the path (e.g., `print("Plot saved to plots/my_plot.png")`).
    
    2.  **Write Queries (create, add, join, pivot):**
        -   Perform the operation (e.g., `file1_Sheet1['new_col'] = ...`).
        -   After the operation, assign the **modified DataFrame** to `result_df` so the user can see the change.
    
    3.  **Examples:**
        -   Query: "what is the average salary in file1_Employees?"
            result_value = file1_Employees['Salary'].mean()
        
        -   Query: "show top 5 earners in file1_Employees"
            result_df = file1_Employees.nlargest(5, 'Salary')
            
        -   Query: "add a 'Bonus' column to file1_Employees which is 10% of salary"
            file1_Employees['Bonus'] = file1_Employees['Salary'] * 0.10
            result_df = file1_Employees
            
        -   Query: "join file1_Employees and file1_Projects on 'EmployeeID'"
            result_df = pd.merge(file1_Employees, file1_Projects, on='EmployeeID')
            
        -   Query: "plot salary distribution for file1_Employees"
            plt.figure(figsize=(10,6)); sns.histplot(file1_Employees['Salary']);
            plt.title('Salary Distribution');
            plt.savefig('plots/salary_dist.png');
            plt.close();
            print("Plot saved to plots/salary_dist.png")

    4.  **Important:**
        -   Output ONLY the raw Python code. No markdown, no explanations.
        -   All data is already loaded into DataFrames for you (e.g., `file1_Sheet1`, `file2_Portfolio`). You do not need to use `pd.read_excel`.
    """

    ai_code = ""
    try:
        print("[Debug] Generating AI code...")
        full_prompt = master_prompt + f"\nUser Question: {query}"
        response = model.generate_content(full_prompt)

        if not response or not hasattr(response, "text"):
            raise HTTPException(status_code=500, detail="AI returned empty response.")
        ai_code = response.text.strip()
        print(f"[Debug] AI generated code:\n{ai_code}")

        
        # --- Code Cleaner ---
        cleaned_lines = []
        for line in ai_code.splitlines():
            stripped_line = line.strip()
            if stripped_line.startswith("import "):
                print(f"[Info] Removing import line: {stripped_line}")
                continue
            if stripped_line.startswith("```"):
                continue
            cleaned_lines.append(line)
        ai_code = "\n".join(cleaned_lines).strip()


        # --- Manual safety scan ---
        dangerous_words = ["os.", "sys", "subprocess", "open(", "exec(", "__"]
        if any(word in ai_code for word in dangerous_words) and "safe_globals['__builtins__']" not in ai_code:
             print(f"🚫 Unsafe word detected in code: {ai_code}")
             raise HTTPException(status_code=403, detail="Unsafe operation detected.")

        print(f"[Debug] Cleaned safe code to execute:\n{ai_code}")

        result_output, is_plot, plot_path = "", False, None
        local_scope = {} # This will capture the new variables

        # --- Execute Code (NEW LOGIC) ---
        output_stream = io.StringIO()
        sys.stdout = output_stream
        try:
            exec(ai_code, safe_globals, local_scope)
        finally:
            sys.stdout = sys.__stdout__
        
        # 1. Check if it was a plot
        print_output = output_stream.getvalue().strip()
        if "Plot saved to plots/" in print_output:
            is_plot = True
            rel_path = print_output.replace("Plot saved to ", "").strip()
            plot_path = os.path.basename(rel_path)
            result_output = print_output
            print(f"[Debug] Plot file: {plot_path}")
        
        # 2. If not a plot, check for `result_df`
        elif "result_df" in local_scope:
            print("[Debug] Found `result_df` variable.")
            result_df = local_scope["result_df"]
            if isinstance(result_df, pd.DataFrame):
                result_output = tabulate(result_df.head(20), headers="keys", tablefmt="psql")
            elif isinstance(result_df, pd.Series):
                result_output = tabulate(result_df.to_frame().head(20), headers="keys", tablefmt="psql")
            else:
                result_output = str(result_df)
        
        # 3. If not, check for `result_value`
        elif "result_value" in local_scope:
            print("[Debug] Found `result_value` variable.")
            result_output = str(local_scope["result_value"])
        
        # 4. If nothing else, just return the print output (if any)
        else:
            print("[Debug] No plot, result_df, or result_value found. Returning print output.")
            result_output = print_output if print_output else "Code executed, but no result was returned."


        return QueryResponse(
            result=result_output, executed_code=ai_code,
            is_plot=is_plot, plot_path=plot_path
        )

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"--- ERROR --- {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=f"Error executing AI code: {type(e).__name__}: {e}. AI Code: {ai_code}")


@app.get("/")
async def root():
    return {"message": "✅ Excel AI Engine API (Multi-File & Write Ops) running. Go to /docs."}