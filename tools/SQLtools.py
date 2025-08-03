import discord
from discord.ext import commands
from discord import app_commands
#from main import SQLsettings
import asyncpg

class SQLtools():

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
    async def databaseExecute(self, prompt: str):
        async with self.pool.acquire() as connection:
            return await connection.execute(prompt)

    async def databaseExecuteDynamic(self, prompt: str, values: list):
        async with self.pool.acquire() as connection:
            return await connection.execute(prompt, *values)

    async def databaseFetch(self, prompt: str):
        async with self.pool.acquire() as connection:
            return await connection.fetch(prompt)

    async def databaseFetchFast(self, prompt: str):
        async with self.pool.acquire() as connection:
            return await connection.fetch(prompt)

    async def databaseMultiFetch(self, prompt: str):
        async with self.pool.acquire() as connection:
            await connection.execute(prompt)
            await connection.execute(prompt)
            await connection.execute(prompt)
            await connection.execute(prompt)
            return await connection.execute(prompt)

    async def databaseFetchDynamic(self, prompt: str, values: list):
        async with self.pool.acquire() as connection:
            return await connection.fetch(prompt, *values)

    async def databaseFetchdict(self, prompt: str):
        async with self.pool.acquire() as connection:
            return [dict(row) for row in await connection.fetch(prompt)]

    async def databaseFetchrow(self, prompt: str):
        async with self.pool.acquire() as connection:
            return dict(await connection.fetchrow(prompt))

    async def databaseFetchlist(self, prompt: str):
        async with self.pool.acquire() as connection:
            return list(await connection.fetchrow(prompt))

    async def databaseFetchdictDynamic(self, prompt: str, values: list):
        async with self.pool.acquire() as connection:
            return [dict(row) for row in await connection.fetch(prompt, *values)]

    async def databaseFetchrowDynamic(self, prompt: str, values: list):
        async with self.pool.acquire() as connection:
            return dict(await connection.fetchrow(prompt, *values))

    async def databaseFetchlistDynamic(self, prompt: str, values: list):
        async with self.pool.acquire() as connection:
            return list(await connection.fetchrow(prompt, *values))

    async def databaseFetchlineDynamic(self, prompt: str, values: list):
        async with self.pool.acquire() as connection:
            return [dict(row) for row in await connection.fetch(prompt, *values)][0]
#
#     @commands.command(name="adminExecute", description="register a contest")
#     async def adminExecute(self, ctx: commands.Context, *, prompt):
#         if ctx.author.id == 712509599135301673:
#             pass
#         else:
#             return
#         await ctx.send(await SQLfunctions.databaseExecute(prompt))
#
#     @commands.command(name="adminFetch", description="register a contest")
#     async def adminFetch(self, ctx: commands.Context, *, prompt):
#         if ctx.author.id == 712509599135301673:
#             pass
#         else:
#             return
#
#         result = await SQLfunctions.databaseFetch(prompt)
#         print(result)
#         await ctx.send(result)
#
#     async def getServerConfig(ctx: commands.Context):
#         prompt = '''SELECT * FROM serverconfig WHERE serverid = $1;'''
#         async with asyncpg.create_pool(**SQLsettings, command_timeout=60) as pool:
#             async with pool.acquire() as connection:
#                 return [dict(row) for row in await connection.fetch(prompt, ctx.guild.id)][0]
#
#     @commands.command(name="databaseAlterTest", description="Sends hello!")
#     async def databaseAlterTest(self, ctx):
#         ## create a new table from scratch
#         await SQLfunctions.databaseExecute('''DROP TABLE altertest''')
#         await SQLfunctions.databaseExecute('''CREATE TABLE IF NOT EXISTS altertest (campaignname VARCHAR, hostserverid BIGINT, campaignkey BIGINT);''')
#         await SQLfunctions.databaseExecute(f''' ALTER TABLE altertest ADD timescale INT;''')
#
#         ## add data
#         valList = ["The Campaign", 1105048871484272682, 12345, 68]
#         await SQLfunctions.databaseExecuteDynamic('''INSERT INTO altertest VALUES ($1, $2, $3, $4)''', valList)
#         valList = ["The Second Campaign", 1105048871484272682, 23456, 72]
#         await SQLfunctions.databaseExecuteDynamic('''INSERT INTO altertest VALUES ($1, $2, $3, $4)''', valList)
#         valList = ["Other campaign", 1105048871484272682, 87650, 68]
#         await SQLfunctions.databaseExecuteDynamic('''INSERT INTO altertest VALUES ($1, $2, $3, $4)''', valList)
#
#         ## retrieve the collected data
#         await ctx.send(await SQLfunctions.databaseFetchdict(f'''SELECT * FROM altertest'''))
#         await ctx.send(await SQLfunctions.databaseFetchrow(f'''SELECT * FROM altertest'''))
#         await ctx.send(await SQLfunctions.databaseFetchlist(f'''SELECT * FROM altertest'''))
#
# async def setup(bot:commands.Bot) -> None:
#   await bot.add_cog(SQLfunctions(bot))


