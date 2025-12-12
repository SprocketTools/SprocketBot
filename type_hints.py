# type_hints.py
from discord.ext import commands
from tools.SQLtools import SQLtools         # Import your actual tool classes here
from tools.campaignTools import campaignTools

class SprocketBot(commands.Bot):
    # Tell PyCharm these attributes exist and what type they are
    sql: SQLtools
    campaignTools: campaignTools
    # Add any other custom tools you attached to 'bot' here