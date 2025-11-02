# 📊 Excel AI Engine

A full-stack AI-powered web application that lets you **analyze, update, and visualize Excel data using natural language**.  
Upload one or more `.xlsx` files, ask questions in plain English (for example, *"show average salary by department"*), and the app automatically generates, executes, and displays the correct Python code.
and answer you can even generate pgraphs with it also you can download the result , you ca use joins and all also .

Built with **FastAPI**, **Streamlit**, and **Google Gemini**, this project demonstrates prompt engineering, data processing, and secure code execution in one cohesive system.

---

## ✨ Features

- 🗂️ **Multi-File Upload:** Handle multiple Excel files and sheets at once.  
- ⚙️ **Dynamic Variable Naming:** Automatically assigns names like `data_Employees`, `project_details_Sheet1`.  
- 💬 **Natural Language Analysis:** Query your data conversationally.  
- 🧮 **Data Updates:** Perform in-memory transformations (for example, add new columns).  
- 🔗 **Joins & Aggregations:** Handle complex operations like merges, grouping, and pivots.  
- 📈 **Visualizations:** Auto-generate plots and charts.  
- 📥 **CSV Export:** Download your query results as `.csv`.  
- 🧰 **Secure Execution:** Code runs in a sandboxed environment with restricted imports.

---

## 🏗️ Tech Stack & Architecture

| Layer | Tool / Framework | Purpose |
|-------|------------------|----------|
| **Frontend** | Streamlit | User interface for upload & query |
| **Backend** | FastAPI | Handles requests and executes AI code |
| **AI Model** | Google Gemini Pro | Natural language → Python code |
| **Data Layer** | pandas | Data manipulation and analytics |
| **Deployment** | Docker | Containerized backend |
| **Utilities** | numpy, matplotlib | Data generation and plotting |

---

## 🧠 Core Logic & Design

This project's intelligence lies in **three core design decisions**:  
creating *realistic data challenges*, designing an *AI translator engine*, and crafting *high-precision prompts*.

### 1. Realistic Data Generation (The "Challenge")

Synthetic datasets are intentionally *messy* to reflect real-world complexity:

- **Skewed Salary Data:** Uses `numpy.random.lognormal()` to mimic real salary distributions — many average earners, few high outliers.  
- **Missing Values:** Random `np.nan` in `PerformanceScore` fields tests robustness of `pandas` functions like `dropna()` and `mean()`.  
- **Outliers:** Manually amplified salary and project values simulate data-entry errors, testing the AI's analytical reasoning.

### 2. The AI as a Translator (The "Engine")

Instead of rigid `if/else` logic, the system treats the AI as a **dynamic code generator**:

1. **Dynamic Schema Detection:** When files are uploaded, all sheets and column names are extracted and given contextual variable names.  
2. **Prompt Injection:** These schema details are passed to the AI in the prompt for contextually accurate code generation.  
3. **Sanitized Code Execution:** Returned code is stripped of unsafe imports and executed in a restricted `safe_globals` sandbox.  
4. **Smart Output Handling:**  
   - Finds `result_df`, `result_value`, or plot instructions in the executed scope.  
   - Converts DataFrames to CSV, numerical outputs to JSON, and plots to file paths for frontend display.

### 3. Advanced Prompt Engineering (The "Magic")

The `master_prompt` defines strict behavioral constraints for the AI:

- **Role Definition:** Begins with *"You are an expert Python data analyst."*  
- **Mode-Based Output:** Forces one of three result formats:  
  1. `result_df = ...` → tables/joins  
  2. `result_value = ...` → single numeric answers  
  3. `plt.savefig(...); print(...)` → plots  
- **Few-Shot Examples:** Demonstrates correct syntax for joins, filters, and updates using actual uploaded variable names.  
- **Safety Rules:** Disallows imports, shell commands, and verbose explanations — ensuring clean, executable Python output.

Together, these design elements create a system that behaves like a **true analyst**, not just a chatbot — capable of performing chained transformations, reasoning about data, and producing professional results safely.

---

## 🗂️ File Structure
```
📦 Excel-AI-Engine/
├── backend.py                 # FastAPI server (core logic)
├── frontend.py                # Streamlit web app (UI)
├── generate.py                # Synthetic data generator
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Containerization for deployment
├── test_backend.py            # Optional API tests
├── plots/                     # Saved plot images
├── main.py                    # Local CLI prototype
├── check.py / visualize.py    # Helper utilities
└── data.xlsx, project_details.xlsx  # Generated test data
```

---

## 🚀 How to Run (Locally)

### 1. Setup
```bash
git clone <https://github.com/M-SRIKAR-VARDHAN/petavue_assesment>
cd petavue_assesment
python -m venv venv
```

Activate the environment:

