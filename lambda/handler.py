import json
import os

import boto3

athena = boto3.client("athena")
DATABASE = os.environ["ATHENA_DB"]
OUTPUT = os.environ["ATHENA_OUTPUT"]


def run_query(query):
    resp = athena.start_query_execution(
        QueryString=query,
        QueryExecutionContext={"Database": DATABASE},
        ResultConfiguration={"OutputLocation": OUTPUT},
    )
    exec_id = resp["QueryExecutionId"]
    while True:
        status = athena.get_query_execution(QueryExecutionId=exec_id)["QueryExecution"][
            "Status"
        ]["State"]
        if status in ("SUCCEEDED", "FAILED", "CANCELLED"):
            break
    if status != "SUCCEEDED":
        raise Exception(f"Athena query status: {status}")
    result = athena.get_query_results(QueryExecutionId=exec_id)
    cols = [c["Label"] for c in result["ResultSet"]["ResultSetMetadata"]["ColumnInfo"]]
    rows = result["ResultSet"]["Rows"][1:]
    data = [
        {cols[i]: field.get("VarCharValue") for i, field in enumerate(r["Data"])}
        for r in rows
    ]
    return data


def lambda_handler(event, context):
    path = event.get("pathParameters") or {}
    resource = event.get("resource")
    if resource == "/orders/{client_id}":
        q = f"SELECT * FROM orders_parquet WHERE client_id = {path['client_id']}"
    elif resource == "/sales/{product_id}":
        q = f"SELECT product_id, SUM(total_cost) AS total_sales FROM orders_parquet WHERE product_id = {path['product_id']} GROUP BY product_id"
    elif resource == "/status/{status}":
        q = f"SELECT * FROM orders_parquet WHERE status = '{path['status']}'"
    else:
        return {"statusCode": 404, "body": json.dumps({"error": "Not found"})}

    try:
        result = run_query(q)
        return {"statusCode": 200, "body": json.dumps(result)}
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
