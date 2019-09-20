# functions.py | function definitions
# Copyright (C) 2019  EraserBird, person_v1.32, hmmm

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import asyncio
import contextlib
from mimetypes import guess_all_extensions, guess_extension
import os
import urllib.parse
from random import randint

import aiohttp
import discord
import eyed3

from data.data import (GenericError, logger, states, database,
                       birdListMaster, sciBirdListMaster,
                       songBirdsMaster, sciSongBirdsMaster)

TAXON_CODE_URL = "https://search.macaulaylibrary.org/api/v1/find/taxon?q={}"
CATALOG_URL = ("https://search.macaulaylibrary.org/catalog.json?searchField=species" +
               "&taxonCode={}&count={}&mediaType={}&sex={}&age={}&behavior={}&qua=3,4,5")
COUNT = 20  # set this to include a margin of error in case some urls throw error code 476 due to still being processed
# Valid file types
valid_image_extensions = {"jpg", "png", "jpeg", "gif"}
valid_audio_extensions = {"mp3", "wav", "ogg", "m4a"}


# sets up new channel
async def channel_setup(ctx):
    if database.exists(str(ctx.channel.id)):
        return
    else:
        # ['prevS', 'prevB', 'prevJ', 'goatsucker answered', 'goatsucker',
        #  'totalCorrect', 'songanswered', 'songbird', 'answered', 'bird']
        database.lpush(str(ctx.channel.id), "20", "", "", "20", "1", "", "0", "1",
                       "", "1", "")
        # true = 1, false = 0, index 0 is last arg, prevJ is 20 to define as integer
        await ctx.send("Ok, setup! I'm all ready to use!")


# sets up new user
async def user_setup(ctx):
    if database.zscore("users", str(ctx.message.author.id)) is not None:
        return
    else:
        database.zadd("users", {str(ctx.message.author.id): 0})
        await ctx.send("Welcome <@" + str(ctx.message.author.id) + ">!")


# sets up new birds
async def bird_setup(bird):
    if database.zscore("incorrect", str(bird).title()) is not None:
        return
    else:
        database.zadd("incorrect", {str(bird).title(): 0})


# Function to run on error
def error_skip(ctx):
    logger.info("ok")
    database.lset(str(ctx.channel.id), 0, "")
    database.lset(str(ctx.channel.id), 1, "1")


def error_skip_song(ctx):
    logger.info("ok")
    database.lset(str(ctx.channel.id), 2, "")
    database.lset(str(ctx.channel.id), 3, "1")


def error_skip_goat(ctx):
    logger.info("ok")
    database.lset(str(ctx.channel.id), 5, "")
    database.lset(str(ctx.channel.id), 6, "1")


def check_state_role(ctx):
    logger.info("checking roles")
    user_states = []
    if ctx.guild is not None:
        user_role_names = [role.name.lower() for role in ctx.author.roles]
        for state in list(states.keys()):
            if len(set(user_role_names + states[state]["aliases"]) -
                set(user_role_names).symmetric_difference(set(states[state]["aliases"]))) is 0:  # gets similarities
                user_states.append(state)
    logger.info(f"user roles: {user_states}")
    return user_states


# Gets a bird picture and sends it to user:
# ctx - context for message (discord thing)
# bird - bird picture to send (str)
# on_error - function to run when an error occurs (function)
# message - text message to send before bird picture (str)
# addOn - string to append to search for female/juvenile birds (str)
async def send_bird(ctx, bird, on_error=None, message=None, addOn=""):
    if bird == "":
        logger.error("error - bird is blank")
        await ctx.send(
            "**There was an error fetching birds.**\n*Please try again.*")
        if on_error is not None:
            on_error(ctx)
        return

    delete = await ctx.send("**Fetching.** This may take a while.")
    # trigger "typing" discord message
    await ctx.trigger_typing()

    try:
        response = await get_image(ctx, bird, addOn)
    except GenericError as e:
        await delete.delete()
        await ctx.send(f"**An error has occurred while fetching images.**\n*Please try again.*\n**Reason:** {str(e)}")
        if on_error is not None:
            on_error(ctx)
        return

    filename = str(response[0])
    extension = str(response[1])
    statInfo = os.stat(filename)
    if statInfo.st_size > 8000000:  # another filesize check
        await delete.delete()
        await ctx.send("**Oops! File too large :(**\n*Please try again.*")
    else:
        with open(filename, 'rb') as img:
            if message is not None:
                await ctx.send(message)
            # change filename to avoid spoilers
            await ctx.send(file=discord.File(img, filename="bird." + extension)
                           )
            await delete.delete()