**Windows:**
```bash
.\venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

---

### 2. Set API Key

Set your Google AI API key as an environment variable:

**Windows:**
```bash
set GOOGLE_API_KEY="YOUR_API_KEY_HERE"
```

**macOS/Linux:**
```bash
export GOOGLE_API_KEY="YOUR_API_KEY_HERE"
```

---

### 3. Generate Test Data
```bash
python generate.py
```

This creates sample Excel files: `data.xlsx` and `project_details.xlsx`.

---

### 4. Run the Backend
```bash
uvicorn backend:app --reload
```

Backend will start at: [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

### 5. Run the Frontend

In another terminal:
```bash
streamlit run frontend.py
```

Application will open in your browser at: [http://localhost:8501](http://localhost:8501)

---

## 💡 Using the App

1. Upload your Excel files (for example, `data.xlsx`, `project_details.xlsx`).
2. Ask a question in plain English, such as:
   - `what is the average salary in data_Employees?`
   - `plot a bar chart of employees per department`
   - `add a Bonus column equal to 10% of Salary`
   - `join data_Employees and project_details_Sheet1 on EmployeeID`
3. Click **Analyze**.
4. Download results as `.csv` if a DataFrame output is generated.

---

## 🧩 Example Queries

| Type | Example Query | Output |
|------|---------------|--------|
| **Analysis** | `average salary by department` | Single numeric value |
| **Transformation** | `add Bonus column = 0.1 × Salary` | Updated DataFrame |
| **Join** | `merge employee and project details` | Joined DataFrame |
| **Visualization** | `plot distribution of performance score` | Matplotlib chart |

---

## 🐳 Docker Deployment

### Build the Docker Image
```bash
docker build -t petavue_assesment .
```

### Run the Container
```bash
docker run -p 8000:8000 -e GOOGLE_API_KEY="YOUR_API_KEY_HERE" petavue_assesment
```

The backend API will be available at: [http://localhost:8000](http://localhost:8000)

---

## 🔒 Security Considerations

- Code execution is sandboxed with restricted `safe_globals`.
- Dangerous imports (`os`, `subprocess`, `sys`) are blocked.
- All file operations are scoped to predefined directories.
- User inputs are sanitized before code generation.

---

## 🛠️ Dependencies
```txt
fastapi
uvicorn
streamlit
pandas
openpyxl
numpy
matplotlib
google-generativeai
python-multipart
```

---

## 🧪 Testing
🥲 testing is not complete i dont know how to write if anyone can do contribute 
Run backend tests:
```bash
pytest test_backend.py
```

---

## 📚 API Endpoints

### `POST /upload`

Upload Excel files and get variable assignments.

**Request:** `multipart/form-data` with Excel files  
**Response:** JSON with variable names and sheet structures

### `POST /query`

Execute natural language queries on uploaded data.

**Request:**
```json
{
  "query": "average salary by department",
  "uploaded_variables": {...}
}
```

**Response:**
```json
{
  "result": "data or path",
  "result_type": "dataframe|value|plot",
  "code_executed": "generated Python code"
}
```

---

## 🎯 Use Cases

- **Business Analytics:** Quick insights from sales, HR, or financial data.
- **Data Science Education:** Learn pandas through natural language interaction.
- **Rapid Prototyping:** Test data transformations without writing code.
- **Non-Technical Users:** Empower analysts without Python knowledge.

---

## 🔮 Future Enhancements

- [ ] Support for CSV and JSON file formats
- [ ] Multi-step query chaining with conversation memory
- [ ] User authentication and session management
- [ ] Real-time collaborative data analysis
- [ ] Integration with cloud storage (AWS S3, Google Drive)
- [ ] Advanced visualization options for now (Plotly, Seaborn) instead colorfull dashboards
- [ ] Query history and result caching
- [ ] Natural language data correction suggestions

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is open-source under the **MIT License**.  
You may modify and adapt it for educational or research purposes.

---

## 🙏 Acknowledgments

- **Google Gemini API** for powerful natural language understanding
- **Streamlit** for rapid UI development
- **FastAPI** for modern async Python web framework
- The open-source community for amazing tools and libraries

---

## 👨‍💻 Author

Developed with ❤️ by **Sky Father** — a computer science engineer passionate about building AI systems that bridge **language and logic**.

---

## 📞 Contact & Support

- **Issues:** [GitHub Issues](https://github.com/M-SRIKAR-VARDHAN/petavue_assesment/issues)
- **Discussions:** [GitHub Discussions](https://github.com/M-SRIKAR-VARDHAN/petavue_assesment/discussions)
- **Email:** your.email@example.com

---

## ⭐ Star History

If you find this project useful, please consider giving it a star on GitHub!
[![Star History Chart](https://api.star-history.com/svg?repos=M-SRIKAR-VARDHAN/petavue_assesment&type=Date)](https://star-history.com/#M-SRIKAR-VARDHAN/petavue_assesment&Date)


---

**Made with 🔥 and ☕ | © 2025 BY Primal Sage(M.Srikar Vardhan)**
