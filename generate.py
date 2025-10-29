import pandas as pd
from faker import Faker
import random
import datetime
import numpy as np
import os


SEED = 42
Faker.seed(SEED)
np.random.seed(SEED)
random.seed(SEED)

fake = Faker()
departments = ['Engineering', 'Sales', 'Marketing', 'HR', 'Finance']
NUM_ROWS = 1000
data = []
employee_ids = []


feedback_samples = [
    "Excellent performance, a real team player.",
    "Needs to improve on deadlines.",
    "Struggling with the new software, needs training.",
    "Very positive attitude, great with clients.",
    "Consistently meets expectations.",
    "Poor communication skills.",
    "A rising star, marked for promotion.",
    "Often late, attendance is an issue.",
    "Fantastic problem solver."
]

print(f"Generating {NUM_ROWS} rows of realistic data (Seed={SEED})...")


mean_salary = np.log(75000)
sigma = 0.5
salaries = np.random.lognormal(mean_salary, sigma, NUM_ROWS)


for i in range(NUM_ROWS):
    employee_id = f"E{1000 + i}"
    employee_ids.append(employee_id)
    join_date = fake.date_between(start_date='-5y', end_date='today')
    
    record = {
        'EmployeeID': employee_id,
        'Name': fake.name(),
        'Email': fake.email(),
        'JobTitle': fake.job(),
        'Department': random.choice(departments),
        'Age': random.randint(22, 65),
        'Salary': round(salaries[i], 2),
        'JoinDate': join_date,
        'City': fake.city(),
        'PerformanceScore': round(random.uniform(1.0, 5.0), 1),
        'OnLeave': random.choice([True, False]),
        'Projects': random.randint(1, 5),
        'LastFeedback': random.choice(feedback_samples)
    }
    data.append(record)

df_main = pd.DataFrame(data)

for _ in range(int(NUM_ROWS * 0.05)):
    row_index = random.randint(0, NUM_ROWS - 1)
    df_main.loc[row_index, 'PerformanceScore'] = np.nan

for _ in range(10):
    row_index = random.randint(0, NUM_ROWS - 1)
    if random.choice([True, False]):
        df_main.loc[row_index, 'Projects'] = random.randint(20, 30)
    else:
        df_main.loc[row_index, 'Salary'] = df_main.loc[row_index, 'Salary'] * 3.5

project_data = []
project_names = ['Alpha Launch', 'Beta Test', 'Project Phoenix', 'Data Migration', 'Security Audit']
project_managers = ['Alice Chen', 'Bob Smith', 'Charlie Lee']

for emp_id in random.sample(employee_ids, int(NUM_ROWS * 0.8)):
    project_record = {
        'EmployeeID': emp_id,
        'ProjectName': random.choice(project_names),
        'ProjectManager': random.choice(project_managers)
    }
    project_data.append(project_record)

df_projects = pd.DataFrame(project_data)


output_file = 'data.xlsx'
with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    df_main.to_excel(writer, sheet_name='Employees', index=False)
    df_projects.to_excel(writer, sheet_name='Projects', index=False)

print(f"\nSuccessfully created '{output_file}' with two sheets:")
print(f"  - 'Employees' sheet ({len(df_main)} rows)")
print(f"  - 'Projects' sheet ({len(df_projects)} rows)")