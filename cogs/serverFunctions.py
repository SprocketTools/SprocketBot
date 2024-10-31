import random

import discord
from discord.ext import commands

import main
from cogs.discordUIfunctions import discordUIfunctions
from cogs.errorFunctions import errorFunctions

promptResponses = {}
from discord import app_commands
from cogs.textTools import textTools
from cogs.adminFunctions import adminFunctions
from cogs.SQLfunctions import SQLfunctions
class serverFunctions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="setupModerationDatabase", description="generate a key that can be used to initiate a campaign")
    async def setupModerationDatabase(self, ctx: commands.Context):
        if ctx.author.id != main.ownerID:
            await errorFunctions.sendCategorizedError(ctx, "campaign")
            return
        await SQLfunctions.databaseExecute('''CREATE TABLE IF NOT EXISTS modrules (serverid BIGINT, name VARCHAR, description VARCHAR, points INT);''')
        await SQLfunctions.databaseExecute('''CREATE TABLE IF NOT EXISTS modlogs (serverid BIGINT, userID BIGINT, name VARCHAR, description VARCHAR, points INT, timestamp TIMESTAMP, type VARCHAR);''')
        await ctx.send("## Done!")

    @commands.command(name="addModRule", description="Add a moderation rule or subrule")
    async def addModRule(self, ctx: commands.Context):
        if ctx.author.id != main.ownerID:
            await errorFunctions.sendCategorizedError(ctx, "insult")
            return
        serverid = ctx.guild.id
        ruleName = await textTools.getCappedResponse(ctx, '''What do you want the name of the rule to be?''', 32)
        ruleDesc = await textTools.getCappedResponse(ctx,'''Reply with a short description of the rule.''',128)
        pointCount = await textTools.getFlooredIntResponse(ctx,'''How many points do you want this rule to be worth?''',0)
        await SQLfunctions.databaseExecuteDynamic('''INSERT INTO modrules VALUES ($1, $2, $3, $4);''', [serverid, ruleName, ruleDesc, pointCount])
        await ctx.send("## Done!")

    @commands.command(name="warn", description="Add a moderation rule or subrule")
    async def warn(self, ctx: commands.Context):
        if ctx.author.id != main.ownerID:
            await errorFunctions.sendCategorizedError(ctx, "insult")
            return
        data = await SQLfunctions.databaseFetchdictDynamic('''SELECT name, points FROM modrules WHERE serverid = $1;''', [ctx.guild.id])
        dataOut = []
        for rule in data:
            dataOut.append(rule["name"])
        await ctx.send("Select the applicable rule violation")
        ruleName = await discordUIfunctions.getButtonChoice(ctx, dataOut)
        data = (await SQLfunctions.databaseFetchrowDynamic('''SELECT points FROM modrules WHERE serverid = $1 AND name = $2;''',[ctx.guild.id, ruleName]))
        points = data['points']
        await ctx.send(f'This is worth {points} points.')

    @app_commands.command(name="roll", description="🎲 roll a dice")
    async def roll(self, interaction):
        result = random.randint(1, 6)
        embed = discord.Embed(
            title="🎲 Dice Roll",
            description=f"**Result:** You rolled a `{result}`!",
            color=discord.Color.blurple()
        )
        await interaction.response.send_message(embed=embed)





async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(serverFunctions(bot))