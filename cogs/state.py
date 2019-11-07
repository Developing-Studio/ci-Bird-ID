# state.py | commands for state specific birds
# Copyright (C) 2019  EraserBird, person_v1.32

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

import string

import discord
from discord.ext import commands

from data.data import logger, states
from functions import channel_setup, user_setup

class States(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # set state role
    @commands.command(help="- Sets your state", name="set", aliases=["set"])
    @commands.cooldown(1, 5.0, type=commands.BucketType.user)
    @commands.guild_only()
    async def state(self, ctx, *, args):
        logger.info("set")

        await channel_setup(ctx)
        await user_setup(ctx)

        roles = [role.name.lower() for role in ctx.author.roles]
        args = args.upper().split(" ")

        for arg in args:
            if arg not in list(states.keys()):
                logger.info("invalid state")
                await ctx.send(
                    f"**Sorry, `{arg}` is not a valid state.**\n*Valid States:* `{', '.join(map(str, list(states.keys())))}`"
                )

            elif len(set(roles).intersection(set(states[arg]["aliases"]))) is 0:  # gets similarities
                # need to add roles (does not have role)
                logger.info("add roles")
                raw_roles = ctx.guild.roles
                guild_role_names = [role.name.lower() for role in raw_roles]
                guild_role_ids = [role.id for role in raw_roles]

                if states[arg]["aliases"][0].lower() in guild_role_names:
                    # guild has role
                    index = guild_role_names.index(states[arg]["aliases"][0].lower())
                    role = ctx.guild.get_role(guild_role_ids[index])

                else:
                    # create role
                    logger.info("creating role")
                    role = await ctx.guild.create_role(
                        name=string.capwords(states[arg]["aliases"][0]),
                        permissions=discord.Permissions.none(),
                        hoist=False,
                        mentionable=False,
                        reason="Create state role for bird list"
                    )

                await ctx.author.add_roles(role, reason="Set state role for bird list")
                await ctx.send(f"**Ok, added the {role.name} role!**")

            else:
                # have roles already (there were similarities)
                logger.info("already has role")
                await ctx.send(f"**You already have the `{arg}` role!**")

    # removes state role
    @commands.command(help="- Removes your state", aliases=["rm"])
    @commands.cooldown(1, 5.0, type=commands.BucketType.user)
    @commands.guild_only()
    async def remove(self, ctx, *, args):
        logger.info("remove")

        await channel_setup(ctx)
        await user_setup(ctx)

        raw_roles = ctx.author.roles
        user_role_names = [role.name.lower() for role in raw_roles]
        user_role_ids = [role.id for role in raw_roles]
        args = args.upper().split(" ")

        for arg in args:
            if arg not in list(states.keys()):
                logger.info("invalid state")
                await ctx.send(
                    f"**Sorry, `{arg}` is not a valid state.**\n*Valid States:* `{', '.join(map(str, list(states.keys())))}`"
                )

            elif states[arg]["aliases"][0].lower() not in user_role_names[1:]:
                logger.info("doesn't have role")
                await ctx.send(
                    f"**You don't have the `{arg}` state role!**\n*Your Roles:* `{', '.join(map(str, user_role_names[1:]))}`"
                )

            else:
                logger.info("deleting role")
                index = user_role_names.index(states[arg]["aliases"][0].lower())
                role = ctx.guild.get_role(user_role_ids[index])
                await ctx.author.remove_roles(role, reason="Delete state role for bird list")
                await ctx.send(f"**Ok, role {role.name} deleted!**")

    @state.error
    async def set_error(self, ctx, error):
        logger.info("set error")
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                f"**Please enter your state.**\n*Valid States:* `{', '.join(map(str, list(states.keys())))}`"
            )
        elif isinstance(error, commands.CommandOnCooldown):  # send cooldown
            await ctx.send("**Cooldown.** Try again after " + str(round(error.retry_after)) + " s.", delete_after=5.0)
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send("**This command is unavaliable in DMs!**")
        elif isinstance(error, commands.BotMissingPermissions):
            logger.error("missing permissions error")
            await ctx.send(
                f"""**The bot does not have enough permissions to fully function.**
**Permissions Missing:** `{', '.join(map(str, error.missing_perms))}`
*Please try again once the correct permissions are set.*"""
            )
        else:
            await ctx.send(
                """**An uncaught set error has occurred.**
*Please log this message in #support in the support server below, or try again.* 
**Error:** """ + str(error)
            )
            await ctx.send("https://discord.gg/fXxYyDJ")
            raise error

    @remove.error
    async def remove_error(self, ctx, error):
        logger.info("remove error")
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"**Please enter a state.**\n*Valid States:* `{', '.join(map(str, list(states.keys())))}`")
        elif isinstance(error, commands.CommandOnCooldown):  # send cooldown
            await ctx.send("**Cooldown.** Try again after " + str(round(error.retry_after)) + " s.", delete_after=5.0)
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send("**This command is unavaliable in DMs!**")
        elif isinstance(error, commands.BotMissingPermissions):
            logger.error("missing permissions error")
            await ctx.send(
                f"""**The bot does not have enough permissions to fully function.**
**Permissions Missing:** `{', '.join(map(str, error.missing_perms))}`
*Please try again once the correct permissions are set.*"""
            )
        else:
            await ctx.send(
                """**An uncaught remove error has occurred.**
*Please log this message in #support in the support server below, or try again.* 
**Error:** """ + str(error)
            )
            await ctx.send("https://discord.gg/fXxYyDJ")
            raise error

def setup(bot):
    bot.add_cog(States(bot))
