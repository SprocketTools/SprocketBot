import discord
import type_hintsfrom discord.ext import commands
from discord import app_commands
#from main import SQLsettings
import asyncpg

class SQLtools():

    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
    async def databaseExecute(self, prompt: str):
        try:
            async with self.pool.acquire() as connection:
                return await connection.execute(prompt)
        except Exception as e:
            print(f"Query: {prompt} failed: \n\n{e}")
            raise e

    async def databaseExecuteDynamic(self, prompt: str, values: list):
        try:
            async with self.pool.acquire() as connection:
                return await connection.execute(prompt, *values)
        except Exception as e:
            print(f"Query: {prompt} failed: \n\n{e}")
            raise e

    async def databaseFetch(self, prompt: str):
        try:
            async with self.pool.acquire() as connection:
                return await connection.fetch(prompt)
        except Exception as e:
            print(f"Query: {prompt} failed: \n\n{e}")
            raise e

    async def databaseFetchFast(self, prompt: str):
        try:
            async with self.pool.acquire() as connection:
                return await connection.fetch(prompt)
        except Exception as e:
            print(f"Query: {prompt} failed: \n\n{e}")
            raise e

    async def databaseMultiFetch(self, prompt: str):
        try:
            async with self.pool.acquire() as connection:
                await connection.execute(prompt)
                await connection.execute(prompt)
                await connection.execute(prompt)
                await connection.execute(prompt)
                return await connection.execute(prompt)
        except Exception as e:
            print(f"Query: {prompt} failed: \n\n{e}")

    async def databaseFetchDynamic(self, prompt: str, values: list):
        try:
            async with self.pool.acquire() as connection:
                return await connection.fetch(prompt, *values)
        except Exception as e:
            print(f"Query: {prompt} failed: \n\n{e}")

    async def databaseFetchdict(self, prompt: str):
        try:
            async with self.pool.acquire() as connection:
                return [dict(row) for row in await connection.fetch(prompt)]
        except Exception as e:
            print(f"Query: {prompt} failed: \n\n{e}")

    async def databaseFetchrow(self, prompt: str):
        try:
            async with self.pool.acquire() as connection:
                return dict(await connection.fetchrow(prompt))
        except Exception as e:
            print(f"Query: {prompt} failed: \n\n{e}")

    async def databaseFetchlist(self, prompt: str):
        try:
            async with self.pool.acquire() as connection:
                return list(await connection.fetchrow(prompt))
        except Exception as e:
            print(f"Query: {prompt} failed: \n\n{e}")

    async def databaseFetchdictDynamic(self, prompt: str, values: list):
        try:
            async with self.pool.acquire() as connection:
                return [dict(row) for row in await connection.fetch(prompt, *values)]
        except Exception as e:
            print(f"Query: {prompt} failed: \n\n{e}")

    async def databaseFetchrowDynamic(self, prompt: str, values: list):
        try:
            async with self.pool.acquire() as connection:
                return dict(await connection.fetchrow(prompt, *values))
        except Exception as e:
            print(f"Query: {prompt} failed: \n\n{e}")

    async def databaseFetchlistDynamic(self, prompt: str, values: list):
        try:
            async with self.pool.acquire() as connection:
                return list(await connection.fetchrow(prompt, *values))
        except Exception as e:
            print(f"Query: {prompt} failed: \n\n{e}")

    async def databaseFetchlineDynamic(self, prompt: str, values: list):
        try:
            async with self.pool.acquire() as connection:
                return [dict(row) for row in await connection.fetch(prompt, *values)][0]
        except Exception as e:
            print(f"Query: {prompt} failed: \n\n{e}")
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


