from flask import Flask, render_template
from flask import request

import os
import redis
import json

app = Flask(__name__)
r = redis.Redis(host='localhost', port=6379, db=0)

@app.route('/')
def hello():
    return render_template('index.html')

@app.route('/search', methods = ['POST'])
def search_values():
    value = request.form["movie"]
    exp = "movie:*"
    for val in value:
        exp += "[" + str(val.lower()) + str(val.upper()) + "]"
    exp += '*'
    keys = r.keys(pattern=exp)
    a = []
    for key in keys:
        newStr = key.decode('utf-8')
        movieId = r.hgetall(newStr)[b'movieId'].decode("utf-8")
        val = key.decode('utf-8')[6:]
        #print(val)
        title = val[:-7]
        date = val[-5:-1]
        a.append((movieId, title, date))
        
    return render_template("searched.html", keys=a)

@app.route('/recommendations', methods=['POST'])
def findPastRecommendation():
    print(request.form['choice'])
    print(request.form['userId'])
    key = 'rating:User ID: ' + request.form['userId'] +  ', Movie ID: ' +  request.form['choice']
    a = r.hgetall(key)
    if not a:
        a = ['Not Rated Yet']
    return json.dumps(a)   

if __name__ == '__main__':
   app.run()