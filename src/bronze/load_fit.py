from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict

from delta import configure_spark_with_delta_pip
from pyspark.sql import SparkSession

from fit_to_rows import file_to_rows

FIT_DIR = Path("data/raw/fit")
BRONZE_PATH = Path("data/bronze")

def create_spark():
    """Start a local Spark session with Delta Lake enabled."""
    builder = (
        SparkSession.builder
        .appName("bronze_fit")
        .master("local[*]")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
    )
    spark = configure_spark_with_delta_pip(builder).getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")
    return spark


if __name__ == "__main__":

    spark = create_spark()

    rows_by_table = defaultdict(list)
    load_time = datetime.now(timezone.utc)

    for fit_file in sorted(FIT_DIR.glob("*.fit"))[::50]:
        fit_rows = file_to_rows(fit_file, export_sha256="test", loaded_at=load_time)
        
        for table_name, table_rows in fit_rows.items():
            rows_by_table[table_name].extend(table_rows)

    for table_name in rows_by_table:
        df = spark.createDataFrame(rows_by_table[table_name])

        print(table_name)
        df.printSchema()
        print(df.count())

        df.write.format("delta").mode("overwrite").save(str(BRONZE_PATH / table_name))

        file_table = spark.read.format("delta").load(str(BRONZE_PATH / table_name))
        print(file_table.count())

    spark.stop()