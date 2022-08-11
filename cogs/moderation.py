# -*- coding: utf-8 -*-

from discord.ext import commands


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot: commands.Bot = bot

    @commands.hybrid_command(name="ban")
    async def ban(self, ctx: commands.Context) -> None:
        await ctx.send("Hi, this is a placeholder")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Moderation(bot))
