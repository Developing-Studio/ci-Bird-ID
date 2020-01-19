# skip.py | commands for skipping birds
# Copyright (C) 2019-2020  EraserBird, person_v1.32, hmmm

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

from discord.ext import commands

from data.data import database, get_wiki_url, logger
from functions import channel_setup, user_setup


class Skip(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Skip command - no args
    @commands.command(help="- Skip the current bird to get a new one", aliases=["sk"])
    @commands.cooldown(1, 5.0, type=commands.BucketType.channel)
    async def skip(self, ctx):
        logger.info("command: skip")

        await channel_setup(ctx)
        await user_setup(ctx)

        currentBird = str(database.hget(f"channel:{str(ctx.channel.id)}", "bird"))[2:-1]
        database.hset(f"channel:{str(ctx.channel.id)}", "bird", "")
        database.hset(f"channel:{str(ctx.channel.id)}", "answered", "1")
        if currentBird != "":  # check if there is bird
            url = get_wiki_url(currentBird)
            await ctx.send(f"Ok, skipping {currentBird.lower()}")
            await ctx.send(url if not database.exists(f"race.data:{str(ctx.channel.id)}") else f"<{url}>")  # sends wiki page
            database.zadd("streak:global", {str(ctx.author.id): 0})  # end streak
            if database.exists(f"race.data:{str(ctx.channel.id)}") and str(
                        database.hget(f"race.data:{str(ctx.channel.id)}", "media"))[2:-1] == "image":

                    limit = int(database.hget(f"race.data:{str(ctx.channel.id)}", "limit"))
                    first = database.zrevrange(f"race.scores:{str(ctx.channel.id)}", 0, 0, True)[0]
                    if int(first[1]) >= limit:
                        logger.info("race ending")
                        race = self.bot.get_cog("Race")
                        await race.stop_race_(ctx)
                    else:
                        logger.info("auto sending next bird image")
                        addon, bw = map(str, database.hmget(f"race.data:{str(ctx.channel.id)}", ["addon", "bw"]))
                        birds = self.bot.get_cog("Birds")
                        await birds.send_bird_(ctx, addon[2:-1], bw[2:-1])
        else:
            await ctx.send("You need to ask for a bird first!")

    # Skip command - no args
    @commands.command(help="- Skip the current goatsucker to get a new one", aliases=["goatskip", "sg"])
    @commands.cooldown(1, 5.0, type=commands.BucketType.channel)
    async def skipgoat(self, ctx):
        logger.info("command: skipgoat")

        await channel_setup(ctx)
        await user_setup(ctx)

        currentBird = str(database.hget(f"channel:{str(ctx.channel.id)}", "goatsucker"))[2:-1]
        database.hset(f"channel:{str(ctx.channel.id)}", "goatsucker", "")
        database.hset(f"channel:{str(ctx.channel.id)}", "gsAnswered", "1")
        if currentBird != "":  # check if there is bird
            url = get_wiki_url(currentBird)
            await ctx.send(f"Ok, skipping {currentBird.lower()}\n{url}")  # sends wiki page
            database.zadd("streak:global", {str(ctx.author.id): 0})
        else:
            await ctx.send("You need to ask for a bird first!")

    # Skip song command - no args
    @commands.command(help="- Skip the current bird call to get a new one", aliases=["songskip", "ss"])
    @commands.cooldown(1, 10.0, type=commands.BucketType.channel)
    async def skipsong(self, ctx):
        logger.info("command: skipsong")

        await channel_setup(ctx)
        await user_setup(ctx)

        currentSongBird = str(database.hget(f"channel:{str(ctx.channel.id)}", "sBird"))[2:-1]
        database.hset(f"channel:{str(ctx.channel.id)}", "sBird", "")
        database.hset(f"channel:{str(ctx.channel.id)}", "sAnswered", "1")
        if currentSongBird != "":  # check if there is bird
            url = get_wiki_url(currentSongBird)
            await ctx.send(f"Ok, skipping {currentSongBird.lower()}")
            await ctx.send(url if not database.exists(f"race.data:{str(ctx.channel.id)}") else f"<{url}>")  # sends wiki page
            database.zadd("streak:global", {str(ctx.author.id): 0})
            if database.exists(f"race.data:{str(ctx.channel.id)}") and str(
                        database.hget(f"race.data:{str(ctx.channel.id)}", "media"))[2:-1] == "song":

                    limit = int(database.hget(f"race.data:{str(ctx.channel.id)}", "limit"))
                    first = database.zrevrange(f"race.scores:{str(ctx.channel.id)}", 0, 0, True)[0]
                    if int(first[1]) >= limit:
                        logger.info("race ending")
                        race = self.bot.get_cog("Race")
                        await race.stop_race_(ctx)
                    else:
                        logger.info("auto sending next bird song")
                        addon, bw = map(str, database.hmget(f"race.data:{str(ctx.channel.id)}", ["addon", "bw"]))
                        birds = self.bot.get_cog("Birds")
                        await birds.send_bird_(ctx, addon[2:-1], bw[2:-1])
        else:
            await ctx.send("You need to ask for a bird first!")

def setup(bot):
    bot.add_cog(Skip(bot))
