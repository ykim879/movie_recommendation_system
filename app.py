from flask import Flask, render_template
from flask import request

import os
import redis
import json
import pandas
from pyspark import SparkContext, SparkConf
import pyspark
from pyspark.sql.types import StructType,StructField, StringType, IntegerType, DoubleType
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, concat, lit, row_number
from pyspark.sql.functions import udf
from pyspark.sql.types import *
from engine import RecommendationEngine
from pyspark.sql.window import Window

app = Flask(__name__)
r = redis.Redis(host='localhost', port=6379, db=0)
sc = 0
userId = 0
movieId = 0
moviedf = 0
ratingdf = 0
ratColumns = 0
newColumns = 0
recEng = 0

@app.route('/')
def hello():
    return render_template('index.html')

@app.route('/search', methods = ['POST'])
def search_values():
    value = request.form["movie"]
    global userId
    userId = request.form["userId"]
    exp = "movie:*"
    for val in value:
        exp += "[" + str(val.lower()) + str(val.upper()) + "]"
    exp += '*'
    keys = r.keys(pattern=exp)
    a = []
    for key in keys:
        newStr = key.decode('utf-8')
        movieId = r.hgetall(newStr)[b'movieId'].decode("utf-8")
        genres = r.hgetall(newStr)[b'genres'].decode("utf-8")
        val = str(key.decode('utf-8')[6:])
        #print(val)
        title = val[:-7]
        date = val[-5:-1]
        a.append((movieId, title, date, genres))
        
    return render_template("searched.html", keys=a)

@app.route('/recommendations', methods=['POST'])
def findPastRecommendation():
    key = 'rating:User ID: ' + str(userId) +  ', Movie ID: ' +  request.form['choice']
    global movieId
    movieId = request.form['choice']
    #key = 'rating:User ID: ' + str(userId) + ', Movie ID: ' + str(choice)
    a = r.hgetall(key)
    if not a:
        a = {}
        a["movieId"] = request.form['choice']
        a["userId"] = str(userId)
        a["rating"] = 'Not Yet Rated'
    else:
        a = {str(key.decode('utf-8')): str(value.decode('utf-8')) for key, value in a.items()}
    return render_template("recommend.html", keys=a)

@app.route('/add_rating', methods=['POST'])
def add_rating():
    key = 'rating:User ID: ' + str(userId) +  ', Movie ID: ' +  str(movieId)
    #print(request.form['newRating'])
    newRating = {}
    newRating["movieId"] = movieId
    newRating["userId"] = userId
    newRating["rating"] = round(float(request.form["newRating"]), 1)
    r.hset(key, key='movieId', value=newRating['movieId'])
    r.hset(key, key='userId', value=newRating['userId'])
    r.hset(key, key='rating', value=newRating['rating'])
    global ratingdf
    global ratColumns
    newRow = spark.createDataFrame([(key[7:], int(newRating["userId"]), int(newRating["movieId"]), float(newRating["rating"]))], ratColumns)
    global newColumns
    newColumns = newColumns.union(newRow)
    printBatch()
    check = r.hgetall(key)
    if not check:
        return 'Didnt Work'
    else:
        a = {str(key.decode('utf-8')) : str(value.decode('utf-8')) for key, value in check.items()}
        return render_template("update_check.html", keys=a)
    return 0

@app.route('/update_rating', methods=['POST'])
def update_rating():
    chkKey = 'rating:User ID: ' + str(userId) +  ', Movie ID: ' +  str(movieId)
    print(request.form['newRating'])
    r.hset(chkKey, key='rating', value=request.form['newRating'])
    global ratingdf
    global ratColumns
    newRow = spark.createDataFrame([(chkKey[7:], int(userId), int(movieId), round(float(request.form["newRating"]), 1))], ratColumns)
    global newColumns
    newColumns = newColumns.union(newRow)
    printBatch()
    check = r.hgetall(chkKey)
    if not check:
        return 'Didnt Work'
    else:
        a = {str(key.decode('utf-8')) : str(value.decode('utf-8')) for key, value in check.items()}
        return render_template("update_check.html", keys=a)
    return 0
    
@app.route('/batch', methods=['POST'])
def processBatch():
    global ratingdf
    global newColumns
    global moviedf
    global recEng
    global sc
    '''
    movieIds = list(newColumns.select(col('movieId')).toPandas()['movieId'])
    movieNames = list(moviedf.filter(moviedf.movieId.isin(movieIds)).toPandas()['title'])
    print(movieIds)
    print(movieNames)
    userIds = list(newColumns.select(col('userId')).toPandas()['userId'])
    print(userIds)
    a = []
    for i in range(len(userIds)):
        a.append((userIds[i], movieIds[i], movieNames[i]))
    '''
    mergedDf = ratingdf.unionAll(newColumns)
    mergedDf = mergedDf.withColumn("_row_number", row_number().over(Window.partitionBy(mergedDf['key']).orderBy('key')))
    counts = mergedDf.groupBy('key').count().selectExpr('key as newKey', 'count as count')
    full_outer_join = mergedDf.join(counts, mergedDf.key == counts.newKey ,how='inner').select(col('key'), col('userId'), col('movieId'), col('rating'), col('_row_number'), col('count'))
    fixedDf = full_outer_join.filter('count == 1').unionAll(full_outer_join.filter((full_outer_join['count'] > 1) & (full_outer_join['_row_number'] > 1)))
    ratingdf = fixedDf.select(col('key'), col('userId'), col('movieId'), col('rating'))
    recEng = RecommendationEngine(sc, moviedf, ratingdf)
    newColumns = spark.createDataFrame([], ratingdf.schema)
    return render_template("batch.html")

