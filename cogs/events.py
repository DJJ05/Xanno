# -*- coding: utf-8 -*-
from __future__ import annotations

import datetime

import discord
from discord.ext import commands

from main import Xanno


class Events(commands.Cog):
    def __init__(self, bot: Xanno) -> None:
        self.bot: Xanno = bot

    async def error_embed(self, ctx: discord.Context, message: str) -> discord.Message:
        embed = discord.Embed(
            colour=self.bot.colour,
            title="An error occurred",
            description=message,
            timestamp=datetime.datetime.now(),
        )
        return await ctx.reply(embed=embed)

    @commands.Cog.listener(name="on_command_error")
    async def on_command_error(
        self, ctx: commands.Context, error: commands.CommandError
    ) -> discord.Message | None:
        cog = ctx.cog

        if hasattr(ctx.command, "on_error") or (
            cog and cog._get_overridden_method(cog.cog_command_error) is not None
        ):
            return

        error = getattr(error, "original", error)
        ignored = (commands.CommandNotFound,)

        if isinstance(error, ignored):
            return

        elif "message" in error.__dir__():
            return await self.error_embed(ctx, error.message)
        elif "args" in error.__dir__():
            return await self.error_embed(
                ctx,
                " ".join(
                    [
                        (arg[0].upper() + arg[1:] + ("." if arg[-1] != "." else ""))
                        for arg in error.args
                    ]
                ),
            )

        elif isinstance(error, commands.ConversionError):
            return await ctx.reply(
                f"Conversion error: {getattr(error.converter, '__name__', error.converter)} raised {error.original}"
            )

        elif isinstance(error, commands.TooManyArguments):
            return await ctx.reply(
                'Too many arguments. Wrap spaces with "" to prevent errors'
            )

        elif isinstance(error, commands.BadArgument):
            return await ctx.reply("Improper argument was passed")

        elif isinstance(error, commands.NotOwner):
            return await ctx.reply("This command is owner-only")

        elif isinstance(error, commands.DisabledCommand):
            return await ctx.reply("This command is currently disabled")

        else:
            self.bot.logger.error(f"An unknown {type(error)} exception occurred")
            return await ctx.reply(
                f"An unknown {type(error)} exception occurred. It has been reported"
            )


async def setup(bot: Xanno) -> None:
    await bot.add_cog(Events(bot))
