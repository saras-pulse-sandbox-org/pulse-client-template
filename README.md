# Pulse Client Template

## Overview
This repository contains the infrastructure setup for running Apache Airflow in a Google Cloud Platform (GCP) Compute Engine VM. It uses Docker Compose for container orchestration and GitHub Actions workflows for automated deployment.

## Infrastructure Components

### Airflow Setup
The Airflow infrastructure includes the following services:
- Airflow Webserver: Web UI for Airflow management
- Airflow Scheduler: Manages DAG scheduling
- Airflow Worker: Executes the tasks
- Airflow DAG Processor: Processes DAG files
- Postgres: Database for Airflow metadata
- Redis: Message broker for Celery executor

### Docker Compose Configuration
The `docker-compose.yml` file defines all necessary services to run Airflow in a containerized environment. It uses the Pulse Airflow image from Google Artifact Registry and sets up appropriate environment variables, volumes, and dependencies.

Key features:
- Celery executor configuration
- Health checks for all services
- Volume mounts for persistent storage
- Environment variable customization

## Setup Instructions

1. Clone this repository
2. Set up the required environment variables:
   - `AIRFLOW_UID`: User ID for Airflow services
   - `GHUB_PAT`: GitHub Personal Access Token
   - `BQ_PROJECT_ID`: BigQuery project ID
   - `AIRFLOW_PROJ_DIR`: (Optional) Directory for Airflow project

3. Place your GCP service account key file as `keyfile.json` in the project root

## Deployment

This infrastructure is designed to be deployed to a GCP Compute Engine VM. GitHub Actions workflows automate the deployment process, including:
- Building and pushing Docker images
- Provisioning GCP resources
- Deploying the Airflow stack
- Configuring necessary permissions

*Note: GitHub Actions workflows will be added to this repository to handle automated deployments.*

## Accessing Airflow

Once deployed, Airflow can be accessed at port 8080 of your VM instance. Default credentials are:
- Username: airflow
- Password: airflow

For production deployments, ensure you change these default credentials.
