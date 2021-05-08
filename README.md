<h1>Movie Recommendation System</h1>

<h2>A Unix/Linux Environment is necessary</h2>
After clone this respository, delete two folders: apache-maven-3.6.3 and redis-5.0.12
<h1>Data Preparation and Setup</h1>

<h2>Create Conda Environment</h2>
Download: <https://conda.io/projects/conda/en/latest/user-guide/install/index.html> <br />
Make sure a Python 3.6+ installation is being used <br />

Create a new Conda environment named `movie`: `conda create --name movie python=3.6` <br />

Activate the environment: `conda activate movie` <br />

Install Redis for python: `pip install redis` <br />

Install Pyspark for python: `conda install pyspark` <br />

Install Flask: `conda install flask` <br />

<h2>Download 25M MovieLense Dataset</h2>
Download: https://grouplens.org/datasets/movielens/25m/ <br />

Make a new folder inside the `movie_recommendation_system` folder named `datasets` and unzip the dataset inside.

<h2>Install Java 8 </h2>
Download: https://www.oracle.com/java/technologies/javase/javase-jdk8-downloads.html
Ensure `JAVA_HOME` is set correctly in your respective PATH

<h2>Install Redis-5.0</h2>
Find 'Redis-5.0.12' and run through installation process to setup the `redis-server` and `redis-cli`. https://download.redis.io/releases/

<h2>Install Maven</h2>
Download: https://maven.apache.org/install.html

<h2>Install Spark-Redis</h2>
Clone the repository: https://github.com/RedisLabs/spark-redis/tree/branch-2.4 into the `movie_recommendation_system` folder<br />

Enter the folder: `cd spark-redis` and run: `mvn clean package -DskipTests` <br />

Copy the generated `spark-redis-<version>-jar-with-dependencies.jar` from the generated `targets` folder and place it inside the `jars` subfolder of the Conda `pyspark` installation <br />

If you are having trouble finding the `pyspark` installation open a python shell inside the `movie` conda environment by calling `python`, running `import pyspark`, and running `pyspark`. It is likely your filepath will look as follows: `<some-path>/python<version>/site-packages/pyspark/__init__.py`.<br />
Navigate to `<some-path>/python<version>/site-packages/pyspark`. There should be a `jars` folder at this location, inside which the aforementioned jar file should be copied into.

<h2>Run fillRedis.py to populate the Redis database with Movies/Ratings/Genres</h2>
Once in the Conda environment, run 'python fillRedis.py'. Make sure that before this, you have turned the redis server on. To do this, in a separate window, navigate to the 'src' folder within the redis folder and run './redis-server'.

<h2>Run app.py</h2>
Within the conda environment, run 'python app.py'. It will take a couple of minutes to process but it should output to navigate to a local webpage, which you can copy and paste into a browser.

<h1>Application and Code</h1>

<h2>Programming Language and Libraries</h2>
The program uses Python 3.6, and the libraries necessary are pyspark, redis, flask, json. You may possibly need to import os, operator, but they should be included in the standard library. For all other libraries, they are included in requirements.txt and should be installed into the conda environment with the command included on the top.

<h2>How to Run GUI</h2>
The GUI should be pretty straightforward. For the a prompt of User ID, only input integers, and when updating and adding ratings, the valid values can be stepped though or they can be directly input.

<h1>Code Documentation and References</h1>

<h2>Github Pages Referenced</h2>
https://spark.apache.org/docs/2.2.0/ml-collaborative-filtering.html (For initial model - Changed parameters and how to input data) <br /> 
https://github.com/jadianes/spark-movie-lens/blob/master/engine.py (For Initial Structure of engine.py - Changed all functions but kept structure) <br /> 
https://github.com/databricks/spark-training/blob/master/website/movie-recommendation-with-mllib.md (For troubleshooting - Added Comparison to Baseline model) <br /> 
https://github.com/snehalnair/als-recommender-pyspark (For adding parameter tuning functionality - Unused due to OutOfMemoryError) <br />


