from flask import Flask
from flask_redis import FlaskRedis


app = Flask(__name__)
app.config.from_object('undemolition.default_settings')
# app.config.from_envvar('TWEETMAPPER_SETTINGS')

redis_store = FlaskRedis(app)


@app.route("/")
def main():
    return "Welcome!"