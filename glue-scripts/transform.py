# glue-scripts/transform.py

import logging
import sys

from awsglue.context import GlueContext
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    DoubleType,
    IntegerType,
    StringType,
    StructField,
    StructType,
)

# -------------------------------------------------------
# Conf login
# -------------------------------------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


# -------------------------------------------------------
# def esquema
# -------------------------------------------------------
def get_schema() -> StructType:
    return StructType(
        [
            StructField("client_id", IntegerType(), nullable=False),
            StructField("client_name", StringType(), nullable=True),
            StructField("order_id", IntegerType(), nullable=False),
            StructField("product_id", IntegerType(), nullable=False),
            StructField("product_description", StringType(), nullable=True),
            StructField("product_price", DoubleType(), nullable=False),
            StructField("product_ccf", IntegerType(), nullable=False),
            StructField("product_volume", DoubleType(), nullable=False),
            StructField("point_of_sale_channel", StringType(), nullable=True),
            StructField("status", StringType(), nullable=True),
        ]
    )


# -------------------------------------------------------
# read_input - Lee archivo csv
# -------------------------------------------------------
def read_input(spark: SparkSession, path: str, schema: StructType) -> DataFrame:
    logger.info(f"Reading input data from {path}")
    return spark.read.option("header", "true").schema(schema).csv(path)


# -------------------------------------------------------
# transform_data - realiza las transformaciones
# -------------------------------------------------------
def transform_data(df: DataFrame) -> DataFrame:
    logger.info(
        "Applying transformations: total_cost, unit_price_per_liter, filter broken"
    )
    # Evitar división por cero
    df = df.filter(F.col("product_volume") > 0)

    return (
        df.withColumn("total_cost", F.col("product_price") * F.col("product_ccf"))
        .withColumn(
            "unit_price_per_liter", F.col("product_price") / F.col("product_volume")
        )
        .filter(F.col("status") != "broken")
    )


# -------------------------------------------------------
# Fwrite_output - Funcion de escritura
# -------------------------------------------------------
def write_output(df: DataFrame, path: str):
    logger.info(f"Writing output data to {path} (partitioned by status)")
    (df.write.mode("overwrite").partitionBy("status").parquet(path))


# -------------------------------------------------------
# Orquestador
# -------------------------------------------------------
def main():
    try:
        args = getResolvedOptions(sys.argv, ["INPUT", "OUTPUT"])
        input_path = args["INPUT"]
        output_path = args["OUTPUT"]

        sc = SparkContext()
        glue = GlueContext(sc)
        spark = glue.spark_session

        schema = get_schema()
        df = read_input(spark, input_path, schema)

        df_transformed = transform_data(df)

        write_output(df_transformed, output_path)

        logger.info("Job completed successfully")

    except Exception:
        logger.error("Job failed with exception", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
