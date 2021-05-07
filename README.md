<h1>Movie Recommendation System</h1>

<h2>Create Conda Environment</h2>
Download: <https://conda.io/projects/conda/en/latest/user-guide/install/index.html> <br />
Make sure a Python 3.6+ installation is being used <br />

Create a new Conda environment: `conda create --name movie --file requirements.txt` <br />

Activate the environment: `conda activate movie`

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
Clone the repository: https://github.com/RedisLabs/spark-redis/tree/branch-2.4 <br />

Enter the folder: `cd spark-redis` and run: `mvn clean package -DskipTests` <br />

Copy the generated `spark-redis-<version>-jar-with-dependencies.jar` and place it inside the `jars` subfolder of the Conda `pyspark` installation <br />

If you are having trouble finding the `pyspark` installation open a python shell inside the `movie` conda environment by calling `python`, running `import pyspark`, and running `pyspark`. It is likely your filepath will look as follows: `<some-path>/python<version>/site-packages/pyspark/__init__.py`.<br />
Navigate to `<some-path>/python<version>/site-packages/pyspark`. There should be a `jars` folder at this location, inside which the aforementioned jar file should be copied into.

<h2>Run fillRedis.py to populate the Redis database with Movies/Ratings/Genres</h2>
Once in the Conda environment, run `python fillRedis.py`. Make sure that before this, you have turned the redis server on. To do this, in a separate window, navigate to the `src` folder within the redis folder and run `./redis-server`.

<h2>Run app.py</h2>
Within the conda environment, run `python app.py`. It will take a couple of minutes to process but it should output to navigate to a local webpage, which you can copy and paste into a browser.
