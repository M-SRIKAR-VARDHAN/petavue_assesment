import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# --- Setup ---
excel_file = 'data.xlsx' # Make sure it's pointed at the main file
output_dir = 'plots'

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# --- Load Data ---
try:
    df = pd.read_excel(excel_file)
    print(f"Loading '{excel_file}' for analysis...")
except FileNotFoundError:
    print(f"Error: '{excel_file}' not found.")
    print("Please run the 'generate_data.py' script first.")
    exit()

# --- 1. Plot for Skew (Salary) ---
print("Generating plot 1: Salary Distribution (to check for skew)...")
plt.figure(figsize=(10, 6))
sns.histplot(df['Salary'], kde=True, bins=50)
plt.title('Salary Distribution (Should be skewed to the right)')
plot1_path = os.path.join(output_dir, '1_salary_distribution.png')
plt.savefig(plot1_path)
plt.close()

# --- 2. Plot for Outliers (Projects) ---
print("Generating plot 2: Project Count (to check for outliers)...")
plt.figure(figsize=(10, 6))
sns.boxplot(x=df['Projects'])
plt.title('Box Plot of Project Counts (Should show outlier dots)')
plot2_path = os.path.join(output_dir, '2_projects_outliers.png')
plt.savefig(plot2_path)
plt.close()

# --- 3. Plot for Missing Data (PerformanceScore) ---
missing_count = df['PerformanceScore'].isnull().sum()
print(f"Generating plot 3: Missing Performance Scores ({missing_count} found)...")
plt.figure(figsize=(8, 5))
status = df['PerformanceScore'].isnull().map({False: 'Present', True: 'Missing (NaN)'})
sns.countplot(x=status, order=['Present', 'Missing (NaN)'])
plt.title('Missing vs. Present Performance Scores')
plot3_path = os.path.join(output_dir, '3_performancescore_missing.png')
plt.savefig(plot3_path)
plt.close()

print(f"\nAnalysis complete. Check the '{output_dir}' folder.")