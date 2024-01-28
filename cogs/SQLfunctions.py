import discord
from discord.ext import commands
from discord import app_commands
from main import SQLsettings
import asyncpg
class SQLfunctions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="cog3", description="Sends hello!")
    async def cog1(self, ctx):
        await ctx.send(content="Hello!")

    async def databaseExecute(self, prompt):
        async with asyncpg.create_pool(**SQLsettings,command_timeout=60) as pool:
            async with pool.acquire() as connection:
                await connection.execute(prompt)

    async def databaseFetch(self, prompt):
        async with asyncpg.create_pool(**SQLsettings,command_timeout=60) as pool:
            async with pool.acquire() as connection:
                await connection.fetch(prompt)

    async def databaseFetchrow(self, prompt):
        async with asyncpg.create_pool(**SQLsettings,command_timeout=60) as pool:
            async with pool.acquire() as connection:
                await connection.fetchrow(prompt)

    @commands.command(name="databaseTest", description="Sends hello!")
    async def databaseTest(self, ctx):
        async with asyncpg.create_pool(**SQLsettings,command_timeout=60) as pool:
            async with pool.acquire() as connection:
                await connection.execute('''DROP TABLE tanks''')
                await connection.execute('''CREATE TABLE IF NOT EXISTS tanks (
                      tankName VARCHAR,
                      tankOwnerID BIGINT,
                      hostEventID INT,
                      time INT,
                      gameVersion REAL,
                      gameEra VARCHAR,
                      weight REAL,
                      crewCount INT,
                      turretCount INT,
                      GCMcount INT,
                      hullHeight REAL,
                      tankWidth REAL,
                      tankLength REAL,
                      torsionBarLength REAL,
                      suspensionType VARCHAR,
                      beltWidth REAL,
                      groundPressure REAL,
                      HP REAL,
                      HPT REAL,
                      litersPerDisplacement REAL,
                      litersPerTon REAL,
                      topSpeed REAL,
                      gunCount INT,
                      maxCaliber INT,
                      maxPropellant INT,
                      maxBore REAL,
                      maxShell INT,
                      minArmor INT,
                      maxArmor INT);''')
                await connection.execute(f'''
                             INSERT INTO tanks (
                      tankName,
                      tankOwnerID,
                      hostEventID,
                      time,
                      gameVersion,
                      gameEra,
                      weight,
                      crewCount,
                      turretCount,
                      GCMcount,
                      hullHeight,
                      tankWidth,
                      tankLength,
                      torsionBarLength,
                      suspensionType,
                      beltWidth,
                      groundPressure,
                      HP,
                      HPT,
                      litersPerDisplacement,
                      litersPerTon,
                      topSpeed,
                      gunCount,
                      maxCaliber,
                      maxPropellant,
                      maxBore,
                      maxShell,
                      minArmor,
                      maxArmor)
                     values (
                          'LT-26',
                          '712509599135301673',
                          '1',
                          '1705413900',
                          '0.127',
                          'Midwar',
                          '29.87',
                          '4',
                          '2',
                          '3',
                          '1.02',
                          '3.6',
                          '6.5',
                          '0.8',
                          'torsion bar',
                          '400',
                          '1.2',
                          '400',
                          '12',
                          '30',
                          '28',
                          '36',
                          '2',
                          '90',
                          '780',
                          '3.9',
                          '1100',
                          '15',
                          '140' ); ''')
                await ctx.send(await connection.fetch('SELECT * FROM tanks'))


async def setup(bot:commands.Bot) -> None:
  await bot.add_cog(SQLfunctions(bot))


