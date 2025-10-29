
import pandas as pd
import google.generativeai as genai
import os
import re
import numpy as np
import sys
from tabulate import tabulate
import matplotlib.pyplot as plt
import seaborn as sns

if not os.path.exists('plots'):
    os.makedirs('plots')
    print("📁 Created 'plots' directory to save visualizations.")

print("[Debug 1/4] Starting setup...")

try:
    GOOGLE_API_KEY = os.environ['GOOGLE_API_KEY']
    genai.configure(api_key=GOOGLE_API_KEY)
    print("[Debug 1/4] API key found and configured.")

    df = pd.read_excel('data.xlsx', sheet_name='Employees')
    df_projects = pd.read_excel('data.xlsx', sheet_name='Projects')

    df_schema = df.columns.tolist()
    df_projects_schema = df_projects.columns.tolist()

    print("[Debug 1/4] Data files loaded successfully from 'Employees' and 'Projects' sheets.")

except KeyError:
    print("\n❌ FATAL ERROR: GOOGLE_API_KEY not found in environment variables.")
    sys.exit(1)
except FileNotFoundError:
    print("\n❌ FATAL ERROR: 'data.xlsx' not found. Please run 'generate_data.py' first.")
    sys.exit(1)
except Exception as e:
    print(f"\n❌ FATAL ERROR during setup: {e}")
    sys.exit(1)

try:
    model = genai.GenerativeModel('gemini-pro-latest')

    master_prompt = f"""
    You are an expert Python data analyst. You have access to two pandas DataFrames:
    1.  df — The main employee dataset.
    2.  df_projects — Employee project assignments.
    You also have access to plotting libraries: matplotlib.pyplot (as plt) and seaborn (as sns).

    Schemas:
    - df columns: {df_schema}
    - df_projects columns: {df_projects_schema}

    Respond in one of two modes:

    MODE 1: DATA/TABLE/NUMBER
      - For data queries (averages, filters, summaries, etc.)
      - Return a single valid Python expression (no print()).
      - Examples:
        - "show top 5 earners" → df.nlargest(5, 'Salary')
        - "average salary in engineering" → df[df['Department'] == 'Engineering']['Salary'].mean()

    MODE 2: PLOT/GRAPH/VISUALIZATION
      - For visualization queries ("plot", "graph", "distribution", "bar", etc.)
      - Code must:
          1. Create a figure (plt.figure())
          2. Make a plot (sns or plt)
          3. Save it to 'plots/' (plt.savefig('plots/...'))
          4. Close it (plt.close())
          5. Print the saved file path (print("Plot saved to ..."))
      - Example:
        "plot salary distribution" →
        plt.figure(figsize=(10,6)); sns.histplot(df['Salary'], kde=True);
        plt.title('Salary Distribution');
        plt.savefig('plots/salary_dist.png');
        plt.close();
        print("Plot saved to plots/salary_dist.png")

    RULES:
      - Output ONLY the Python code — no markdown, no explanations.
      - ALWAYS save plots in 'plots/'.
      - NEVER use imports, file I/O, or OS/system commands.
    """

    print("[Debug 2/4] Model and advanced master prompt configured successfully.")
    print("---------------------------------------------------------")

except Exception as e:
    print(f"\n❌ FATAL ERROR: Could not initialize model. {e}")
    sys.exit(1)

safe_builtins = {
    "print": print,
    "len": len,
    "round": round,
    "abs": abs,
    "sum": sum,
    "min": min,
    "max": max,
    "str": str,
    "int": int,
    "float": float,
}

safe_globals = {
    "__builtins__": safe_builtins,
    "df": df,
    "df_projects": df_projects,
    "pd": pd,
    "np": np,
    "plt": plt,
    "sns": sns,
}

FORBIDDEN_PATTERNS = r"import|os\.|sys\.|subprocess|open\(|exec\(|__"

def print_help():
    print("\n--- 🤖 Excel AI Analyst Help ---")
    print("I can analyze your Excel data, summarize it, or create visualizations.")
    print("\nExamples:")
    print("  'what is the average salary?'")
    print("  'show me top 5 employees by salary'")
    print("  'plot salary vs performance'")
    print("  'show employees in HR earning above 90000'")
    print("  'bar chart of employees per department'")
    print("\nCommands:")
    print("  'schema' → Show available columns.")
    print("  'help'   → Show this help message.")
    print("  'exit'   → Quit the program.")

def print_schema():
    print("\n--- Data Schema ---")
    print("📄 Employees (df):")
    print(f"   {df_schema}")
    print("\n📄 Projects (df_projects):")
    print(f"   {df_projects_schema}")

print("\n🤖 Welcome to the Excel AI Analyst!")
print("Type 'help' for examples or 'exit' to quit.")

while True:
    try:
        user_query = input("\n[You] ").strip()

        if user_query.lower() == 'exit':
            print("🤖 Goodbye!")
            break
        if user_query.lower() == 'help':
            print_help()
            continue
        if user_query.lower() == 'schema':
            print_schema()
            continue
        if not user_query:
            print("🤖 Please enter a query.")
            continue

        print("[Debug 3/4] Generating AI response...")
        full_prompt = master_prompt + f"\nUser Question: {user_query}"
        response = model.generate_content(full_prompt)
        ai_code = response.text.strip().replace("```python", "").replace("```", "").strip()

        if not ai_code:
            print("🤖 Error: AI returned an empty response. Try again.")
            continue

        if re.search(FORBIDDEN_PATTERNS, ai_code):
            print(f"--- 🚫 SECURITY ALERT ---\nUnsafe code blocked:\n{ai_code}")
            continue

        print(f"[Debug 4/4] AI wants to execute:\n{ai_code}")

        if "plt." in ai_code or "sns." in ai_code:
            print("[Mode: PLOT] Executing visualization code...")
            exec(ai_code, safe_globals, {})

        else:
            print("[Mode: DATA] Evaluating data expression...")
            result = eval(ai_code, safe_globals, {})

            if isinstance(result, pd.DataFrame):
                print(tabulate(result.head(10), headers='keys', tablefmt='psql'))
                print(f"\n🧮 Showing top {min(len(result),10)} of {len(result)} rows.")
            elif isinstance(result, pd.Series):
                print(tabulate(result.to_frame(), headers='keys', tablefmt='psql'))
            else:
                print(result)

    except genai.types.generation_types.StopCandidateException as e:
        print(f"\n--- ERROR (AI Generation) ---\n🤖 AI blocked unsafe content: {e}")
    except (KeyError, ValueError, AttributeError, TypeError, pd.errors.EmptyDataError, IndexError) as e:
        print(f"\n--- ERROR (Data Handling) ---\n🤖 {type(e).__name__}: {e}")
        print("💡 Try rephrasing your question.")
    except Exception as e:
        print(f"\n--- ERROR (Unknown) ---\n🤖 {type(e).__name__}: {e}")
