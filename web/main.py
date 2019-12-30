import random
import asyncio
import flask
import urllib.parse

from sentry_sdk import capture_exception
from flask import jsonify, redirect
from web.data import birdList, logger, app, FRONTEND_URL
from web.functions import get_media, get_sciname

from . import practice, user
app.register_blueprint(practice.bp)
app.register_blueprint(user.bp)


@app.route('/')
def api_index():
    logger.info("index page accessed")
    return "<h1>Hello!</h1><p>This is the index page for the Bird-ID internal API.<p>"


@app.route('/bird')
def bird_info():
    logger.info("fetching random bird")
    content = {}
    bird = random.choice(birdList)
    logger.info(f"bird: {bird}")
    content["bird"] = bird
    content["sciName"] = asyncio.run(get_sciname(bird))
    content["imageURL"] = urllib.parse.quote(f"/image/{bird}")
    content["songURL"] = urllib.parse.quote(f"/song/{bird}")
    logger.info(f"{bird} sent!")
    return content


@app.route('/image/<string:bird>')
def bird_image(bird):
    path, ext = asyncio.run(get_media(bird, "images"))
    return flask.send_file(f"../{path}")


@app.route('/song/<string:bird>')
def bird_song(bird):
    path, ext = asyncio.run(get_media(bird, "songs"))
    return flask.send_file(f"../{path}")

@app.errorhandler(403)
def not_allowed(e):
    capture_exception(e)
    return jsonify(error=str(e)), 403

@app.errorhandler(404)
def not_found(e):
    capture_exception(e)
    return jsonify(error=str(e)), 404

@app.errorhandler(406)
def input_error(e):
    capture_exception(e)
    return jsonify(error=str(e)), 406

@app.errorhandler(500)
def other_internal_error(e):
    capture_exception(e)
    return jsonify(error=str(e)), 500

@app.errorhandler(503)
def internal_error(e):
    capture_exception(e)
    return jsonify(error=str(e)), 503