@app.route('/find_recommendations', methods=['POST'])
def find_recommendations():
    movies = recEng.recommendForUser(request.form['recUserId'])
    print(movies)
    recMovieList = moviedf.filter(col('movieId').isin(movies)).collect()
    #print(recMovieList)
    a = []
    keys = [row['title'] for row in recMovieList]
    print(keys)
    for key in keys:
        movieId = str(r.hgetall('movie:' + key)[b'movieId'].decode("utf-8"))
        genres = str(r.hgetall('movie:' + key)[b'genres'].decode("utf-8"))
        title = key[:-7]
        date = key[-5:-1]
        a.append((movieId, title, date, genres))

    return render_template("recs.html", keys=a)

@app.route('/user_history', methods=['POST'])
def user_history():
    vals = r.keys("rating:User ID: " + str(request.form['recUserId']) + ", *")
    movies = []
    ratingVals = []
    for st in vals:
        numbers = [int(word) for word in st.split() if word.isdigit()]
        ratingVal = str(r.hgetall(st)[b'rating'].decode("utf-8"))
        movies.append(numbers[0])
        ratingVals.append(ratingVal)

    movieNames = moviedf.filter(moviedf.movieId.isin(movies)).select(col('title'))
    movieNames = [row['title'] for row in movieNames.collect()]
    history = []
    a = []
    a.append(str(request.form['recUserId']))
    for i in range(len(movieNames)):
        key = movieNames[i]
        title = key[:-7]
        date = key[-5:-1]
        genres = str(r.hgetall('movie:' + key)[b'genres'].decode("utf-8"))
        history.append((movies[i], title, date, genres, ratingVals[i]))
    
    a.append(history)
    return render_template("user_history.html", keys=a)

def init_spark_context():
    MAX_MEMORY = "5g"
    conf = SparkConf().setAll([("spark.app.name", "Spark_Processor"), ("spark.redis.port", "6379"), 
                                      ("spark.jars", "spark-redis-branch-2.4/target/spark-redis_2.11-2.5.0-SNAPSHOT-jar-with-dependencies.jar"), 
                                      ("spark.executor.memory", MAX_MEMORY), ("spark.driver.memory", MAX_MEMORY), 
                                      ("spark.memory.fraction", "0.6")])
    sc = SparkContext(conf=conf)
    return sc

def printBatch():
    global newColumns
    print(newColumns.show())

if __name__ == '__main__':
    #global sc
    sc = init_spark_context()
    spark = SparkSession.builder.config(conf = sc.getConf()).getOrCreate()
    #print(read_moviedf.show())
    read_moviedf = spark.read.format("org.apache.spark.sql.redis").option("table", "movie").option("key.column", "title").load()
    #global moviedf
    moviedf = read_moviedf.sort("title")
    datasets_path = os.path.join('..','movie_recommendation_system', 'datasets')
    complete_ratings_file = os.path.join(datasets_path, 'ml-latest', 'ratings.csv')
    movies_file = os.path.join(datasets_path, 'ml-latest', 'movies.csv')

    movie = spark.read.option("inferSchema", "true").option("header", "true").csv(movies_file)
    
    ratingschema = StructType()\
        .add("userId", IntegerType(), True)\
        .add("movieId", IntegerType(), True)\
        .add("rating", DoubleType(), True)\
        .add("timeStamp", IntegerType(), True)

    #global ratingdf
    ratingdf = spark.read.format("csv")\
        .option("header",True)\
        .schema(ratingschema)\
        .load(complete_ratings_file)

    #global ratingdf
    ratingdf = ratingdf.drop("timestamp")
    #global ratingdf
    ratingdf = ratingdf.withColumn("key", (concat(lit("User ID: "),col("userId"),lit(", Movie ID: "),col("movieID"))))
    #global ratingdf
    ratingdf = ratingdf.select("key", "userId", "movieId", "rating")
    #global ratColumns
    ratColumns = ratingdf.columns
    #print(moviedf.show())
    #print(ratingdf.show())
    newColumns = spark.createDataFrame([], ratingdf.schema)
    recEng = RecommendationEngine(sc, moviedf, ratingdf)
    
    app.run()