from datetime import datetime
from discord.ext import commands


class errorTools:
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def retrieveError(self, ctx: commands.Context):
        if ctx.author.id == 299330776162631680:  # Special user
            query = '''SELECT error from errorlist WHERE status = true AND errortype = 'mlp' ORDER BY RANDOM() LIMIT 1;'''
        else:
            query = '''SELECT error from errorlist WHERE status = true AND errortype NOT IN ('mlp', 'catgirl') ORDER BY RANDOM() LIMIT 1;'''

        # Fetch the records first without immediately indexing [0]
        records = await self.bot.sql.databaseFetchdict(query)

        # Safely check if records exist and isn't empty
        if not records or len(records) == 0:
            return "Oops, I couldn't find an error!"

        error_record = records[0]
        error_text = await self.errorfyText(ctx, error_record.get("error", "Unknown error"))
        return error_text.replace('@', '')

    async def retrieveCategorizedError(self, ctx: commands.Context, category: str):
        # Swapped to databaseFetchdictDynamic to avoid the NoneType iterable crash
        records = await self.bot.sql.databaseFetchdictDynamic(
            '''SELECT error from errorlist WHERE status = true AND errortype = $1 ORDER BY RANDOM() LIMIT 1;''',
            [category]
        )

        if not records or len(records) == 0:
            return f"Oops, I couldn't find an error in the '{category}' category!"

        error_record = records[0]
        error_text = await self.errorfyText(ctx, error_record.get("error", "Unknown error"))
        return error_text.replace('@', '')

    async def sendCategorizedError(self, ctx: commands.Context, category: str):
        error_message = await self.retrieveCategorizedError(ctx, category)
        await ctx.send(error_message)

    async def sendError(self, ctx: commands.Context):
        error_message = await self.retrieveError(ctx)
        await ctx.send(error_message)

    async def errorfyText(self, ctx: commands.Context, error_text: str):
        replacements = {
            '{user}': ctx.author.display_name,
            '{server}': ctx.guild.name,
            '{second}': datetime.now().strftime('%S'),
            '{minute}': datetime.now().strftime('%M'),
            '{hour}': datetime.now().strftime('%I'),
            '{meridian}': datetime.now().strftime('%p'),
            '{day}': datetime.now().strftime('%A'),
            '{month}': datetime.now().strftime('%B'),
            '{year}': datetime.now().strftime('%Y')
        }
        for key, value in replacements.items():
            error_text = error_text.replace(key, str(value))
        return error_text