# Gets a bird sound and sends it to user:
# ctx - context for message (discord thing)
# bird - bird picture to send (str)
# on_error - function to run when an error occurs (function)
# message - text message to send before bird picture (str)
async def send_birdsong(ctx, bird, on_error=None, message=None):
    if bird == "":
        logger.error("error - bird is blank")
        await ctx.send(
            "**There was an error fetching birds.**\n*Please try again.*")
        if on_error is not None:
            on_error(ctx)
        return

    delete = await ctx.send("**Fetching.** This may take a while.")
    # trigger "typing" discord message
    await ctx.trigger_typing()

    try:
        response = await get_song(ctx, bird)
    except GenericError as e:
        await delete.delete()
        await ctx.send(f"**An error has occurred while fetching songs.**\n*Please try again.*\n**Reason:** {str(e)}")
        if on_error is not None:
            on_error(ctx)
        return

    filename = str(response[0])
    extension = str(response[1])

    # remove spoilers in tag metadata
    audioFile = eyed3.load(filename)
    if audioFile is not None and audioFile.tag is not None:
        audioFile.tag.remove(filename)

    statInfo = os.stat(filename)
    if statInfo.st_size > 8000000:  # another filesize check
        await delete.delete()
        await ctx.send("**Oops! File too large :(**\n*Please try again.*")
    else:
        with open(filename, 'rb') as img:
            if message is not None:
                await ctx.send(message)
            # change filename to avoid spoilers
            await ctx.send(file=discord.File(img, filename="bird." + extension)
                           )
            await delete.delete()


# Function that gets bird images to run in pool (blocking prevention)
# Chooses one image to send
async def get_image(ctx, bird, addOn=None):
    # fetch scientific names of birds
    if bird in birdListMaster:
        sciBird = sciBirdListMaster[birdListMaster.index(bird)]
    else:
        sciBird = bird
    images = await get_files(sciBird, "images", addOn)
    logger.info("images: " + str(images))
    prevJ = int(str(database.lindex(str(ctx.channel.id), 7))[2:-1])
    # Randomize start (choose beginning 4/5ths in case it fails checks)
    if images:
        j = (prevJ + 1) % len(images)
        logger.debug("prevJ: " + str(prevJ))
        logger.debug("j: " + str(j))

        for x in range(j, len(images)):  # check file type and size
            image_link = images[x]
            extension = image_link.split('.')[-1]
            logger.debug("extension: " + str(extension))
            statInfo = os.stat(image_link)
            logger.debug("size: " + str(statInfo.st_size))
            if extension.lower(
            ) in valid_image_extensions and statInfo.st_size < 8000000:  # 8mb discord limit
                logger.info("found one!")
                break
            elif x == len(images) - 1:
                j = (j + 1) % (len(images))
                raise GenericError("No Valid Images Found")

        database.lset(str(ctx.channel.id), 7, str(j))
    else:
        raise GenericError("No Images Found")

    return [image_link, extension]


# Function that gets bird sounds to run in pool (blocking prevention)
# Chooses one sound to send
async def get_song(ctx, bird):
    # fetch scientific names of birds
    if bird in songBirdsMaster:
        sciBird = sciSongBirdsMaster[songBirdsMaster.index(bird)]
    else:
        sciBird = bird
    songs = await get_files(sciBird, "songs")
    logger.info("songs: " + str(songs))
    prevK = int(str(database.lindex(str(ctx.channel.id), 10))[2:-1])
    # Randomize start (choose beginning 4/5ths in case it fails checks)
    if songs:
        k = (prevK + 1) % len(songs)
        logger.debug("prevK: " + str(prevK))
        logger.debug("k: " + str(k))

        for x in range(k, len(songs)):  # check file type and size
            song_link = songs[x]
            extension = song_link.split('.')[-1]
            logger.debug("extension: " + str(extension))
            statInfo = os.stat(song_link)
            logger.debug("size: " + str(statInfo.st_size))
            if extension.lower(
            ) in valid_audio_extensions and statInfo.st_size < 8000000:  # 8mb discord limit
                logger.info("found one!")
                break
            elif x == len(songs) - 1:
                k = (k + 1) % (len(songs))
                raise GenericError("No Valid Songs Found")

        database.lset(str(ctx.channel.id), 7, str(k))
    else:
        raise GenericError("No Songs Found")

    return [song_link, extension]


# Manages cache
async def get_files(sciBird, media_type, addOn=""):
    directory = f"cache/{media_type}/{sciBird}{addOn}/"
    try:
        logger.info("trying")
        files_dir = os.listdir(directory)
        logger.info(directory)
        if not files_dir:
            raise GenericError("No Files")
        return [f"{directory}{path}" for path in files_dir]
    except (FileNotFoundError, GenericError):
        logger.info("fetching files")
        # if not found, fetch images
        logger.info("scibird: " + str(sciBird))
        return await download_media(sciBird, media_type, addOn, directory)


# Manages downloads
async def download_media(bird, media_type, addOn="", directory=None, session=None):
    if directory is None:
        directory = f"cache/{media_type}/{bird}{addOn}/"

    if addOn == "female":
        sex = "f"
    else:
        sex = ""

    if addOn == "juvenile":
        age = "j"
    else:
        age = ""

    if media_type == "images":
        media = "p"
    elif media_type == "songs":
        media = "a"

    async with contextlib.AsyncExitStack() as stack:
        if session is None:
            session = await stack.enter_async_context(aiohttp.ClientSession())
        urls = await _get_urls(session, bird, media, sex, age)
        if not os.path.exists(directory):
            os.makedirs(directory)
        paths = [f"{directory}{i}" for i in range(len(urls))]
        filenames = await asyncio.gather(*(_download_helper(path, url, session) for path, url in zip(paths, urls)))
        logger.info(f"downloaded {media_type} for {bird}")
        return filenames


