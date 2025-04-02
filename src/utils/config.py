import json
import os
from pathlib import Path


class ClientConfig:
    def __init__(self):
        # Load base configuration from JSON
        config_path = Path(__file__).parent.parent / "dags" / "dag_config.json"
        with open(config_path, "r", encoding="utf-8") as file:
            self.config = json.load(file)

        # Use environment from config file if available, otherwise use env var
        self.environment = self.config.get("environment", os.getenv("ENVIRONMENT", "dev"))
        self.project_id = os.getenv("BQ_PROJECT_ID", "solutionsdw")

        # Client properties
        self.client_name = self.config["client_name"]
        self.client_display_name = self.config["client_display_name"]
        self.client_id = self.config["client_id"]
        self.project_name = self.config["project_name"]

        # Derived properties
        self.presentation_dataset_name = f"{self.project_name}_presentation"
        self.dashboard_topic_name = os.getenv("DASHBOARD_TOPIC_NAME", "dev-edm-insights-dashboards-topic")

    @property
    def schedule_interval(self):
        return self.config["schedule_interval"]
