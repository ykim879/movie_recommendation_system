
import os
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.recommendation import ALS
from pyspark.ml.tuning import ParamGridBuilder, CrossValidator
import math
from operator import add
from pyspark.sql.functions import avg
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
        (training, test) = self.ratingforals.randomSplit([0.8, 0.2])
        # Build the recommendation model using ALS on the training data
        # Note we set cold start strategy to 'drop' to ensure we don't get NaN evaluation metrics
        # c
        als = ALS(userCol="userId", itemCol="movieId", ratingCol="rating", coldStartStrategy="drop", nonnegative = True, implicitPrefs = False, maxIter=20, regParam=0.05, rank=20)
        self.model = als.fit(training)
        '''
        param_grid = ParamGridBuilder() \
            .addGrid(als.rank, [10, 50, 100, 150]) \
            .addGrid(als.regParam, [.01, .05, .1, .15]) \
            .build()

        evaluator = RegressionEvaluator(metricName="rmse", labelCol="rating", predictionCol="prediction") 
        print ("Num models to be tested: ", len(param_grid))
        cv = CrossValidator(estimator=als, estimatorParamMaps=param_grid, evaluator=evaluator, numFolds=5)
        models = cv.fit(training)

        #Extract best model from the cv model above
        self.model = models.bestModel

        print("**Best Model**")

        # # Print "Rank"
        print("  Rank:", self.model._java_obj.parent().getRank())

        # Print "MaxIter"
        print("  MaxIter:", self.model._java_obj.parent().getMaxIter())

        # Print "RegParam"
        print("  RegParam:", self.model._java_obj.parent().getRegParam())
        '''
        # Evaluate the model by computing the RMSE on the test data
        predictions = self.model.transform(test)
        evaluator = RegressionEvaluator(metricName="rmse", labelCol="rating", predictionCol="prediction")
        rmse = evaluator.evaluate(predictions)
        print("Root-mean-square error = " + str(rmse))
        
        meanRating = training.rdd.map(lambda x: x[3]).mean()
        baselineRmse = math.sqrt(test.rdd.map(lambda x: (meanRating - x[3]) ** 2).reduce(add) / test.count())
        improvement = (baselineRmse - rmse) / baselineRmse * 100 
        print("The best model improves the baseline by " + "%1.2f" % (improvement) + "%.")
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
        print(recommendations)
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