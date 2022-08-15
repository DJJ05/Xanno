# -*- coding: utf-8 -*-
import asyncio
import datetime
import logging
import os
import sys
import traceback

import discord
from discord.ext import commands
from dotenv import load_dotenv


class Xanno(commands.Bot):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(
            command_prefix=kwargs.pop(
                "command_prefix", commands.when_mentioned_or("xo.")
            ),
            intents=kwargs.pop("intents", discord.Intents.all()),
            case_insensitive=kwargs.pop("case_insensitive", True),
            description=kwargs.pop("description", "General utility bot"),
            owner_ids=kwargs.pop("owner_ids", []).append(670564722218762240),
            strip_after_prefix=kwargs.pop("strip_after_prefix", True),
            log_handler=kwargs.pop(
                "log_handler", logging.FileHandler(filename="log.LOG", encoding="utf-8")
            ),
            allowed_mentions=discord.AllowedMentions(everyone=False),
            *args,
            **kwargs,
        )
        self.logger = self.fetchlogger()
        self.synced = False
        self.colour = 0x6AC9B8

    async def on_error(self, event_method, *args, **kwargs) -> None:
        ei = sys.exc_info()
        private = "".join(traceback.format_exception(ei[0], ei[1], ei[2]))
        public = (
            "".join(traceback.format_exception(ei[0], ei[1], ei[2], 2))
            .replace(os.getcwd(), "CWD")
            .replace("CWD/venv/lib/python3.10/site-packages/discord", "discord")
        )

        channel = self.get_channel(1008350814730993675)
        embed = discord.Embed(
            colour=self.colour,
            title="An unknown error occurred",
            description=f"`FUNC:` {event_method}\n```ansi\n\u001b[31m"
            + public
            + "\n```",
            timestamp=datetime.datetime.now(),
        )
        await channel.send(embed=embed)
        return self.logger.error(
            private
            + f"{', '.join([str(a) for a in args])} —— {', '.join(list(kwargs))}"
        )

    @staticmethod
    def fetchlogger() -> logging.Logger:
        logger = logging.getLogger("xanno")
        logger.setLevel(logging.DEBUG)

        handler = logging.FileHandler(filename="log.LOG", encoding="utf-8")
        streamer = logging.StreamHandler()

        dt_fmt = "%Y-%m-%d %H:%M:%S"
        formatter = logging.Formatter(
            "[{asctime}] [{levelname:<8}] {name}: {message}", dt_fmt, style="{"
        )

        handler.setFormatter(formatter)
        streamer.setFormatter(formatter)

        logger.addHandler(handler)
        logger.addHandler(streamer)
        return logger

    async def setup_hook(self) -> None:
        for filename in os.listdir("cogs"):
            if filename.endswith(".py"):
                try:
                    await self.load_extension(f'cogs.{filename.removesuffix(".py")}')
                except commands.ExtensionNotFound:
                    self.logger.warning(f"Extension {filename} failed to load")
        await self.load_extension("jishaku")

    # noinspection PyMethodMayBeStatic
    async def on_ready(self) -> None:
        self.logger.info(f"Bot initiated and ready")

        if not self.synced:
            await self.tree.sync()
            self.synced = True


async def main(bot: Xanno) -> None:
    load_dotenv()
    token = os.getenv("TOKEN")

    async with bot:
        await bot.start(token)


if __name__ == "__main__":
    xanno = Xanno()
    try:
        asyncio.run(main(bot=xanno))
    except KeyboardInterrupt:
        xanno.logger.info("KeyboardInterrupt, exiting gracefully")
