# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import datetime
import json
from itertools import zip_longest

import discord
from discord import app_commands
from discord.ext import commands

from main import Xanno
from utils.mappings import LOGGING_CALLBACKS
from utils.views import RevokeView


class Moderation(commands.Cog):
    def __init__(self, bot: Xanno) -> None:
        self.bot: Xanno = bot

    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    @commands.hybrid_command(name="ban")
    @app_commands.describe(
        member="The member to ban",
        days_to_purge="Last n days to delete member's messages. Can be none",
        reason="Reason for the ban. Can be none",
    )
    async def ban(
        self,
        ctx: commands.Context,
        member: discord.Member,
        days_to_purge: int = 1,
        *,
        reason: str = "None",
    ) -> discord.Message:
        """Ban a member from a guild"""
        if member == ctx.me:
            return await ctx.reply("I cannot ban myself")

        dtp = days_to_purge
        dtp = 0 if dtp < 0 else 7 if dtp > 7 else dtp
        freason = f"{str(ctx.author)}({ctx.author.id}): {reason}"

        embed = discord.Embed(
            colour=self.bot.colour,
            title="Member successfully banned",
            description=f"`User:` {str(member)}({member.id})\n"
            f"`Moderator:` {str(ctx.author)}({ctx.author.id})\n"
            f"`Reason:` {reason}\n"
            f"`DTP:` {dtp}",
            timestamp=datetime.datetime.now(),
        )
        embed.set_thumbnail(url=str(member.display_avatar))

        embed2 = embed.copy()
        embed2.title = f"You were banned from {ctx.guild.name}"

        cont = "User has been informed"
        try:
            await member.send(embed=embed2)
        except discord.HTTPException:
            cont = "User could not be informed"

        await member.ban(delete_message_days=dtp, reason=freason)

        view = RevokeView(bot=self.bot, member=member)
        resp = await ctx.reply(content=cont, embed=embed, view=view)
        await asyncio.sleep(60)

        button = view.children[0]
        if not button.disabled:
            button.disabled = True
            await resp.edit(view=view)
            view.stop()

    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.hybrid_group(name="logging")
    async def logging(self, ctx: commands.Context) -> None:
        ...

    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @logging.command(name="config")
    async def config(self, ctx: commands.Context) -> None | discord.Message:
        """Configure the logging extension for your server"""
        with open("logging.json", "r") as fp:
            data = json.load(fp)

        if not data.get(str(ctx.guild.id)):
            config = {"channel": None, "callbacks": LOGGING_CALLBACKS}
            data[str(ctx.guild.id)] = config
        else:
            config = data[str(ctx.guild.id)]

        channel = (
            None if not config["channel"] else ctx.guild.get_channel(config["channel"])
        )

        embed = discord.Embed(
            colour=self.bot.colour,
            title=f"Logging is {'enabled' if channel else 'disabled'} in {ctx.guild.name}",
            description=f"**Callbacks are being redirected to {channel.mention}**\n```ansi"
            if channel
            else "",
            timestamp=datetime.datetime.now(),
        )

        if channel:
            callbacks = list(
                zip_longest(
                    *([iter([(k, v) for k, v in config["callbacks"].items()])] * 2),
                    fillvalue=None,
                )
            )
            for group in callbacks:
                to_add = []
                for item in group:
                    if item:
                        emoji = "✅" if item[1] else "❌"
                        ansi = f"\u001b[{'32' if item[1] else '31'}m"
                        to_add.append(
                            f"{emoji}{ansi}{item[0].removeprefix('on_')}\u001b[0m"
                        )
                to_add[0] += " " * (34 - len(to_add[0]))
                embed.description += "\n" + "".join(to_add)
            embed.description += "\n```"

        return await ctx.reply(embed=embed)


async def setup(bot: Xanno) -> None:
    await bot.add_cog(Moderation(bot))
