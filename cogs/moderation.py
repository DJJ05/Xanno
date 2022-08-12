# -*- coding: utf-8 -*-
import datetime

import discord
from discord import app_commands
from discord.ext import commands

from main import Xanno


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
        days_to_purge: commands.Greedy[int] = 1,
        *,
        reason: str = "",
    ) -> discord.Message:
        """Ban a member from a guild"""
        dtp = days_to_purge[0] if not isinstance(days_to_purge, int) else days_to_purge
        dtp = 0 if dtp < 0 else 7 if dtp > 7 else dtp
        freason = f"{str(ctx.author)}({ctx.author.id}): {reason}"
        await member.ban(delete_message_days=dtp, reason=freason)
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
        return await ctx.reply(embed=embed)


async def setup(bot: Xanno) -> None:
    await bot.add_cog(Moderation(bot))
