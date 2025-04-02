import json
import subprocess
from pathlib import Path

import yaml
from google.cloud import bigquery, pubsub_v1
from google.oauth2 import service_account

from utils.config import ClientConfig
from utils.queries import AVAILABLE_TABLES_QUERY, SUCCESSFUL_TABLES_QUERY


def execute_command(cmd):
    """
    Execute a shell command and stream output to logs

    Args:
        cmd: Command to execute (list of strings)

    Returns:
        Tuple of (success, output_lines)
    """
    # Print command for logging
    print(f"Executing: {' '.join(cmd)}")

    # Run command and stream output
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,  # Line buffered for real-time output
    )

    # Stream output to logs
    output_lines = []
    for line in iter(process.stdout.readline, ""):
        print(line, end="")
        output_lines.append(line.rstrip())

    # Wait for process to complete
    process.wait()

    # Return success/failure and output
    return process.returncode == 0, output_lines


def run_dbt_command(command, project_dir=None, profiles_dir=None, target="dev", **kwargs):
    """
    Execute a dbt command with support for all CLI options

    Args:
        command: dbt command to run (e.g., 'run', 'test')
        project_dir: dbt project directory (Path or string)
        profiles_dir: dbt profiles directory (Path or string)
        target: dbt target environment
        **kwargs: Additional dbt arguments:
            - select: Models to include
            - exclude: Models to exclude
            - full_refresh: Whether to run with --full-refresh
            - vars: Dict of variables to pass to dbt

    Returns:
        True if command succeeded, False otherwise
    """
    # Default directories
    project_dir = Path(__file__).parent.parent if not project_dir else Path(project_dir)
    profiles_dir = project_dir if not profiles_dir else Path(profiles_dir)

    # Common command arguments
    base_args = [
        "--no-use-colors",
        "--profiles-dir",
        str(profiles_dir),
        "--project-dir",
        str(project_dir),
        "--target",
        target,
    ]

    # Process additional arguments
    if kwargs.get("select"):
        base_args.extend(["--select", kwargs["select"]])

    if kwargs.get("exclude"):
        base_args.extend(["--exclude", kwargs["exclude"]])

    if kwargs.get("full_refresh") == True:
        base_args.append("--full-refresh")

    if kwargs.get("vars"):
        base_args.extend(["--vars", json.dumps(kwargs["vars"])])

    # Run dbt deps first (unless the command is already deps)
    if command != "deps":
        print("Installing dbt dependencies...")
        deps_cmd = ["dbt", "deps"] + base_args
        success, _ = execute_command(deps_cmd)

        if not success:
            print("Failed to install dbt dependencies")
            return False

    # Run the requested command
    cmd = ["dbt", command] + base_args
    success, _ = execute_command(cmd)

    return success


def publish_dashboard_tables(run_id, credentials_path=None):
    """
    Publish successful dbt tables to the dashboard service via Pub/Sub

    Args:
        run_id: Airflow run ID used to identify the dbt run
        credentials_path: Path to the GCP service account credentials file

    Returns:
        List of published table names
    """
    config = ClientConfig()

    # Set default credentials path if not provided
    if not credentials_path:
        credentials_path = Path(__file__).parent.parent.parent / "keyfile.json"  # main dags folder

    try:
        # Load credentials and create clients
        credentials = service_account.Credentials.from_service_account_file(credentials_path)
        bq_client = bigquery.Client(credentials=credentials, project=credentials.project_id)
        pubsub_client = pubsub_v1.PublisherClient(credentials=credentials)

        # Get version and margin from dbt project
        project_path = Path(__file__).parent.parent / "dbt" / "dbt_project.yml"
        with open(project_path, "r") as f:
            dbt_config = yaml.safe_load(f)

        version = dbt_config.get("vars", {}).get("version", "1.0.0")
        cogs_margin = dbt_config.get("vars", {}).get("cogsMargin", 15.0)

        # Set topic based on version
        topic_name = config.dashboard_topic_name
        dashboard_table = "dashboard_service_config_v1" if version == "1.0.0" else "dashboard_service_config_v2"

        # Format and execute queries
        successful_query = SUCCESSFUL_TABLES_QUERY.format(
            project_id=config.project_id,
            client_id=config.client_id,
            run_id=run_id,
        )
        print(f"Executing query to get successful tables: {successful_query}")

        available_query = AVAILABLE_TABLES_QUERY.format(
            project_id=config.project_id,
            client_id=config.client_id,
            dashboard_table=dashboard_table,
        )
        print(f"Executing query to get available tables: {available_query}")

        # Execute queries
        successful_tables = [row.name for row in bq_client.query(successful_query).result()]
        available_tables = [row.name for row in bq_client.query(available_query).result()]
        print(f"Found {len(successful_tables)} successful tables")
        print(f"Found {len(available_tables)} available tables")

        # Find intersection
        tables_to_publish = list(set(successful_tables) & set(available_tables))
        print(f"Found {len(tables_to_publish)} tables to publish")

        # Publish message
        if tables_to_publish:
            message = {
                "client_id": config.client_id,
                "client_name": config.client_name,
                "project_id": config.project_id,
                "dataset_name": config.presentation_dataset_name,
                "table_names": tables_to_publish,
                "version": version,
                "cogsMargin": cogs_margin,
            }

            topic_path = pubsub_client.topic_path(config.project_id, topic_name)
            message_data = json.dumps(message).encode("utf-8")

            print(f"Publishing {len(tables_to_publish)} tables to Pub/Sub")
            future = pubsub_client.publish(topic_path, message_data)
            future.result()
            print(f"Successfully published tables to {topic_name}")

        return tables_to_publish

    except Exception as e:
        print(f"Error publishing dashboard tables: {e}")
        raise
