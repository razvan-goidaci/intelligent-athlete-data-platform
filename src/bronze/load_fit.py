from pathlib import Path
from datetime import datetime, timezone

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

    session_rows = []
    activity_files_found = 0
    load_time = datetime.now(timezone.utc)

    for fit_file in sorted(FIT_DIR.glob("*.fit")):
        fit_rows = file_to_rows(fit_file, export_sha256="test", loaded_at=load_time)
        
        if "session" in fit_rows:
            session_rows.extend(fit_rows["session"])
            activity_files_found += 1
        if activity_files_found == 5:
            break

    df = spark.createDataFrame(session_rows)

    df.printSchema()
    print(df.count())

    df.write.format("delta").mode("overwrite").save(str(BRONZE_PATH / "session"))

    session_table = spark.read.format("delta").load(str(BRONZE_PATH / "session"))
    print(session_table.count())

    spark.stop()