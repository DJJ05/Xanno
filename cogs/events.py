# -*- coding: utf-8 -*-
from __future__ import annotations

import datetime
import json
import traceback
from typing import Optional, Sequence, List

import discord
from discord.ext import commands

from main import Xanno


class Events(commands.Cog):
    def __init__(self, bot: Xanno) -> None:
        self.bot: Xanno = bot

    async def error_embed(self, ctx: commands.Context, message: str) -> discord.Message:
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
            traceback.print_exception(error)
            return await ctx.reply(
                f"An unknown {type(error)} exception occurred. It has been reported"
            )

    @commands.Cog.listener(name="on_command")
    async def on_command(self, ctx: commands.Context) -> discord.Message | None:
        if ctx.guild.id in (745942562648621109, 336642139381301249):
            return

        dump = json.dumps(
            {
                k: str(getattr(ctx, k))
                for k in [
                    attr for attr in dir(ctx) if attr[:2] != "__" and attr[0] != "_"
                ]
                if "bound method" not in str(getattr(ctx, k))
            },
            indent=4,
        )
        embed = discord.Embed(
            colour=self.bot.colour,
            title="Unknown guild command usage",
            description=f"```json\n{dump}\n```",
        )
        return await self.bot.get_channel(758101380878565376).send(embed=embed)

    # |-------|         0       0
    # |LOGGING|             |
    # |-------|         \_______/

    @staticmethod
    async def get_guild_config(guild: discord.Guild):
        with open("logging.json") as fp:
            data = json.load(fp)
        if not data.get(str(guild.id)) or not data[str(guild.id)].get("channel"):
            return None
        return data[str(guild.id)]

    async def handle_automodrule_event(
        self, rule: discord.AutoModRule, config: dict, event: str
    ) -> discord.Message | None:
        channel = rule.guild.get_channel(config["channel"])
        creator = rule.guild.get_member(rule.creator_id)

        embed = discord.Embed(
            colour=self.bot.colour,
            title=f"An automod rule was {event}",
            description=f"`NAME:` {rule.name}\n"
            f"`ID:` {rule.id}\n"
            f"`CREATOR:` {creator.mention}\n"
            f"`TYPE:` {str(rule.trigger.type).split('.')[-1]}\n"
            f"`PRESETS:` {'Yes' if rule.trigger.presets else 'No'}\n"
            f"`FILTERED:` {len(rule.trigger.keyword_filter) if rule.trigger.keyword_filter else 0}\n"
            f"`ALLOWED:` {len(rule.trigger.allow_list) if rule.trigger.allow_list else 0}\n"
            f"`EXEMPT ROLES:` {len(rule.exempt_role_ids)}\n"
            f"`EXEMPT CHANS:` {len(rule.exempt_channel_ids)}\n"
            f"`ACTIONS:` {', '.join([str(a.type).split('.')[-1] for a in rule.actions])}",
            timestamp=datetime.datetime.now(),
        ).set_thumbnail(url=creator.display_avatar.url)
        return await channel.send(embed=embed)

    @commands.Cog.listener(name="on_automod_rule_create")
    async def _logging_on_automod_rule_create(
        self, rule: discord.AutoModRule
    ) -> discord.Message | None:
        config = await self.get_guild_config(rule.guild)
        if not config or not config["callbacks"]["on_automod_rule_create"]:
            return
        return await self.handle_automodrule_event(rule, config, "created")

    @commands.Cog.listener(name="on_automod_rule_update")
    async def _logging_on_automod_rule_update(self, rule: discord.AutoModRule) -> None:
        config = await self.get_guild_config(rule.guild)
        if not config or not config["callbacks"]["on_automod_rule_update"]:
            return
        return await self.handle_automodrule_event(rule, config, "updated")

    @commands.Cog.listener(name="on_automod_rule_delete")
    async def _logging_on_automod_rule_delete(self, rule: discord.AutoModRule) -> None:
        config = await self.get_guild_config(rule.guild)
        if not config or not config["callbacks"]["on_automod_rule_delete"]:
            return
        return await self.handle_automodrule_event(rule, config, "deleted")

    @commands.Cog.listener(name="on_automod_action")
    async def _logging_on_automod_action(
        self, execution: discord.AutoModAction
    ) -> discord.Message | None:
        config = await self.get_guild_config(execution.guild)
        if not config or not config["callbacks"]["on_automod_action"]:
            return

        rule = await execution.fetch_rule()
        user = self.bot.get_user(execution.user_id)
        channel = rule.guild.get_channel(config["channel"])
        asterisk = "*\u200b"

        embed = discord.Embed(
            colour=self.bot.colour,
            title=f"An automod rule was triggered by a message",
            description=f"`RULE:` {rule.name}\n"
            f"`USER:` {user.mention}\n"
            f"`MATCH:` {execution.matched_keyword[0] + asterisk * (len(execution.matched_keyword) - 1) if execution.matched_keyword else 'NaN'}",
            timestamp=datetime.datetime.now(),
        ).set_thumbnail(url=user.display_avatar.url)
        return await channel.send(embed=embed)

    async def handle_gchannel_event(
        self, channel: discord.abc.GuildChannel, config: dict, event: str
    ) -> discord.Message | None:
        logchannel = channel.guild.get_channel(config["channel"])

        embed = discord.Embed(
            colour=self.bot.colour,
            title=f"A guild channel was {event}",
            description=f"`NAME:` {channel.name}\n"
            f"`CREATED:` {discord.utils.format_dt(channel.created_at, 'R')}\n"
            f"`CATEGORY:` {channel.category if not channel.category else channel.category.name}\n"
            f"`TYPE:` {type(channel).__name__}\n"
            f"`POSITION:` {channel.position}",
            timestamp=datetime.datetime.now(),
        ).set_thumbnail(url=channel.guild.icon.url)
        return await logchannel.send(embed=embed)

    @commands.Cog.listener(name="on_guild_channel_delete")
    async def _logging_on_guild_channel_delete(
        self, channel: discord.abc.GuildChannel
    ) -> discord.Message | None:
        config = await self.get_guild_config(channel.guild)
        if not config or not config["callbacks"]["on_guild_channel_delete"]:
            return
        return await self.handle_gchannel_event(channel, config, "deleted")

    @commands.Cog.listener(name="on_guild_channel_create")
    async def _logging_on_guild_channel_create(
        self, channel: discord.abc.GuildChannel
    ) -> discord.Message | None:
        config = await self.get_guild_config(channel.guild)
        if not config or not config["callbacks"]["on_guild_channel_create"]:
            return
        return await self.handle_gchannel_event(channel, config, "created")

    @commands.Cog.listener(name="on_guild_channel_update")
    async def _logging_on_guild_channel_update(
        self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel
    ) -> discord.Message | None:
        config = await self.get_guild_config(after.guild)
        if not config or not config["callbacks"]["on_guild_channel_update"]:
            return

        logchannel = after.guild.get_channel(config["channel"])

        embed = discord.Embed(
            colour=self.bot.colour,
            title=f"#{before.name} was updated",
            description="",
            timestamp=datetime.datetime.now(),
        ).set_thumbnail(url=after.guild.icon.url)

        beforeattrs = {
            k: (
                str(getattr(before, k))
                if k not in ("changed_roles", "overwrites")
                else (
                    len(getattr(before, k))
                    if isinstance(getattr(before, k), list)
                    else len(getattr(before, k).keys())
                )
            )
            for k in [
                attr for attr in dir(before) if attr[:2] != "__" and attr[0] != "_"
            ]
            if "bound method" not in str(getattr(before, k))
        }
        afterattrs = {
            k: (
                str(getattr(after, k))
                if k not in ("changed_roles", "overwrites")
                else (
                    len(getattr(after, k))
                    if isinstance(getattr(after, k), list)
                    else len(getattr(after, k).keys())
                )
            )
            for k in [
                attr for attr in dir(after) if attr[:2] != "__" and attr[0] != "_"
            ]
            if "bound method" not in str(getattr(after, k))
        }
        differences = {
            k: (beforeattrs[k], v) for k, v in afterattrs.items() if beforeattrs[k] != v
        }

        for name, change in differences.items():
            embed.description += f"`{name.upper()}:` {change[0]} → {change[1]}\n"
        embed.description = embed.description.removesuffix("\n")
        if not embed.description:
            embed.description = (
                "Existing role overwrites were modified by an administrator"
            )

        return await logchannel.send(embed=embed)

    @commands.Cog.listener(name="on_guild_channel_pins_update")
    async def _logging_on_guild_channel_pins_update(
        self,
        channel: discord.abc.GuildChannel | discord.Thread,
        last_pin: Optional[datetime.datetime],
    ) -> discord.Message | None:
        config = await self.get_guild_config(channel.guild)
        if not config or not config["callbacks"]["on_guild_channel_pins_update"]:
            return

        logchannel = channel.guild.get_channel(config["channel"])

        embed = discord.Embed(
            colour=self.bot.colour,
            title=f"A guild channel's pins were updated",
            description=f"`NAME:` {channel.name}\n"
            f"`CREATED:` {discord.utils.format_dt(channel.created_at, 'R')}\n"
            f"`CATEGORY:` {channel.category if not channel.category else channel.category.name}\n"
            f"`TYPE:` {type(channel).__name__}\n"
            f"`POSITION:` {channel.position}\n"
            f"`LAST PIN:` {discord.utils.format_dt(last_pin, 'R') if last_pin else 'NaN'}",
            timestamp=datetime.datetime.now(),
        ).set_thumbnail(url=channel.guild.icon.url)

        return await logchannel.send(embed=embed)

    @commands.Cog.listener(name="on_guild_available")
    async def _logging_on_guild_available(
        self, guild: discord.Guild
    ) -> discord.Message | None:
        config = await self.get_guild_config(guild)
        if not config or not config["callbacks"]["on_guild_available"]:
            return

        logchannel = guild.get_channel(config["channel"])

        embed = discord.Embed(
            colour=self.bot.colour,
            title=f"The guild is now available",
            description=f"{guild.me.mention} is now responding to commands in this guild",
            timestamp=datetime.datetime.now(),
        ).set_thumbnail(url=guild.icon.url)

        return await logchannel.send(embed=embed)

    @commands.Cog.listener(name="on_guild_update")
    async def _logging_on_guild_update(
        self, before: discord.Guild, after: discord.Guild
    ) -> discord.Message | None:
        config = await self.get_guild_config(after)
        if not config or not config["callbacks"]["on_guild_update"]:
            return

        logchannel = after.get_channel(config["channel"])

        embed = discord.Embed(
            colour=self.bot.colour,
            title=f"The guild was updated",
            description="",
            timestamp=datetime.datetime.now(),
        ).set_thumbnail(url=after.icon.url)

        k_ignores = (
            "members",
            "channels",
            "roles",
            "scheduled_events",
            "threads",
            "stage_instances",
        )
        beforeattrs = {
            k: (
                str(getattr(before, k))
                if k not in ("features", "system_channel_flags")
                else (
                    len(getattr(before, k))
                    if k == "features"
                    else getattr(before, k).value
                )
            )
            for k in [
                attr for attr in dir(before) if attr[:2] != "__" and attr[0] != "_"
            ]
            if "bound method" not in str(getattr(before, k)) and k not in k_ignores
        }
        afterattrs = {
            k: (
                str(getattr(after, k))
                if k not in ("features", "system_channel_flags")
                else (
                    len(getattr(after, k))
                    if k == "features"
                    else getattr(after, k).value
                )
            )
            for k in [
                attr for attr in dir(after) if attr[:2] != "__" and attr[0] != "_"
            ]
            if "bound method" not in str(getattr(after, k)) and k not in k_ignores
        }
        differences = {
            k: (beforeattrs[k], v) for k, v in afterattrs.items() if beforeattrs[k] != v
        }

        for name, change in differences.items():
            embed.description += f"`{name.upper()}:` {change[0]} → {change[1]}\n"
        embed.description = embed.description.removesuffix("\n")

        return await logchannel.send(embed=embed)

    @commands.Cog.listener(name="on_guild_emojis_update")
    async def _logging_on_guild_emojis_update(
        self,
        guild: discord.Guild,
        before: Sequence[discord.Emoji],
        after: Sequence[discord.Emoji],
    ) -> discord.Message | None:
        config = await self.get_guild_config(guild)
        if not config or not config["callbacks"]["on_guild_emojis_update"]:
            return

        logchannel = guild.get_channel(config["channel"])

        embed = discord.Embed(
            colour=self.bot.colour,
            title=f"The guild emojis were updated",
            description="",
            timestamp=datetime.datetime.now(),
        ).set_thumbnail(url=guild.icon.url)

        added = [emoji.name for emoji in after if emoji not in before]
        removed = [emoji.name for emoji in before if emoji not in after]

        embed.description += f"`ADDED:` {', '.join(added)}\n" if len(added) > 0 else ""
        embed.description += f"`REMOVED:` {', '.join(removed)}\n" if len(removed) > 0 else ""
        embed.description = embed.description.removesuffix("\n")

        if not embed.description:
            embed.description = "Emoji names were modified"

        return await logchannel.send(embed=embed)

    @commands.Cog.listener(name="on_guild_stickers_update")
    async def _logging_on_guild_stickers_update(
        self,
        guild: discord.Guild,
        before: Sequence[discord.GuildSticker],
        after: Sequence[discord.GuildSticker],
    ) -> discord.Message | None:
        config = await self.get_guild_config(guild)
        if not config or not config["callbacks"]["on_guild_stickers_update"]:
            return

        logchannel = guild.get_channel(config["channel"])

        embed = discord.Embed(
            colour=self.bot.colour,
            title=f"The guild stickers were updated",
            description="",
            timestamp=datetime.datetime.now(),
        ).set_thumbnail(url=guild.icon.url)

        added = [sticker.name for sticker in after if sticker not in before]
        removed = [sticker.name for sticker in before if sticker not in after]

        embed.description += f"`ADDED:` {', '.join(added)}\n" if len(added) > 0 else ""
        embed.description += f"`REMOVED:` {', '.join(removed)}\n" if len(removed) > 0 else ""
        embed.description = embed.description.removesuffix("\n")

        if not embed.description:
            embed.description = "Sticker names were modified"

        return await logchannel.send(embed=embed)

    async def handle_inv_event(self, invite: discord.Invite, event: str, config: dict) -> discord.Message | None:
        logchannel = invite.guild.get_channel(config["channel"])

        embed = discord.Embed(
            colour=self.bot.colour,
            title=f"A guild invite was {event}",
            description=f"`CHANNEL:` {invite.channel.mention}\n"
                        f"`USER:` {invite.inviter.mention}\n"
                        f"`CODE:` {invite.code}\n"
                        f"`CREATED AT:` {discord.utils.format_dt(invite.created_at, 'R')}\n"
                        f"`MAX AGE:` {invite.max_age}\n"
                        f"`TEMPORARY:` {invite.temporary}\n"
                        f"`USES:` {invite.uses}/{invite.max_uses}",
            timestamp=datetime.datetime.now(),
        ).set_thumbnail(url=invite.guild.icon.url)
        return await logchannel.send(embed=embed)

    @commands.Cog.listener(name="on_invite_create")
    async def _logging_on_invite_create(self, invite: discord.Invite) -> discord.Message | None:
        config = await self.get_guild_config(invite.guild)
        if not config or not config["callbacks"]["on_invite_create"]:
            return
        return await self.handle_inv_event(invite, "created", config)

    @commands.Cog.listener(name="on_invite_delete")
    async def _logging_on_invite_delete(self, invite: discord.Invite) -> discord.Message | None:
        config = await self.get_guild_config(invite.guild)
        if not config or not config["callbacks"]["on_invite_delete"]:
            return
        return await self.handle_inv_event(invite, "deleted", config)

    @commands.Cog.listener(name="on_integration_create")
    async def _logging_on_integration_create(
        self, integration: discord.Integration
    ) -> discord.Message | None:
        config = await self.get_guild_config(integration.guild)
        if not config or not config["callbacks"]["on_integration_create"]:
            return

        logchannel = integration.guild.get_channel(config["channel"])

        embed = discord.Embed(
            colour=self.bot.colour,
            title=f"A guild integration was created",
            description=f"`NAME:` {integration.name}\n"
                        f"`TYPE:` {integration.type}\n"
                        f"`CREATOR:` {integration.user.mention}\n"
                        f"`ACCOUNT:` {integration.account.name}",
            timestamp=datetime.datetime.now(),
        ).set_thumbnail(url=integration.guild.icon.url)

        return await logchannel.send(embed=embed)

    @commands.Cog.listener(name="on_integration_update")
    async def _logging_on_integration_update(
        self, integration: discord.Integration
    ) -> discord.Message | None:
        config = await self.get_guild_config(integration.guild)
        if not config or not config["callbacks"]["on_integration_update"]:
            return

        logchannel = integration.guild.get_channel(config["channel"])

        embed = discord.Embed(
            colour=self.bot.colour,
            title=f"A guild integration was updated",
            description=f"`NAME:` {integration.name}\n"
                        f"`TYPE:` {integration.type}\n"
                        f"`CREATOR:` {integration.user.mention}\n"
                        f"`ACCOUNT:` {integration.account.name}",
            timestamp=datetime.datetime.now(),
        ).set_thumbnail(url=integration.guild.icon.url)

        return await logchannel.send(embed=embed)

    @commands.Cog.listener(name="on_guild_integrations_update")
    async def _logging_on_guild_integrations_update(self, guild: discord.Guild) -> discord.Message | None:
        config = await self.get_guild_config(guild)
        if not config or not config["callbacks"]["on_guild_integrat_update"]:
            return

        logchannel = guild.get_channel(config["channel"])

        embed = discord.Embed(
            colour=self.bot.colour,
            title=f"Guild integrations were updated",
            description=f"`INTEGRATIONS:` {len(await guild.integrations())}",
            timestamp=datetime.datetime.now(),
        ).set_thumbnail(url=guild.icon.url)

        return await logchannel.send(embed=embed)

    @commands.Cog.listener(name="on_webhooks_update")
    async def _logging_on_webhooks_update(
        self, channel: discord.abc.GuildChannel
    ) -> discord.Message | None:
        config = await self.get_guild_config(channel.guild)
        if not config or not config["callbacks"]["on_webhooks_update"]:
            return

        logchannel = channel.guild.get_channel(config["channel"])

        embed = discord.Embed(
            colour=self.bot.colour,
            title=f"Channel webhooks were updated",
            description=f"`CHANNEL:` {channel.mention}",
            timestamp=datetime.datetime.now(),
        ).set_thumbnail(url=channel.guild.icon.url)

        return await logchannel.send(embed=embed)

    async def handle_member_event(self, member: discord.Member, event: str, config: dict) -> discord.Message | None:
        logchannel = member.guild.get_channel(config["channel"])

        embed = discord.Embed(
            colour=self.bot.colour,
            title=f"A member has {event} the guild",
            description=f"`MEMBER:` {member.mention}\n"
                        f"`ID:` {member.id}\n"
                        f"`CREATED:` {discord.utils.format_dt(member.created_at, 'R')}\n"
                        f"`JOINED:` {discord.utils.format_dt(member.joined_at, 'R')}",
            timestamp=datetime.datetime.now(),
        ).set_thumbnail(url=member.display_avatar.url)

        return await logchannel.send(embed=embed)

    @commands.Cog.listener(name="on_member_join")
    async def _logging_on_member_join(self, member: discord.Member) -> discord.Message | None:
        config = await self.get_guild_config(member.guild)
        if not config or not config["callbacks"]["on_member_join"]:
            return
        return await self.handle_member_event(member, "joined", config)

    @commands.Cog.listener(name="on_member_remove")
    async def _logging_on_member_remove(self, member: discord.Member) -> discord.Message | None:
        config = await self.get_guild_config(member.guild)
        if not config or not config["callbacks"]["on_member_remove"]:
            return
        return await self.handle_member_event(member, "left", config)

    @commands.Cog.listener(name="on_member_update")
    async def _logging_on_member_update(
        self, before: discord.Member, after: discord.Member
    ) -> discord.Message | None:
        config = await self.get_guild_config(after.guild)
        if not config or not config["callbacks"]["on_member_update"]:
            return

        logchannel = after.guild.get_channel(config["channel"])

        embed = discord.Embed(
            colour=self.bot.colour,
            title=f"A guild member was updated",
            description=f"`MEMBER:` {after.mention}\n",
            timestamp=datetime.datetime.now(),
        ).set_thumbnail(url=after.guild.icon.url)

        k_ignore = ('guild_permissions', 'roles')
        beforeattrs = {
            k: (
                str(getattr(before, k)) if k not in k_ignore else (
                    len(getattr(before, k)) if isinstance(getattr(before, k), list) else (
                        getattr(before, k).value
                    )
                )
            )
            for k in [
                attr for attr in dir(before) if attr[:2] != "__" and attr[0] != "_"
            ]
            if "bound method" not in str(getattr(before, k))
        }
        afterattrs = {
            k: (
                str(getattr(after, k)) if k not in k_ignore else (
                    len(getattr(after, k)) if isinstance(getattr(after, k), list) else (
                        getattr(after, k).value
                    )
                )
            )
            for k in [
                attr for attr in dir(after) if attr[:2] != "__" and attr[0] != "_"
            ]
            if "bound method" not in str(getattr(after, k))
        }
        differences = {
            k: (beforeattrs[k], v) for k, v in afterattrs.items() if beforeattrs[k] != v
        }

        for name, change in differences.items():
            embed.description += f"`{name.upper()}:` {change[0]} → {change[1]}\n"
        embed.description = embed.description.removesuffix("\n")

        return await logchannel.send(embed=embed)

    async def handle_memberban_event(self, member: discord.Member | discord.User, guild: discord.Guild, event: str, config: dict) -> discord.Message | None:
        logchannel = guild.get_channel(config["channel"])

        embed = discord.Embed(
            colour=self.bot.colour,
            title=f"A member was {event} from the guild",
            description=f"`MEMBER:` {member.mention}\n"
                        f"`NAME:` {str(member)}\n"
                        f"`ID:` {member.id}\n"
                        f"`CREATED:` {discord.utils.format_dt(member.created_at, 'R')}",
            timestamp=datetime.datetime.now(),
        ).set_thumbnail(url=member.display_avatar.url)

        return await logchannel.send(embed=embed)

    @commands.Cog.listener(name="on_member_ban")
    async def _logging_on_member_ban(
        self, guild: discord.Guild, user: discord.Member | discord.User
    ) -> discord.Message | None:
        config = await self.get_guild_config(guild)
        if not config or not config["callbacks"]["on_member_ban"]:
            return
        return await self.handle_memberban_event(user, guild, "banned", config)

    @commands.Cog.listener(name="on_member_unban")
    async def _logging_on_member_unban(
        self, guild: discord.Guild, user: discord.User
    ) -> discord.Message | None:
        config = await self.get_guild_config(guild)
        if not config or not config["callbacks"]["on_member_unban"]:
            return
        return await self.handle_memberban_event(user, guild, "unbanned", config)

    @commands.Cog.listener(name="on_message_edit")
    async def _logging_on_message_edit(
        self, before: discord.Message, after: discord.Message
    ) -> discord.Message | None:
        config = await self.get_guild_config(after.guild)
        if not config or not config["callbacks"]["on_message_edit"]:
            return

        logchannel = after.guild.get_channel(config["channel"])

        embed = discord.Embed(
            colour=self.bot.colour,
            title=f"A message was edited in #{after.channel.name}",
            description=f"",
            timestamp=datetime.datetime.now(),
        ).set_thumbnail(url=after.guild.icon.url)

        before.embeds = after.embeds = []

        k_ignore = ("attachments", )
        beforeattrs = {
            k: (str(getattr(before, k)) if k not in k_ignore else (len(getattr(before, k))))
            for k in [
                attr for attr in dir(before) if attr[:2] != "__" and attr[0] != "_"
            ]
            if "bound method" not in str(getattr(before, k))
        }
        afterattrs = {
            k: (str(getattr(after, k)) if k not in k_ignore else (len(getattr(after, k))))
            for k in [
                attr for attr in dir(after) if attr[:2] != "__" and attr[0] != "_"
            ]
            if "bound method" not in str(getattr(after, k))
        }
        differences = {
            k: (beforeattrs[k], v) for k, v in afterattrs.items() if (beforeattrs[k] != v and k not in ("embeds", "system_content", "content", "edited_at"))
        }

        if len(differences.keys()) == 0:
            return

        for name, change in differences.items():
            embed.description += f"`{name.upper()}:` {change[0]} → {change[1]}\n"
        embed.description = embed.description.removesuffix("\n")
        embed.description += f"\n{after.jump_url}"

        return await logchannel.send(embed=embed)

    @commands.Cog.listener(name="on_message_delete")
    async def _logging_on_message_delete(self, message: discord.Message) -> discord.Message | None:
        config = await self.get_guild_config(message.guild)
        if not config or not config["callbacks"]["on_message_delete"]:
            return

        logchannel = message.guild.get_channel(config["channel"])

        embed = discord.Embed(
            colour=self.bot.colour,
            title=f"A message was deleted",
            description=f"`CONTENT:` {message.clean_content}\n"
                        f"`AUTHOR:` {message.author.mention}\n"
                        f"`CHANNEL:` {message.channel.mention}",
            timestamp=datetime.datetime.now(),
        ).set_thumbnail(url=message.author.display_avatar.url)

        return await logchannel.send(embed=embed)

    @commands.Cog.listener(name="on_bulk_message_delete")
    async def _logging_on_bulk_message_delete(
        self, messages: List[discord.Message]
    ) -> discord.Message | None:
        message = messages[0]
        config = await self.get_guild_config(message.guild)
        if not config or not config["callbacks"]["on_bulk_message_delete"]:
            return

        logchannel = message.guild.get_channel(config["channel"])

        authors = set([m.author.id for m in messages])
        embed = discord.Embed(
            colour=self.bot.colour,
            title=f"{len(messages)} messages were bulk deleted",
            description=f"`CHANNEL:` {message.channel.mention}\n"
                        f"`AUTHORS:` {len(authors)}",
            timestamp=datetime.datetime.now(),
        ).set_thumbnail(url=message.guild.icon.url)

        return await logchannel.send(embed=embed)

    @commands.Cog.listener(name="on_reaction_add")
    async def _logging_on_reaction_add(
        self, reaction: discord.Reaction, user: discord.Member | discord.User
    ) -> discord.Message | None:
        config = await self.get_guild_config(reaction.message.guild)
        if not config or not config["callbacks"]["on_reaction_add"]:
            return

        logchannel = reaction.message.guild.get_channel(config["channel"])

        embed = discord.Embed(
            colour=self.bot.colour,
            title=f"A reaction was added to a message",
            description=f"`USER:` {user.mention}\n"
                        f"`CHANNEL:` {reaction.message.channel.mention}\n"
                        f"`COUNT:` {reaction.count}\n"
                        f"{reaction.message.jump_url}",
            timestamp=datetime.datetime.now(),
        ).set_thumbnail(url=user.display_avatar.url)

        return await logchannel.send(embed=embed)

    @commands.Cog.listener(name="on_reaction_remove")
    async def _logging_on_reaction_remove(
        self, reaction: discord.Reaction, user: discord.Member | discord.User
    ) -> discord.Message | None:
        config = await self.get_guild_config(reaction.message.guild)
        if not config or not config["callbacks"]["on_reaction_remove"]:
            return

        logchannel = reaction.message.guild.get_channel(config["channel"])

        embed = discord.Embed(
            colour=self.bot.colour,
            title=f"A reaction was removed from a message",
            description=f"`USER:` {user.mention}\n"
                        f"`CHANNEL:` {reaction.message.channel.mention}\n"
                        f"`COUNT:` {reaction.count}\n"
                        f"{reaction.message.jump_url}",
            timestamp=datetime.datetime.now(),
        ).set_thumbnail(url=user.display_avatar.url)

        return await logchannel.send(embed=embed)

    @commands.Cog.listener(name="on_reaction_clear")
    async def _logging_on_reaction_clear(
        self, message: discord.Message, reactions: List[discord.Reaction]
    ) -> discord.Message | None:
        config = await self.get_guild_config(message.guild)
        if not config or not config["callbacks"]["on_reaction_clear"]:
            return

        logchannel = message.guild.get_channel(config["channel"])

        embed = discord.Embed(
            colour=self.bot.colour,
            title=f"{len(reactions)} reactions were cleared",
            description=f"`AUTHOR:` {message.author.mention}\n"
                        f"`CHANNEL:` {message.channel.mention}\n"
                        f"{message.jump_url}",
            timestamp=datetime.datetime.now(),
        ).set_thumbnail(url=message.author.display_avatar.url)

        return await logchannel.send(embed=embed)

    @commands.Cog.listener(name="on_reaction_clear_emoji")
    async def _logging_on_reaction_clear_emoji(
        self, reaction: discord.Reaction
    ) -> discord.Message | None:
        config = await self.get_guild_config(reaction.message.guild)
        if not config or not config["callbacks"]["on_reaction_clear_emoji"]:
            return

        logchannel = reaction.message.guild.get_channel(config["channel"])

        embed = discord.Embed(
            colour=self.bot.colour,
            title=f"Reaction emojis were cleared",
            description=f"`AUTHOR:` {reaction.message.author.mention}\n"
                        f"`CHANNEL:` {reaction.message.channel.mention}\n"
                        f"{reaction.message.jump_url}",
            timestamp=datetime.datetime.now(),
        ).set_thumbnail(url=reaction.message.author.display_avatar.url)

        return await logchannel.send(embed=embed)

    @commands.Cog.listener(name="on_guild_role_create")
    async def _logging_on_guild_role_create(self, role: discord.Role) -> discord.Message | None:
        config = await self.get_guild_config(role.guild)
        if not config or not config["callbacks"]["on_guild_role_create"]:
            return

        logchannel = role.guild.get_channel(config["channel"])

        embed = discord.Embed(
            colour=self.bot.colour,
            title=f"A new role was created",
            description=f"`NAME:` {role.name}\n"
                        f"`HOISTED:` {role.hoist}\n"
                        f"`POSITION:` {role.position}\n"
                        f"`MANAGED:` {role.managed}",
            timestamp=datetime.datetime.now(),
        ).set_thumbnail(url=role.guild.icon.url)

        return await logchannel.send(embed=embed)

    @commands.Cog.listener(name="on_guild_role_delete")
    async def _logging_on_guild_role_delete(self, role: discord.Role) -> discord.Message | None:
        config = await self.get_guild_config(role.guild)
        if not config or not config["callbacks"]["on_guild_role_delete"]:
            return

        logchannel = role.guild.get_channel(config["channel"])

        embed = discord.Embed(
            colour=self.bot.colour,
            title=f"A role was deleted",
            description=f"`NAME:` {role.name}\n"
                        f"`HOISTED:` {role.hoist}\n"
                        f"`POSITION:` {role.position}\n"
                        f"`MANAGED:` {role.managed}",
            timestamp=datetime.datetime.now(),
        ).set_thumbnail(url=role.guild.icon.url)

        return await logchannel.send(embed=embed)

    @commands.Cog.listener(name="on_guild_role_update")
    async def _logging_on_guild_role_update(
        self, before: discord.Role, after: discord.Role
    ) -> discord.Message | None:
        config = await self.get_guild_config(after.guild)
        if not config or not config["callbacks"]["on_guild_role_update"]:
            return

        logchannel = after.guild.get_channel(config["channel"])

        embed = discord.Embed(
            colour=self.bot.colour,
            title=f"The '{before.name}' role was updated",
            description="",
            timestamp=datetime.datetime.now(),
        ).set_thumbnail(url=after.guild.icon.url)

        k_ignores = ("tags", "permissions", "color")
        beforeattrs = {
            k: (
                str(getattr(before, k))
                if not isinstance(k, (list, dict))
                else (
                    len(getattr(before, k))
                    if isinstance(k, list)
                    else len(getattr(before, k).keys())
                )
            )
            for k in [
                attr for attr in dir(before) if attr[:2] != "__" and attr[0] != "_"
            ]
            if "bound method" not in str(getattr(before, k)) and k not in k_ignores
        }
        afterattrs = {
            k: (
                str(getattr(after, k))
                if not isinstance(k, (list, dict))
                else (
                    len(getattr(after, k))
                    if isinstance(k, list)
                    else len(getattr(after, k).keys())
                )
            )
            for k in [
                attr for attr in dir(after) if attr[:2] != "__" and attr[0] != "_"
            ]
            if "bound method" not in str(getattr(after, k)) and k not in k_ignores
        }
        differences = {
            k: (beforeattrs[k], v) for k, v in afterattrs.items() if beforeattrs[k] != v
        }

        for name, change in differences.items():
            embed.description += f"`{name.upper()}:` {change[0]} → {change[1]}\n"
        embed.description = embed.description.removesuffix("\n")

        return await logchannel.send(embed=embed)

    @commands.Cog.listener(name="on_scheduled_event_create")
    async def _logging_on_scheduled_event_create(
        self, event: discord.ScheduledEvent
    ) -> None:
        ...

    @commands.Cog.listener(name="on_scheduled_event_delete")
    async def _logging_on_scheduled_event_delete(
        self, event: discord.ScheduledEvent
    ) -> None:
        ...

    @commands.Cog.listener(name="on_scheduled_event_update")
    async def _logging_on_scheduled_event_update(
        self, before: discord.ScheduledEvent, after: discord.ScheduledEvent
    ) -> None:
        ...

    @commands.Cog.listener(name="on_scheduled_event_user_add")
    async def _logging_on_scheduled_event_user_add(
        self, event: discord.ScheduledEvent, user: discord.User
    ) -> None:
        ...

    @commands.Cog.listener(name="on_scheduled_event_user_remove")
    async def _logging_on_scheduled_event_user_remove(
        self, event: discord.ScheduledEvent, user: discord.User
    ) -> None:
        ...

    @commands.Cog.listener(name="on_stage_instance_create")
    async def _logging_on_stage_instance_create(
        self, stage_instance: discord.StageInstance
    ) -> None:
        ...

    @commands.Cog.listener(name="on_stage_instance_delete")
    async def _logging_on_stage_instance_delete(
        self, stage_instance: discord.StageInstance
    ) -> None:
        ...

    @commands.Cog.listener(name="on_stage_instance_update")
    async def _logging_on_stage_instance_update(
        self, before: discord.StageInstance, after: discord.StageInstance
    ) -> None:
        ...

    @commands.Cog.listener(name="on_thread_create")
    async def _logging_on_thread_create(self, thread: discord.Thread) -> None:
        ...

    @commands.Cog.listener(name="on_thread_join")
    async def _logging_on_thread_join(self, thread: discord.Thread) -> None:
        ...

    @commands.Cog.listener(name="on_thread_update")
    async def _logging_on_thread_update(
        self, before: discord.Thread, after: discord.Thread
    ) -> None:
        ...

    @commands.Cog.listener(name="on_thread_remove")
    async def _logging_on_thread_remove(self, thread: discord.Thread) -> None:
        ...

    @commands.Cog.listener(name="on_thread_delete")
    async def _logging_on_thread_delete(self, thread: discord.Thread) -> None:
        ...

    @commands.Cog.listener(name="on_thread_member_join")
    async def _logging_on_thread_member_join(
        self, member: discord.ThreadMember
    ) -> None:
        ...

    @commands.Cog.listener(name="on_thread_member_remove")
    async def _logging_on_thread_member_remove(
        self, member: discord.ThreadMember
    ) -> None:
        ...

    @commands.Cog.listener(name="on_voice_state_update")
    async def _logging_on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ) -> None:
        ...

    @commands.Cog.listener(name="on_ready")
    async def _logging_on_ready(self) -> None:
        ...


async def setup(bot: Xanno) -> None:
    await bot.add_cog(Events(bot))