# Gets urls for downloading
async def _get_urls(session, bird, media_type, sex="", age="", sound_type=""):
    """
    bird can be either common name or scientific name
    media_type is either p(for pictures), a(for audio) or v(for video)
    sex is m,f or blank
    age is a(for adult), j(for juvenile), i(for immature(may be very few pics)) or blank
    sound_type is s(for song),c(for call) or blank
    return is list of urls. some urls may return an error code of 476(because it is still being processed);
        if so, ignore that url.
    """
    # fix labeling issues in the library and on the list
    if bird == "Porphyrio martinicus":
        bird = "Porphyrio martinica"
    elif bird == "Strix acio":
        bird = "Screech Owl"
    logger.info(f"getting file urls for {bird}")
    taxon_code_url = TAXON_CODE_URL.format(
        urllib.parse.quote(
            bird.replace("-", " ").replace("'s", "")
        )
    )
    async with session.get(taxon_code_url) as taxon_code_response:
        if taxon_code_response.status != 200:
            raise GenericError(f"An http error code of {taxon_code_response.status} occured" +
                               f" while fetching {taxon_code_url} for a {'image'if media_type=='p' else 'song'} for {bird}")
        taxon_code_data = await taxon_code_response.json()
        try:
            taxon_code = taxon_code_data[0]["code"]
        except IndexError:
            raise GenericError(f"No taxon code found for {bird}")
    catalog_url = CATALOG_URL.format(
        taxon_code, COUNT, media_type, sex, age, sound_type)
    async with session.get(catalog_url) as catalog_response:
        if catalog_response.status != 200:
            raise GenericError(f"An http error code of {catalog_response.status} occured " +
                               f"while fetching {catalog_url} for a {'image'if media_type=='p' else 'song'} for {bird}")
        catalog_data = await catalog_response.json()
        content = catalog_data["results"]["content"]
        urls = [data["mediaUrl"] for data in content]
        return urls


# Actually downloads the file
async def _download_helper(path, url, session):
    try:
        async with session.get(url) as response:
            # from https://stackoverflow.com/questions/29674905/convert-content-type-header-into-file-extension
            content_type = response.headers['content-type'].partition(';')[
                0].strip()
            if content_type.partition("/")[0] == "image":
                ext = "." + \
                    (set(ext[1:] for ext in guess_all_extensions(
                        content_type)) & valid_image_extensions).pop()

            elif content_type.partition("/")[0] == "audio":
                ext = "." + \
                    (set(ext[1:] for ext in guess_all_extensions(
                        content_type)) & valid_audio_extensions).pop()

            else:
                ext = guess_extension(content_type)

            filename = f"{path}{ext}"
            # from https://stackoverflow.com/questions/38358521/alternative-of-urllib-urlretrieve-in-python-3-5
            with open(filename, 'wb') as out_file:
                block_size = 1024 * 8
                while True:
                    block = await response.content.read(block_size)  # pylint: disable=no-member
                    if not block:
                        break
                    out_file.write(block)
            return filename
    except aiohttp.ClientError:
        logger.error(f"Client Error with url {url} and path {path}")
        raise


async def precache():
    timeout = aiohttp.ClientTimeout(total=10*60)
    conn = aiohttp.TCPConnector(limit=100)
    async with aiohttp.ClientSession(connector=conn, timeout=timeout) as session:
        logger.info("Starting cache")
        await asyncio.gather(*(download_media(bird, "images", session=session) for bird in sciBirdListMaster))
        logger.info("Starting females")
        await asyncio.gather(*(download_media(bird, "images", addOn="female", session=session) for bird in sciBirdListMaster))
        logger.info("Starting juveniles")
        await asyncio.gather(*(download_media(bird, "images", addOn="juvenile", session=session) for bird in sciBirdListMaster))
        logger.info("Starting songs")
        await asyncio.gather(*(download_media(bird, "songs", session=session) for bird in sciSongBirdsMaster))
    logger.info("Images Cached")


# spellcheck - allows one letter off/extra
def spellcheck(worda, wordb):
    worda = worda.lower().replace("-", " ").replace("'", "")
    wordb = wordb.lower().replace("-", " ").replace("'", "")
    wrongcount = 0
    if worda != wordb:
        if len(worda) != len(wordb):
            list1 = list(worda)
            list2 = list(wordb)
            longerword = max(list1, list2, key=len)
            shorterword = min(list1, list2, key=len)
            if abs(len(longerword) - len(shorterword)) > 1:
                return False
            else:
                for i in range(len(shorterword)):
                    try:
                        if longerword[i] != shorterword[i]:
                            wrongcount += 1
                            del longerword[i]
                    except IndexError:
                        wrongcount = 100
        else:
            wrongcount = sum(x != y for x, y in zip(worda, wordb))
        return wrongcount <= 1
    else:
        return True
