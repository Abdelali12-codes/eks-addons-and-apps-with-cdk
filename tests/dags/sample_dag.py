from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime


# Define a Python function to be executed by PythonOperator
def my_python_task(**kwargs):
    print("Hello from PythonOperator!")
    return "Task completed."


# Default DAG arguments
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 1,
}

# Define the DAG
with DAG(
    dag_id='sample_python_operator_dag',
    default_args=default_args,
    description='A simple DAG with PythonOperator',
    schedule_interval='@daily',
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['example'],
) as dag:

    # Task using PythonOperator
    python_task = PythonOperator(
        task_id='run_python_function',
        python_callable=my_python_task,
        provide_context=True,  # to access **kwargs if needed
    )

    python_task
