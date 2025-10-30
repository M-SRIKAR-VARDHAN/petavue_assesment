
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

app = FastAPI(title="Excel AI Engine (Smart EDA)")
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
    excel_file: UploadFile = File(...),
):
    print(f"\n[Request] Query: '{query}' | File: '{excel_file.filename}'")


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
        contents = await excel_file.read()
        excel_data = io.BytesIO(contents)
        
        xls = pd.ExcelFile(excel_data, engine="openpyxl")
        sheet_names = xls.sheet_names
        
        if not sheet_names:
            raise HTTPException(status_code=400, detail="The uploaded Excel file is empty or contains no sheets.")

        print(f"[Debug] Found sheets: {sheet_names}")


        for sheet_name in sheet_names:
            var_name = sanitize_name(sheet_name)
            df = pd.read_excel(xls, sheet_name=sheet_name)
            safe_globals[var_name] = df
            

            info_stream = io.StringIO()
            df.info(buf=info_stream)
            info_string = info_stream.getvalue()
            

            head_string = df.head(3).to_string()
            

            schema_description += f"--- DataFrame: `{var_name}` (from sheet '{sheet_name}') ---\n"
            schema_description += f"1. Columns, Dtypes, and Non-Null Counts:\n{info_string}\n"
            schema_description += f"2. First 3 Rows of Data (to see headers):\n{head_string}\n"
            schema_description += "---------------------------------------------------\n\n"
            
        print("[Debug] Excel loaded and Auto-EDA complete.")
        print(f"[Debug] Schema for prompt:\n{schema_description}")

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Error reading Excel file: {e}. Ensure it's a valid .xlsx file.",
        )


    master_prompt = f"""
    You are an expert Python data analyst.
    Here is a summary of the data you have access to:
    
    {schema_description}
    
    - Access to plt and sns for plotting.

    Your response MUST be in one of two modes.
    Do NOT state which mode you are in.
    Do NOT add any explanations, headers, markdown, or text.
    Output ONLY the raw Python code required.

    MODE 1 (for data/table/number queries):
    - Return a single, valid Python expression.
    - Example: {sanitize_name(sheet_names[0])}.describe()
    - Example: {sanitize_name(sheet_names[0])}['SomeColumn'].mean()

    MODE 2 (for plot/graph queries):
    - Return a block of Python code to create, save, and close a plot.
    - Example:
    plt.figure(figsize=(10,6)); sns.histplot({sanitize_name(sheet_names[0])}['SomeColumn']);
    plt.title('Column Distribution');
    plt.savefig('plots/column_dist.png');
    plt.close();
    print("Plot saved to plots/column_dist.png")
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

        

        cleaned_lines = []
        for line in ai_code.splitlines():
            stripped_line = line.strip()
            if stripped_line.startswith("import "):
                print(f"[Info] Removing import line: {stripped_line}")
                continue
            if stripped_line.startswith("```"):
                continue
            if stripped_line.startswith("1️⃣") or stripped_line.startswith("2️⃣") or "DATA/TABLE/NUMBER" in stripped_line or "PLOT/GRAPH" in stripped_line:
                print(f"[Info] Removing preamble line: {stripped_line}")
                continue
            cleaned_lines.append(line)
        ai_code = "\n".join(cleaned_lines).strip()



        dangerous_words = ["os.", "sys", "subprocess", "open(", "exec(", "__"]
        if any(word in ai_code for word in dangerous_words) and "safe_globals['__builtins__']" not in ai_code:
             print(f"🚫 Unsafe word detected in code: {ai_code}")
             raise HTTPException(status_code=403, detail="Unsafe operation detected.")

        print(f"[Debug] Cleaned safe code to execute:\n{ai_code}")

        result_output, is_plot, plot_path = "", False, None


        if "plt." in ai_code or "sns." in ai_code:
            print("[Mode: PLOT] Executing...")
            output_stream = io.StringIO()
            sys.stdout = output_stream
            try:
                exec(ai_code, safe_globals, {})
            finally:
                sys.stdout = sys.__stdout__
            result_output = output_stream.getvalue().strip()

            if "Plot saved to plots/" in result_output:
                is_plot = True
                rel_path = result_output.replace("Plot saved to ", "").strip()
                plot_path = os.path.basename(rel_path)
                print(f"[Debug] Plot file: {plot_path}")
            else:
                is_plot = False
                result_output = "Plotting code executed, but no valid 'Plot saved to...' message was captured."
        else:
            print("[Debug] Mode: DATA] Evaluating...")
            result = eval(ai_code, safe_globals, {})
            if isinstance(result, pd.DataFrame):
                result_output = tabulate(result.head(20), headers="keys", tablefmt="psql")
            elif isinstance(result, pd.Series):
                result_output = tabulate(result.to_frame().head(20), headers="keys", tablefmt="psql")
            else:
                result_output = str(result)

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
    return {"message": "✅ Excel AI Engine API (Smart EDA) running. Go to /docs."}