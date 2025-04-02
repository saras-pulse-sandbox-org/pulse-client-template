"""SQL queries used by the Pulse client template"""

# Query to get successful tables from a dbt run
SUCCESSFUL_TABLES_QUERY = """
SELECT DISTINCT name
FROM `{project_id}.pulse_metadata.dbt_results`
WHERE
  schema_name LIKE '%{client_id}%presentation'
  AND airflow_run_id = '{run_id}'
  AND status = 'success'
QUALIFY
  RANK() OVER(PARTITION BY airflow_run_id, invocation_id ORDER BY record_created_at DESC) = 1
"""

# Query to get available dashboard tables for a client
AVAILABLE_TABLES_QUERY = """
WITH client_sources AS (
  SELECT platform
  FROM `{project_id}.pulse_metadata.client_platforms`,
       UNNEST(platforms) AS platform
  WHERE client_id = '{client_id}'
),
dashboard_tables AS (
  SELECT DISTINCT
    TRIM(dataset_name) AS dataset_name
  FROM `{project_id}.pulse_metadata.{dashboard_table}`,
       UNNEST(COALESCE(mandatory_src, [])) AS src,
       UNNEST(COALESCE(dataset_names, [])) AS dataset_name
  WHERE src IN (SELECT platform FROM client_sources)
  
  UNION ALL
  
  SELECT DISTINCT
    TRIM(dataset_name) AS dataset_name
  FROM `{project_id}.pulse_metadata.{dashboard_table}`,
       UNNEST(COALESCE(optional_src, [])) AS src,
       UNNEST(COALESCE(dataset_names, [])) AS dataset_name
  WHERE src IN (SELECT platform FROM client_sources)
)
SELECT dataset_name AS name
FROM dashboard_tables
"""
