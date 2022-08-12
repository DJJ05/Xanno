# -*- coding: utf-8 -*-
import datetime

import discord.ui
from discord import ButtonStyle

from main import Xanno


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
            return await interaction.response.send_message("You cannot perform this action", ephemeral=True)

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
        return await interaction.response.send_message(embed=embed)
