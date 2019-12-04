import random
import os

from flask import Flask, session
from data.data import database, logger, GenericError, birdList, screech_owls

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

# Web Database Keys

# web.session:session_id : {
#   bird: ""
#   media_type: ""
#   answered: 1
#   prevB: ""
#   prevJ: 20
#   tempScore: 0
#   user_id: 0
# }

# web.user:user_id : {
#   avatar_hash: ""
#   avatar_url: "https://cdn.discordapp.com/avatars/{user_id}/{avatar_hash}.png"
#   username: ""
#   discriminator: ""
# }


def web_session_setup(session_id):
    logger.info("setting up session")
    session_id = str(session_id)
    if database.exists(f"web.session:{session_id}"):
        logger.info("session data ok")
    else:
        database.hmset(
            f"web.session:{session_id}", {
                "bird": "",
                "media_type": "",
                "answered": 1,  # true = 1, false = 0
                "prevB": "",
                "prevJ": 20,
                "tempScore": 0,  # not used = -1
                "user_id": 0
            }
        )
        logger.info("session set up")


def update_web_user(user_data):
    logger.info("updating user data")
    user_id = str(user_data['id'])
    database.hmset(
        f"web.user:{user_id}", {
            "avatar_hash": str(user_data['avatar']),
            "avatar_url": f"https://cdn.discordapp.com/avatars/{user_id}/{str(user_data['avatar'])}.png",
            "username": str(user_data['username']),
            "discriminator": str(user_data['discriminator'])
        }
    )
    logger.info("updated user data")


def get_session_id():
    if "session_id" not in session:
        session["session_id"] = start_session()
        return str(session["session_id"])
    elif verify_session(session["session_id"]) is False:
        session["session_id"] = start_session()
        return str(session["session_id"])
    else:
        return str(session["session_id"])


def start_session():
    logger.info("creating session id")
    session_id = 0
    session_id = random.randint(9999000000000000, 9999099999999999)
    while database.exists(f"web.session:{session_id}") and session_id == 0:
        session_id = random.randint(9999000000000000, 9999099999999999)
    logger.info(f"session_id: {session_id}")
    web_session_setup(session_id)
    logger.info(f"created session id: {session_id}")
    return session_id


def verify_session(session_id):
    session_id = str(session_id)
    logger.info(f"verifying session id: {session_id}")
    if not database.exists(f"web.session:{session_id}"):
        logger.info("doesn't exist")
        return False
    elif int(database.hget(f"web.session:{session_id}", "user_id")) == 0:
        logger.info("exists, no user id")
        return True
    else:
        logger.info("exists with user id")
        return int(database.hget(f"web.session:{session_id}", "user_id"))
