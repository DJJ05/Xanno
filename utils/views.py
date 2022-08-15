# -*- coding: utf-8 -*-
from __future__ import annotations

import datetime

import discord.ui
from discord import ButtonStyle

from main import Xanno

"""
class LogSetupModal(discord.ui.Modal):
    def __init__(
        self,
        bot: Xanno,
        guild: discord.Guild,
        user: discord.Member,
        callbacks: dict,
        default_channel: discord.TextChannel | None = None,
    ) -> None:
        super().__init__(title="Logging setup options")
        self.bot = bot
        self.user = user

        self.channel = GuildChannelsSelect(
            guild=guild, user=user, default_channel=default_channel
        )
        self.callbacks = LogCallbackSelect(callbacks=dict(islice(callbacks.items(), 25)))
        self.callbacks2 = LogCallbackSelect(callbacks=dict(islice(callbacks.items(), 25, None)))

        self.add_item(self.channel)
        self.add_item(self.callbacks)
        self.add_item(self.callbacks2)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            print(self.channel.values)
            print(self.callbacks.values)
            print(self.callbacks2.values)
            self.channel = self.bot.get_channel(int(self.channel.values[0]))
            self.callbacks = self.callbacks.values.extend(self.callbacks2.values)
            await interaction.response.defer()
            self.stop()
        except Exception as e:
            traceback.print_exception(e)


class GuildChannelInput(discord.ui.TextInput):
    ...
"""

""" Selects not officially supported by modals.
class GuildChannelsSelect(discord.ui.Select):
    def __init__(
        self,
        guild: discord.Guild,
        user: discord.Member,
        default_channel: discord.TextChannel | None = None,
    ) -> None:
        options = [
            discord.SelectOption(
                label=c.name, value=str(c.id), default=c == default_channel
            )
            for c in guild.text_channels
            if c.permissions_for(user).read_messages
        ]
        super().__init__(options=options, placeholder="Select logging channel")


class LogCallbackSelect(discord.ui.Select):
    def __init__(self, callbacks: dict) -> None:
        options = [
            discord.SelectOption(
                label=k,
                value=k,
                default=v
            )
            for k, v in callbacks.items()
        ]
        super().__init__(options=options, placeholder="Select event callbacks", max_values=len(options))
"""


class RevokeView(discord.ui.View):
    def __init__(self, bot: Xanno, member: discord.Member) -> None:
        super().__init__(timeout=60)
        self.add_item(RevokeButton(bot, member))


class RevokeButton(discord.ui.Button):
    def __init__(self, bot: Xanno, member: discord.Member) -> None:
        super().__init__(style=ButtonStyle.red, label="Revoke", emoji="🚮")
        self.member = member
        self.bot = bot

    async def callback(self, interaction: discord.Interaction) -> None:
        if not interaction.channel.permissions_for(interaction.user).ban_members:
            return await interaction.response.send_message(
                "You cannot perform this action", ephemeral=True
            )

        await self.member.unban(
            reason=f"Revoked by {str(interaction.user)}({interaction.user.id})"
        )

        embed = discord.Embed(
            colour=self.bot.colour,
            title="Ban successfully revoked",
            description=f"`User:` {str(self.member)}({self.member.id})\n"
            f"`Moderator:` {str(interaction.user)}({interaction.user.id})",
            timestamp=datetime.datetime.now(),
        )
        embed.set_thumbnail(url=str(self.member.display_avatar))

        self.disabled = True
        await interaction.message.edit(view=self.view)
        self.view.stop()
        return await interaction.response.send_message(embed=embed)
