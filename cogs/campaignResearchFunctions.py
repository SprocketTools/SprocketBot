import discord
import json
import datetime
from discord.ext import commands
import type_hints
import main
from cogs.textTools import textTools


class campaignResearchFunctions(commands.Cog):
    def __init__(self, bot: type_hints.SprocketBot):
        self.bot = bot

    # ----------------------------------------------------------------------------------
    # SETUP: Research Database
    # ----------------------------------------------------------------------------------
    @commands.is_owner()
    @commands.command(name="setupResearchTables", description="Initialize tables for the Tech Tree system")
    async def setupResearchTables(self, ctx: commands.Context):
        if ctx.author.id != main.ownerID:
            return await self.bot.error.sendCategorizedError(ctx, "campaign")

        # Wipe existing for clean slate (Requested)
        await self.bot.sql.databaseExecute("DROP TABLE IF EXISTS tech_definitions CASCADE;")
        await self.bot.sql.databaseExecute("DROP TABLE IF EXISTS faction_doctrines CASCADE;")
        await self.bot.sql.databaseExecute("DROP TABLE IF EXISTS faction_tech_unlocked CASCADE;")
        await self.bot.sql.databaseExecute("DROP TABLE IF EXISTS active_research CASCADE;")
        await self.bot.sql.databaseExecute("DROP TABLE IF EXISTS research_settings CASCADE;")

        # 1. Tech Master List
        await self.bot.sql.databaseExecute('''CREATE TABLE IF NOT EXISTS tech_definitions (
                tech_id SERIAL PRIMARY KEY,
                name VARCHAR(100) UNIQUE,
                description VARCHAR(500),
                research_time_days INT DEFAULT 7,
                research_cost BIGINT DEFAULT 0,
                prerequisite_tech_id INT,
                doctrine_tag VARCHAR(50) DEFAULT NULL, 
                effects_json TEXT
            );''')

        # 2. Faction Doctrine Choice
        await self.bot.sql.databaseExecute('''CREATE TABLE IF NOT EXISTS faction_doctrines (
                faction_id BIGINT PRIMARY KEY,
                doctrine_name VARCHAR(50),
                chosen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );''')

        # 3. Unlocked Technologies
        await self.bot.sql.databaseExecute('''CREATE TABLE IF NOT EXISTS faction_tech_unlocked (
                faction_id BIGINT,
                tech_id INT,
                unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (faction_id, tech_id)
            );''')

        # 4. Active Research Queue
        await self.bot.sql.databaseExecute('''CREATE TABLE IF NOT EXISTS active_research (
                faction_id BIGINT PRIMARY KEY,
                tech_id INT,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                finish_time_expected TIMESTAMP
            );''')

        # 5. Campaign Settings (New)
        # mode: 'EXCLUSIVE' (Default) or 'OPEN'
        await self.bot.sql.databaseExecute('''CREATE TABLE IF NOT EXISTS research_settings (
                server_id BIGINT PRIMARY KEY,
                doctrine_mode VARCHAR(20) DEFAULT 'EXCLUSIVE'
            );''')

        await ctx.send("## Research Database Initialized (Wiped & Rebuilt)!")

    # ----------------------------------------------------------------------------------
    # ADMIN: Manage Tech Tree
    # ----------------------------------------------------------------------------------
    @commands.is_owner()
    @commands.command(name="addTech", description="[Admin] Add a new technology to the game")
    async def addTech(self, ctx: commands.Context):
        """
        Wizard to add a technology to the database.
        """
        name = await textTools.getCappedResponse(ctx, "Tech Name:", 100)
        desc = await textTools.getResponse(ctx, "Description:")
        days = await textTools.getIntResponse(ctx, "Research Time (Days):")
        cost = await textTools.getIntResponse(ctx, "Research Cost (Money):")

        # Prerequisite Handling
        prereq_name = await textTools.getResponse(ctx, "Prerequisite Tech Name (or 'None'):")
        prereq_id = None
        if "none" not in prereq_name.lower():
            res = await self.bot.sql.databaseFetchrowDynamic("SELECT tech_id FROM tech_definitions WHERE name = $1",
                                                             [prereq_name])
            if res:
                prereq_id = res['tech_id']
            else:
                return await ctx.send("Prerequisite tech not found.")

        # Doctrine Handling
        doctrine = await textTools.getResponse(ctx, "Doctrine Exclusivity (Tag or 'None'):")
        if "none" in doctrine.lower(): doctrine = None

        # Effects (JSON)
        effects_str = await textTools.getResponse(ctx, "Effects JSON (e.g. {'max_weight': 5}):")
        try:
            json.loads(effects_str)  # Validate JSON
        except:
            return await ctx.send("Invalid JSON format.")

        await self.bot.sql.databaseExecuteDynamic(
            '''INSERT INTO tech_definitions (name, description, research_time_days, research_cost, prerequisite_tech_id, doctrine_tag, effects_json)
               VALUES ($1, $2, $3, $4, $5, $6, $7)''',
            [name, desc, days, cost, prereq_id, doctrine, effects_str]
        )
        await ctx.send(f"Added tech: **{name}**")

    # ----------------------------------------------------------------------------------
    # USER: Research Commands
    # ----------------------------------------------------------------------------------
    @commands.command(name="chooseDoctrine", description="Select your faction's permanent doctrine")
    async def chooseDoctrine(self, ctx: commands.Context):
        faction_data = await ctx.bot.campaignTools.getUserFactionData(ctx)
        faction_id = faction_data['factionkey']

        # Check if already chosen
        existing = await self.bot.sql.databaseFetchrowDynamic(
            "SELECT doctrine_name FROM faction_doctrines WHERE faction_id = $1", [faction_id])
        if existing:
            return await ctx.send(f"Your faction is already committed to the **{existing['doctrine_name']}** doctrine.")

        # Hardcoded list of doctrines (could be moved to DB later)
        doctrines = ["Mass Assault", "Superior Firepower", "Grand Battleplan", "Mobile Warfare"]
        choice = await ctx.bot.ui.getChoiceFromList(ctx, doctrines, "Select your Doctrine (Permanent Choice):")

        if not choice: return

        await self.bot.sql.databaseExecuteDynamic(
            "INSERT INTO faction_doctrines (faction_id, doctrine_name) VALUES ($1, $2)",
            [faction_id, choice]
        )
        await ctx.send(f"Doctrine set to **{choice}**.")

    @commands.command(name="setDoctrineMode", description="[Host] Toggle between Exclusive or Open doctrines")
    async def setDoctrineMode(self, ctx: commands.Context):
        if not await ctx.bot.campaignTools.isCampaignHost(ctx):
            return await ctx.send("Only the Campaign Host can change this setting.")

        options = ["EXCLUSIVE (Factions must pick one)", "OPEN (Factions can research everything)"]
        choice = await ctx.bot.ui.getChoiceFromList(ctx, options, "Select Doctrine Mode:")

        if not choice: return
        mode = "EXCLUSIVE" if "EXCLUSIVE" in choice else "OPEN"

        await self.bot.sql.databaseExecuteDynamic(
            '''INSERT INTO research_settings (server_id, doctrine_mode) VALUES ($1, $2)
               ON CONFLICT (server_id) DO UPDATE SET doctrine_mode = EXCLUDED.doctrine_mode''',
            [ctx.guild.id, mode]
        )
        await ctx.send(f"Campaign Doctrine Mode set to: **{mode}**")

    @commands.command(name="research", description="Start researching a technology")
    async def research(self, ctx: commands.Context):
        faction_data = await ctx.bot.campaignTools.getUserFactionData(ctx)
        faction_id = faction_data['factionkey']

        # 1. Check if busy
        busy = await self.bot.sql.databaseFetchrowDynamic("SELECT * FROM active_research WHERE faction_id = $1",
                                                          [faction_id])
        if busy:
            finish = busy['finish_time_expected'].strftime("%Y-%m-%d %H:%M")
            return await ctx.send(f"You are already researching. Expected completion: {finish}")

        # 2. Get Available Techs
        # Logic:
        # - Not already unlocked
        # - Prerequisite IS unlocked (or is NULL)
        # - Doctrine matches User Doctrine (or is NULL)
        query = '''
            WITH my_doctrine AS (SELECT doctrine_name FROM faction_doctrines WHERE faction_id = $1),
                 my_techs AS (SELECT tech_id FROM faction_tech_unlocked WHERE faction_id = $1)
            SELECT t.tech_id, t.name, t.research_cost, t.research_time_days
            FROM tech_definitions t
            LEFT JOIN my_doctrine d ON 1=1
            WHERE t.tech_id NOT IN (SELECT tech_id FROM my_techs)
            AND (t.prerequisite_tech_id IS NULL OR t.prerequisite_tech_id IN (SELECT tech_id FROM my_techs))
            AND (t.doctrine_tag IS NULL OR t.doctrine_tag = d.doctrine_name);
        '''
        available = await self.bot.sql.databaseFetchdictDynamic(query, [faction_id])

        if not available:
            return await ctx.send("No researchable technologies found.")

        # 3. User Selection
        options = [f"{t['name']} (${t['research_cost']} | {t['research_time_days']}d)" for t in available]
        selection_str = await ctx.bot.ui.getChoiceFromList(ctx, options, "Select Technology to Research:")
        if not selection_str: return

        # Extract selected tech
        selected_name = selection_str.split(" ($")[0]
        selected_tech = next(t for t in available if t['name'] == selected_name)

        # 4. Payment & Start
        current_money = faction_data['money']
        cost = selected_tech['research_cost']

        if current_money < cost:
            return await ctx.send("Insufficient funds.")

        # Deduct money
        await self.bot.sql.databaseExecuteDynamic(
            "UPDATE campaignfactions SET money = money - $1 WHERE factionkey = $2", [cost, faction_id])

        # Add to Queue
        finish_time = datetime.datetime.now() + datetime.timedelta(days=selected_tech['research_time_days'])
        await self.bot.sql.databaseExecuteDynamic(
            "INSERT INTO active_research (faction_id, tech_id, finish_time_expected) VALUES ($1, $2, $3)",
            [faction_id, selected_tech['tech_id'], finish_time]
        )

        await ctx.send(
            f"Research started on **{selected_name}**. Completion expected: {finish_time.strftime('%Y-%m-%d %H:%M')}")

    @commands.command(name="myTech", description="View unlocked technologies")
    async def myTech(self, ctx: commands.Context):
        faction_data = await ctx.bot.campaignTools.getUserFactionData(ctx)

        # Get Doctrine
        doc = await self.bot.sql.databaseFetchrowDynamic(
            "SELECT doctrine_name FROM faction_doctrines WHERE faction_id = $1", [faction_data['factionkey']])
        doctrine_name = doc['doctrine_name'] if doc else "None"

        # Get Unlocked Techs
        techs = await self.bot.sql.databaseFetchdictDynamic(
            '''SELECT t.name, t.description FROM tech_definitions t 
               JOIN faction_tech_unlocked u ON t.tech_id = u.tech_id 
               WHERE u.faction_id = $1''',
            [faction_data['factionkey']]
        )

        # Get Active Research
        active = await self.bot.sql.databaseFetchrowDynamic(
            '''SELECT t.name, a.finish_time_expected FROM active_research a 
               JOIN tech_definitions t ON a.tech_id = t.tech_id 
               WHERE a.faction_id = $1''',
            [faction_data['factionkey']]
        )

        embed = discord.Embed(title=f"Research Status: {faction_data['factionname']}", color=discord.Color.blue())
        embed.add_field(name="Current Doctrine", value=doctrine_name, inline=False)

        if active:
            remaining = active['finish_time_expected'] - datetime.datetime.now()
            embed.add_field(name="Currently Researching",
                            value=f"{active['name']} (Done in {remaining.days}d {remaining.seconds // 3600}h)",
                            inline=False)
        else:
            embed.add_field(name="Currently Researching", value="Idle", inline=False)

        if techs:
            tech_list = "\n".join([f"• {t['name']}" for t in techs])
            if len(tech_list) > 1000: tech_list = tech_list[:1000] + "..."
            embed.add_field(name="Unlocked Technologies", value=tech_list, inline=False)
        else:
            embed.add_field(name="Unlocked Technologies", value="None", inline=False)

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(campaignResearchFunctions(bot))