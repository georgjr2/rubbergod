import discord
from discord.ext import commands

import utils
from config import messages, config
from features import karma, reaction
from repository import karma_repo
from cogs import room_check


karma_r = karma_repo.KarmaRepository()
config = config.Config
messages = messages.Messages


class Karma(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.karma = karma.Karma(bot, karma_r)
        self.check = room_check.RoomCheck(bot)
        self.reaction = reaction.Reaction(bot, karma_r)

    @commands.Cog.listener()
    async def on_message(self, message):

        if message.author.bot:
            return

        if message.content.startswith(config.role_string) or\
           message.channel.id in config.role_channels:
            role_data = await self.reaction.get_join_role_data(message)
            await self.reaction.message_role_reactions(message, role_data)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        await self.reaction.add(payload)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        await self.reaction.remove(payload)

    @commands.cooldown(rate=5, per=30.0, type=commands.BucketType.user)
    @commands.command(name="karma")
    async def pick_karma_command(self, ctx, *args):
        karma = self.karma
        if len(args) == 0:
            await ctx.send(karma.karma_get(ctx.author))
            await self.check.botroom_check(ctx.message)

        elif args[0] == "stalk":
            try:
                converter = commands.MemberConverter()
                target_member = await converter.convert(
                        ctx=ctx, argument=' '.join(args[1:]))
            except commands.errors.BadArgument:
                await ctx.send(
                    messages.member_not_found
                    .format(user=utils.generate_mention(ctx.author.id)))
                return

            await ctx.send(karma.karma_get(ctx.author, target_member))
            await self.check.botroom_check(ctx.message)

        elif args[0] == "get":
            if not await self.check.guild_check(ctx.message):
                await ctx.send(
                    "{}".format(messages.server_warning))
            else:
                try:
                    await karma.emoji_get_value(ctx.message)
                    await self.check.botroom_check(ctx.message)
                except discord.errors.Forbidden:
                    return

        elif args[0] == "revote":
            if not await self.check.guild_check(ctx.message):
                await ctx.send(
                    "{}".format(messages.server_warning))
            else:
                if ctx.message.channel.id == config.vote_room or \
                   ctx.author.id == config.admin_id:
                    try:
                        await ctx.message.delete()
                        await karma.emoji_revote_value(ctx.message)
                    except discord.errors.Forbidden:
                        return
                else:
                    await ctx.send(
                        messages.vote_room_only
                        .format(room=discord.utils.get(ctx.guild.channels,
                                                       id=config.vote_room)))

        elif args[0] == "vote":
            if not await self.check.guild_check(ctx.message):
                await ctx.send(
                    "{}".format(messages.server_warning))
            else:
                if ctx.message.channel.id == config.vote_room or \
                   ctx.author.id == config.admin_id:
                    try:
                        await ctx.message.delete()
                        await karma.emoji_vote_value(ctx.message)
                    except discord.errors.Forbidden:
                        return
                else:
                    await ctx.send(
                        messages.vote_room_only
                        .format(room=discord.utils.get(ctx.guild.channels,
                                                       id=config.vote_room)))

        elif args[0] == "give":
            if ctx.author.id == config.admin_id:
                await karma.karma_give(ctx.message)
            else:
                await ctx.send(
                    messages.insufficient_rights
                    .format(user=utils.generate_mention(ctx.author.id)))
        else:
            await ctx.send(
                messages.karma_invalid_command
                .format(utils.generate_mention(ctx.author.id)))

    @commands.cooldown(rate=2, per=30.0, type=commands.BucketType.user)
    @commands.command()
    async def leaderboard(self, ctx):
        await self.karma.leaderboard(ctx.message.channel, 'get', 'DESC')
        await self.check.botroom_check(ctx.message)

    @commands.cooldown(rate=2, per=30.0, type=commands.BucketType.user)
    @commands.command()
    async def bajkarboard(self, ctx):
        await self.karma.leaderboard(ctx.message.channel, 'get', 'ASC')
        await self.check.botroom_check(ctx.message)

    @commands.cooldown(rate=2, per=30.0, type=commands.BucketType.user)
    @commands.command()
    async def givingboard(self, ctx):
        await self.karma.leaderboard(ctx.message.channel, 'give', 'DESC')
        await self.check.botroom_check(ctx.message)

    @commands.cooldown(rate=2, per=30.0, type=commands.BucketType.user)
    @commands.command()
    async def ishaboard(self, ctx):
        await self.karma.leaderboard(ctx.message.channel, 'give', 'ASC')
        await self.check.botroom_check(ctx.message)


def setup(bot):
    bot.add_cog(Karma(bot))
