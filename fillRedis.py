import redis
from pyspark import SparkContext, SparkConf
import pyspark
from pyspark.sql.types import StructType,StructField, StringType, IntegerType, DoubleType
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, concat, lit
from pyspark.sql.types import *
import os

r = redis.Redis(host='localhost', port=6379, db=0)
r.flushall()

def init_spark_context():
    MAX_MEMORY = "5g" #May need to change based on hardware configuration
    conf = SparkConf().setAll([("spark.app.name", "Spark_Processor"), ("spark.redis.port", "6379"), 
                                      ("spark.jars", "spark-redis-branch-2.4/target/spark-redis_2.11-2.5.0-SNAPSHOT-jar-with-dependencies.jar"), 
                                      ("spark.executor.memory", MAX_MEMORY), ("spark.driver.memory", MAX_MEMORY), 
                                      ("spark.memory.fraction", "0.6")])
    sc = SparkContext(conf=conf)
    return sc

sc = init_spark_context()
spark = SparkSession.builder.config(conf = sc.getConf()).getOrCreate()

datasets_path = os.path.join('..','movie_recommendation_system', 'datasets')
complete_ratings_file = os.path.join(datasets_path, 'ml-latest', 'ratings.csv')
movies_file = os.path.join(datasets_path, 'ml-latest', 'movies.csv')

ratingschema = StructType()\
    .add("userId", IntegerType(), True)\
    .add("movieId", IntegerType(), True)\
    .add("rating", DoubleType(), True)\
    .add("timeStamp", IntegerType(), True)

ratingdf = spark.read.format("csv")\
    .option("header",True)\
    .schema(ratingschema)\
    .load(complete_ratings_file)

ratingdf = ratingdf.drop("timestamp")
ratingdf = ratingdf.withColumn("key", (concat(lit("User ID: "),col("userId"),lit(", Movie ID: "),col("movieID"))))
ratingdf = ratingdf.select("key", "userId", "movieId", "rating")
ratColumns = ratingdf.columns

movie = spark.read.option("inferSchema", "true")\
    .option("header", "true").csv(movies_file)

movie.write.format("org.apache.spark.sql.redis").option("table", "movie").option("key.column", "title").save()
print('Movies Added!')
(includedRatings, excluded) = ratingdf.randomSplit([0.1, 0.9])
includedRatings.write.format("org.apache.spark.sql.redis").option("table", "rating").option("key.column", "key").save()
print('Ratings Added!')