import asyncio
from discord.ext import tasks

import discord
from discord.ext import commands

import main
from datetime import datetime, timedelta
from cogs.discordUIfunctions import discordUIfunctions
from cogs.errorFunctions import errorFunctions

promptResponses = {}
from discord import app_commands
from cogs.textTools import textTools
from cogs.adminFunctions import adminFunctions
from cogs.SQLfunctions import SQLfunctions
class roleColorTools(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.startup = True
        self.updateFrequency = 300
        self.startupdelay = 10800
        self.updateRoles.start()

    @tasks.loop(seconds=300)
    async def updateRoles(self):
        await roleColorTools.roleUpdater(self)

    @commands.command(name="updateColorChangers",description="Update the color changers by force")
    async def updateColorChangers(self, ctx: commands.Context):
        try:
            self.startup = False
            await roleColorTools.roleUpdater(self)
            self.startup = True
            print("test")
            await ctx.send("## Done!")
        except Exception as e:
            await ctx.send(f"{e}")

    async def roleUpdater(self):
        if self.startup == True:
            await asyncio.sleep(self.startupdelay)
            self.startup = False
        else:
            colorData = await SQLfunctions.databaseFetchdict('''SELECT * FROM colorchangers WHERE rainbow = true;''')
            for colorInstance in colorData:
                server = self.bot.get_guild(colorInstance['serverid'])
                role = discord.utils.get(server.roles, id=colorInstance['roleid'])
                colorout = discord.Color.from_hsv(min(colorInstance['percent'], 1), 1, 1)
                await role.edit(color=colorout)
                percentInceease = self.updateFrequency/(60*colorInstance['duration'])
                await SQLfunctions.databaseExecuteDynamic('''UPDATE colorchangers SET percent = percent + $1 WHERE roleid = $2;''', [percentInceease, colorInstance['roleid']])
            await SQLfunctions.databaseExecute('''UPDATE colorchangers SET percent = 0 WHERE rainbow = true AND percent > 1;''')

            colorData = await SQLfunctions.databaseFetchdict('''SELECT * FROM colorchangers WHERE rainbow = false;''')
            for colorInstance in colorData:
                server = self.bot.get_guild(colorInstance['serverid'])
                role = discord.utils.get(server.roles, id=colorInstance['roleid'])
                color1 = discord.Color.from_hsv(colorInstance['percent'], 1, 1)

                percent = colorInstance['percent']
                color3_r = colorInstance['r_i'] - (colorInstance['r_i'] - colorInstance['r_f']) * percent
                color3_g = colorInstance['g_i'] - (colorInstance['g_i'] - colorInstance['g_f']) * percent
                color3_b = colorInstance['b_i'] - (colorInstance['b_i'] - colorInstance['b_f']) * percent
                # color3 = (int(color3_r), int(color3_g), int(color3_b))
                # print(color3)
                color3out = discord.Color.from_rgb(int(color3_r), int(color3_g), int(color3_b))
                await role.edit(color=color3out)
                percentInceease = self.updateFrequency / (60 * colorInstance['duration'])
                await SQLfunctions.databaseExecuteDynamic('''UPDATE colorchangers SET percent = percent + $1 WHERE roleid = $2;''',[percentInceease, colorInstance['roleid']])
            await SQLfunctions.databaseExecute('''DELETE FROM colorchangers WHERE rainbow = false AND percent > 1;''')

    @commands.command(name="setupRoleColorDatabase", description="generate a key that can be used to initiate a campaign")
    async def setupRoleColorDatabase(self, ctx: commands.Context):
        if ctx.author.id != main.ownerID:
            await errorFunctions.sendCategorizedError(ctx, "campaign")
            return
        await SQLfunctions.databaseExecute('''CREATE TABLE IF NOT EXISTS colorchangers (serverid BIGINT, roleid BIGINT, r_i INT, g_i INT, b_i INT, r_f INT, g_f INT, b_f INT, percent REAL, duration BIGINT, rainbow BOOLEAN);''')
        await ctx.send("## Done!")

    @commands.command(name="addColorChanger", description="generate a key that can be used to initiate a campaign")
    async def addColorChanger(self, ctx: commands.Context):
        if ctx.author.id != main.ownerID:
            return
        await ctx.send("Do you want to use this server?")
        isThisServer = await discordUIfunctions.getYesNoChoice(ctx)
        if isThisServer == True:
            serverid = ctx.guild.id
        else:
            serverid = await textTools.getIntResponse(ctx, "What is the server ID you wish to use?")
        roleid = await textTools.getIntResponse(ctx, "What role do you want to update?  Reply with that role's ID.")
        minutes = await textTools.getIntResponse(ctx, "How many minutes do you want the update to take?  Reply with an integer.")
        await ctx.send("Do you want to make it a rainbow color?")
        isRainbow = await discordUIfunctions.getYesNoChoice(ctx)
        server = self.bot.get_guild(serverid)
        role = discord.utils.get(server.roles, id=roleid)
        if isRainbow == False:
            final_color_str = await textTools.getResponse(ctx, "What hex color do you want to conclude with?")
            current_color_str = role.color
            h = str(current_color_str).lstrip('#')
            current_color = tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
            h = final_color_str.lstrip('#')
            final_color = tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
        else:
            current_color = (0, 0, 0)
            final_color = (0, 0, 0)
        datalist = [serverid, roleid, current_color[0], current_color[1], current_color[2], final_color[0], final_color[1], final_color[2], 0, minutes, isRainbow]
        await SQLfunctions.databaseExecuteDynamic('''INSERT INTO colorchangers VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)''', datalist)
        await ctx.send("## Done!\nThis role will now be automatically be updated!")

    @commands.command(name="clearColorChangers", description="generate a key that can be used to initiate a campaign")
    async def clearColorChangers(self, ctx: commands.Context):
        if ctx.author.id != main.ownerID:
            return
        roleid = await textTools.getIntResponse(ctx, "What role do you want to stop updating?  Reply with that role's ID.")
        server = self.bot.get_guild(ctx.guild.id)
        role = discord.utils.get(server.roles, id=roleid)
        await SQLfunctions.databaseExecuteDynamic('''DELETE FROM colorchangers WHERE roleid = $1''', [roleid])
        await ctx.send("## Done!")

    @commands.command(name="viewColorChangers", description="generate a key that can be used to initiate a campaign")
    async def listColorChangers(self, ctx: commands.Context):
        colorList = await SQLfunctions.databaseFetchdict('''SELECT * FROM colorchangers''')
        print(colorList)

        for colori in colorList:
            print(colori)
            end_time = datetime.now() + timedelta(minutes=int(colori['duration']*(1-colori['percent'])))
            date_string = str(end_time.replace(microsecond=0, second=0))
            format_string = "%Y-%m-%d %H:%M:%S"
            dt = datetime.strptime(date_string, format_string)
            print(dt.year)
            hour = dt.strftime("%I")
            min = dt.strftime("%M %p")
            day = dt.strftime("%A %B %d")
            guildIn = self.bot.get_guild(colori['serverid'])
            embed = discord.Embed(title=f"{guildIn.name} (ID: {colori['serverid']})",
                                  description=f"Role: **{discord.utils.get(guildIn.roles, id=colori['roleid']).name}** (ID: {colori['roleid']})",
                                  color=discord.Color.random())

            if colori['rainbow'] == True:
                embed.add_field(name="Cycle duration", value=colori['duration'])
                embed.add_field(name="Rainbow percent", value=f"{round(colori['percent']*100, 3)}%")
                embed.add_field(name="Resets at", value=discord.utils.format_dt(dt, style='f'), inline=False)
            else:
                embed.add_field(name="Starting color", value=f"RGB ({colori['r_i']}, {colori['g_i']}, {colori['b_i']})")
                embed.add_field(name="Ending color", value=f"RGB ({colori['r_f']}, {colori['g_f']}, {colori['b_f']})")
                embed.add_field(name="Progress", value=f"{round(colori['percent'] * 100, 3)}%")
                embed.add_field(name="End time", value=discord.utils.format_dt(dt, style='f'))
            await ctx.send(embed=embed)

async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(roleColorTools(bot))