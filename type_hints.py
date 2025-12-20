# type_hints.py
from discord.ext import commands
from tools.AITools import AITools
from tools.blueprintAnalysisTools import blueprintAnalysisTools
from tools.campaignTools import campaignTools
from tools.errorTools import errorTools
from tools.SQLtools import SQLtools
from tools.UItools import UItools

class SprocketBot(commands.Bot):
    ai: AITools
    analyzer: blueprintAnalysisTools
    campaign: campaignTools
    error: errorTools
    sql: SQLtools
    ui: UItools

