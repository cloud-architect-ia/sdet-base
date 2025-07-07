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
# 1) Logging
# -------------------------------------------------------
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
)
logger = logging.getLogger(__name__)

# -------------------------------------------------------
# 2) Esquema con tipos estrictos
# -------------------------------------------------------
def get_schema() -> StructType:
    return StructType([
        StructField("client_id", IntegerType(), nullable=False),
        StructField("client_name", StringType(), nullable=False),
        StructField("order_id", IntegerType(), nullable=False),
        StructField("product_id", IntegerType(), nullable=False),
        StructField("product_description", StringType(), nullable=False),
        StructField("product_price", DoubleType(), nullable=False),
        StructField("product_ccf", IntegerType(), nullable=False),
        StructField("product_volume", DoubleType(), nullable=False),
        StructField("point_of_sale_channel", StringType(), nullable=False),
        StructField("status", StringType(), nullable=False),
    ])

VALID_CHANNELS = F.array(
    F.lit("Retail"), F.lit("Online"), F.lit("B2B")
)
VALID_STATUSES = F.array(
    F.lit("created"), F.lit("delivered"), F.lit("broken")
)

# -------------------------------------------------------
# 3) Leer CSV y validar esquema
# -------------------------------------------------------
def read_input(spark: SparkSession, path: str, schema: StructType) -> DataFrame:
    logger.info(f" Leyendo datos de entrada desde {path}")
    df = (
        spark.read
             .option("header", "true")
             .schema(schema)
             .csv(path)
    )

    total = df.count()
    non_null = df.dropna().count()
    logger.info(f"   → Filas totales: {total}, sin nulls: {non_null}")
    return df

# -------------------------------------------------------
# 4) Transformaciones con validaciones
# -------------------------------------------------------
def transform_data(df: DataFrame) -> DataFrame:
    logger.info(" Aplicando transformaciones y validaciones")

    df = df.dropna(
        subset=[
            "client_id", "order_id", "product_id",
            "product_price", "product_ccf", "product_volume",
            "point_of_sale_channel", "status"
        ]
    )

    df = df.filter(F.col("product_volume") > 0)

    df = df.filter(F.col("product_price") >= 0)

    df = df.filter(F.array_contains(VALID_CHANNELS, F.col("point_of_sale_channel")))
    df = df.filter(F.array_contains(VALID_STATUSES, F.col("status")))

    df = (
        df
        .withColumn("total_cost", F.col("product_price") * F.col("product_ccf"))
        .withColumn(
            "unit_price_per_liter",
            F.col("product_price") / F.col("product_volume")
        )
    )

    # 4.6 Filtrar filas “broken” por negocio
    df = df.filter(F.col("status") != "broken")

    # Log de filas finales
    logger.info(f"   → Filas después de transform: {df.count()}")
    return df

# -------------------------------------------------------
# 5) Escribir parquet particionado
# -------------------------------------------------------
def write_output(df: DataFrame, path: str):
    logger.info(f" Escribiendo resultado a {path} particionado por status")
    (
        df.write
          .mode("overwrite")
          .partitionBy("status")
          .parquet(path)
    )

# -------------------------------------------------------
# 6) Orquestación principal
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
        df_raw = read_input(spark, input_path, schema)

        df_transformed = transform_data(df_raw)
        write_output(df_transformed, output_path)

        logger.info("Job completado con éxito")
    except Exception:
        logger.exception(" Job falló con excepción")
        sys.exit(1)

if __name__ == "__main__":
    main()
