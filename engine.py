
import os
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.recommendation import ALS
from pyspark.sql import Row

def get_counts_and_averages(ID_and_ratings_tuple):
    nratings = len(ID_and_ratings_tuple[1])
    return ID_and_ratings_tuple[0], (nratings, float(sum(x for x in ID_and_ratings_tuple[1]))/nratings)


class RecommendationEngine:
    """A movie recommendation engine
    """
 
    def __count_and_average_ratings(self):
        """Updates the movies ratings counts from 
        the current data self.ratings_RDD
        """
        print("Counting movie ratings...")
        movie_ID_with_ratings_RDD = self.ratings_RDD.map(lambda x: (x[1], x[2])).groupByKey()
        movie_ID_with_avg_ratings_RDD = movie_ID_with_ratings_RDD.map(get_counts_and_averages)
        self.movies_rating_counts_RDD = movie_ID_with_avg_ratings_RDD.map(lambda x: (x[0], x[1][0]))
 
 
    def __train_model(self):
        """Train the ALS model with the current dataset
        """
        print("Training the ALS model...")
        self.ratingforals = self.ratings_RDD.toDF()
        (training, test) = self.ratingforals.randomSplit([0.5, 0.5])
        # Build the recommendation model using ALS on the training data
        # Note we set cold start strategy to 'drop' to ensure we don't get NaN evaluation metrics
        # c
        als = ALS(maxIter=3, regParam=0.01, userCol="userId", itemCol="movieId", ratingCol="rating", 
                  coldStartStrategy="drop")
        self.model = als.fit(training)

        # Evaluate the model by computing the RMSE on the test data
        predictions = self.model.transform(test)
        evaluator = RegressionEvaluator(metricName="rmse", labelCol="rating",
                                        predictionCol="prediction")
        rmse = evaluator.evaluate(predictions)
        print("Root-mean-square error = " + str(rmse))
        print("ALS model built!")

    
    def recommendForUser(self, userId):
        '''
        get a recommendation for a user
        
        userId: integer value for a user id
        result: recommendedMovieID: list of movie ID that a userID gets recommended
        '''
        user = self.ratingforals.select("userId").distinct().filter(self.ratingforals.userId == userId)
        userSubsetRecs = self.model.recommendForUserSubset(user, 10)
        recommendations = list(userSubsetRecs.select('recommendations').toPandas()['recommendations'])
        recommendations = recommendations[0]
        recommendedMovieID = []
        for row in recommendations:
            recommendedMovieID.append(row[0])
        return recommendedMovieID
 
 
    def __init__(self, sc, movie, ratings):
        """Init the recommendation engine given a Spark context and a dataset path
        """
 
        print("Starting up the Recommendation Engine: ")
 
        self.sc = sc
 
        # Load ratings data for later use
        
        #logger.info("Loading Ratings data...")
        #ratings_file_path = os.path.join(dataset_path, 'ratings.csv')
        #ratings_raw_RDD = self.sc.textFile(ratings_file_path)
        #ratings_raw_data_header = ratings_raw_RDD.take(1)[0]
        #self.ratings_RDD = ratings_raw_RDD.filter(lambda line: line!=ratings_raw_data_header)\
        #    .map(lambda line: line.split(",")).map(lambda tokens: (int(tokens[0]),int(tokens[1]),float(tokens[2]))).cache()
        # Load movies data for later use
        #logger.info("Loading Movies data...")
        #movies_file_path = os.path.join(dataset_path, 'movies.csv')
        #movies_raw_RDD = self.sc.textFile(movies_file_path)
        #movies_raw_data_header = movies_raw_RDD.take(1)[0]
        #self.movies_RDD = movies_raw_RDD.filter(lambda line: line!=movies_raw_data_header)\
        #    .map(lambda line: line.split(",")).map(lambda tokens: (int(tokens[0]),tokens[1],tokens[2])).cache()
        # Pre-calculate movies ratings counts
        self.movies_RDD = movie.rdd
        self.movies_titles_RDD = self.movies_RDD.map(lambda x: (int(x[0]),x[1])).cache()

        self.ratings_RDD = ratings.rdd
        self.__count_and_average_ratings()
 
        # Train the model
        #self.rank = 8
        #self.seed = 13
        #self.iterations = 10
        #self.regularization_parameter = 0.1
        self.__train_model()