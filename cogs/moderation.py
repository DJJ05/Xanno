# -*- coding: utf-8 -*-
import asyncio
import datetime

import discord
from discord import app_commands
from discord.ext import commands

from main import Xanno
from utils.views import RevokeButton, RevokeView


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
        resp = await ctx.reply(
            content=cont, embed=embed, view=view
        )
        await asyncio.sleep(60)

        button = view.children[0]
        if not button.disabled:
            button.disabled = True
            await resp.edit(view=view)


async def setup(bot: Xanno) -> None:
    await bot.add_cog(Moderation(bot))
