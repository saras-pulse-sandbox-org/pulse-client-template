import sys
from datetime import datetime
from pathlib import Path

from airflow.decorators import dag, task
from airflow.operators.python import get_current_context

sys.path.insert(0, str(Path(__file__).parent.parent.absolute()))
from utils.config import ClientConfig
from utils.helpers import publish_dashboard_tables, run_dbt_command

# Load client configuration
config = ClientConfig()

# Configuration using client info
BASE_DIR = Path(__file__).parent.parent
DBT_DIR = BASE_DIR / "dbt"  # Point to the dbt subdirectory


@dag(
    dag_id=config.project_name,
    description=f"dbt DAG for {config.client_display_name}",
    schedule_interval=config.schedule_interval,
    start_date=datetime(2025, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=["pulse", config.client_display_name, config.client_id],
    default_args={"owner": config.client_display_name},
)
def dbt_dag():
    """dbt DAG for client"""

    @task
    def dbt_run():
        """Run dbt models"""
        context = get_current_context()
        dag_run_conf = context["dag_run"].conf or {}

        # Get task-specific config
        task_config = dag_run_conf.get("dbt_run", {})

        success = run_dbt_command(
            command="run",
            project_dir=DBT_DIR,
            profiles_dir=DBT_DIR,
            target=config.environment,
            **task_config,  # Pass all task-specific configs
        )

        if not success:
            raise Exception("dbt run failed")
        return "dbt run completed successfully"

    @task
    def dbt_test():
        """Test dbt models"""
        context = get_current_context()
        dag_run_conf = context["dag_run"].conf or {}

        # Get task-specific config
        task_config = dag_run_conf.get("dbt_test", {})

        success = run_dbt_command(
            command="test",
            project_dir=DBT_DIR,
            profiles_dir=DBT_DIR,
            target=config.environment,
            **task_config,  # Pass all task-specific configs
        )

        if not success:
            raise Exception("dbt test failed")
        return "dbt test completed successfully"

    @task
    def publish_tables():
        """Publish tables to dashboard service"""
        context = get_current_context()
        run_id = context["run_id"]

        published_tables = publish_dashboard_tables(run_id)
        print(f"Published {len(published_tables)} tables")
        return published_tables

    # Define task dependencies
    dbt_run_task = dbt_run()
    dbt_test_task = dbt_test()
    publish_tables_task = publish_tables()

    dbt_run_task >> [dbt_test_task, publish_tables_task]


# Instantiate DAG
dag_instance = dbt_dag()
