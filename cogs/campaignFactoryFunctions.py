import discord
import datetime
import asyncio
from discord.ext import commands, tasks
import type_hints
import main
from cogs.textTools import textTools

# Configuration
FACTORY_TICK_RATE = 300  # Seconds (5 Minutes). Adjust as needed.


class campaignFactoryFunctions(commands.Cog):
    def __init__(self, bot: type_hints.SprocketBot):
        self.bot = bot

    async def cog_load(self):
        self.factory_heartbeat.start()
        print("Factory Heartbeat started.")

    async def cog_unload(self):
        self.factory_heartbeat.cancel()
        print("Factory Heartbeat stopped.")

    # ----------------------------------------------------------------------------------
    # SETUP: Factory Database
    # ----------------------------------------------------------------------------------
    @commands.is_owner()
    @commands.command(name="setupFactoryTables", description="Initialize tables for Industry and Inventory")
    async def setupFactoryTables(self, ctx: commands.Context):
        if ctx.author.id != main.ownerID:
            return await self.bot.error.sendCategorizedError(ctx, "campaign")

        # 1. Inventory Table
        await self.bot.sql.databaseExecute('''CREATE TABLE IF NOT EXISTS campaign_inventory (
            id SERIAL PRIMARY KEY,
            faction_id BIGINT,
            item_id BIGINT, 
            item_type VARCHAR(50), 
            quantity BIGINT DEFAULT 0,
            UNIQUE(faction_id, item_id, item_type)
        );''')

        # 2. Factories Table
        await self.bot.sql.databaseExecute('''CREATE TABLE IF NOT EXISTS campaign_factories (
            factory_id SERIAL PRIMARY KEY,
            faction_id BIGINT,
            factory_name VARCHAR(100),
            factory_level INT DEFAULT 1,
            efficiency REAL DEFAULT 1.0,
            production_type VARCHAR(50) DEFAULT 'General'
        );''')

        # 3. Production Queue Table
        await self.bot.sql.databaseExecute('''CREATE TABLE IF NOT EXISTS campaign_production_queue (
            queue_id SERIAL PRIMARY KEY,
            faction_id BIGINT,
            factory_id INT,
            item_id BIGINT,
            item_name VARCHAR(100),
            quantity_ordered INT,
            quantity_completed INT DEFAULT 0,
            start_time TIMESTAMP,
            finish_time_expected TIMESTAMP
        );''')

        await ctx.send("## Factory Database Initialized!")

    # ----------------------------------------------------------------------------------
    # AUTOMATION: The Factory Heartbeat
    # ----------------------------------------------------------------------------------
    @tasks.loop(seconds=FACTORY_TICK_RATE)
    async def factory_heartbeat(self):
        """
        Independent loop that checks production queues.
        """
        try:
            # FIX: Call the internal function, NOT the command
            await self._process_production_queue(ctx=None)
        except Exception as e:
            print(f"Factory Heartbeat Error: {e}")

    @factory_heartbeat.before_loop
    async def before_heartbeat(self):
        await self.bot.wait_until_ready()

    # ----------------------------------------------------------------------------------
    # LOGIC: Internal Processors
    # ----------------------------------------------------------------------------------
    async def _process_production_queue(self, ctx=None):
        """
        Internal logic to process completed items.
        """
        now = datetime.datetime.now()

        # Find completed items
        completed = await self.bot.sql.databaseFetchdictDynamic(
            "SELECT * FROM campaign_production_queue WHERE finish_time_expected < $1",
            [now]
        )

        count = 0
        for job in completed:
            # 1. Add to Inventory (Upsert)
            await self.bot.sql.databaseExecuteDynamic(
                '''INSERT INTO campaign_inventory (faction_id, item_id, item_type, quantity)
                   VALUES ($1, $2, 'vehicle', $3)
                   ON CONFLICT (faction_id, item_id, item_type) 
                   DO UPDATE SET quantity = campaign_inventory.quantity + EXCLUDED.quantity''',
                [job['faction_id'], job['item_id'], job['quantity_ordered']]
            )

            # 2. Remove from Queue
            await self.bot.sql.databaseExecuteDynamic("DELETE FROM campaign_production_queue WHERE queue_id = $1",
                                                      [job['queue_id']])
            count += 1

            # 3. Logging
            print(
                f"Job {job['queue_id']} completed. {job['quantity_ordered']}x {job['item_name']} added to Faction {job['faction_id']}.")

        # Only send Discord messages if triggered manually via command
        if ctx:
            if count > 0:
                await ctx.send(f"Processed {count} completed production jobs.")
            else:
                await ctx.send("No jobs ready for completion.")

    # ----------------------------------------------------------------------------------
    # USER: Factory Management
    # ----------------------------------------------------------------------------------
    @commands.command(name="checkProduction", description="[Debug] Force check production queue")
    async def checkProduction(self, ctx: commands.Context):
        """
        Manual trigger for the queue processor.
        """
        await self._process_production_queue(ctx=ctx)

    @commands.command(name="buildFactory", description="Construct new industrial capacity")
    async def buildFactory(self, ctx: commands.Context):
        faction_data = await ctx.bot.campaignTools.getUserFactionData(ctx)

        factory_cost = 1000000000  # 1 Billion default

        confirm = await ctx.bot.ui.getYesNoChoice(ctx, f"Build a new Factory for ${factory_cost:,}?")
        if not confirm: return

        if faction_data['money'] < factory_cost:
            return await ctx.send("Insufficient funds.")

        await self.bot.sql.databaseExecuteDynamic(
            "UPDATE campaignfactions SET money = money - $1 WHERE factionkey = $2",
            [factory_cost, faction_data['factionkey']])

        await self.bot.sql.databaseExecuteDynamic(
            "INSERT INTO campaign_factories (faction_id, factory_name, factory_level) VALUES ($1, $2, $3)",
            [faction_data['factionkey'], "Heavy Industry Plant", 1]
        )

        await ctx.send("Factory construction complete!")

    @commands.command(name="produce", description="Start a production line")
    async def produce(self, ctx: commands.Context):
        faction_data = await ctx.bot.campaignTools.getUserFactionData(ctx)

        # 1. Select Factory
        factories = await self.bot.sql.databaseFetchdictDynamic(
            "SELECT * FROM campaign_factories WHERE faction_id = $1", [faction_data['factionkey']])
        if not factories:
            return await ctx.send("You have no factories! Use `-buildFactory` first.")

        f_options = [f"{f['factory_name']} (Lvl {f['factory_level']})" for f in factories]
        f_choice = await ctx.bot.ui.getChoiceFromList(ctx, f_options, "Select Factory:")
        if not f_choice: return
        selected_factory = factories[f_options.index(f_choice)]

        # 2. Select Blueprint (Vehicle)
        bps = await self.bot.sql.databaseFetchdictDynamic(
            "SELECT vehicle_name, vehicle_id, base_cost, tank_weight FROM blueprint_stats WHERE owner_id = $1",
            [ctx.author.id])
        if not bps:
            return await ctx.send("You have no valid blueprints. Run `-submitDesign` or `-analyzeBlueprint` first.")

        bp_options = [f"{b['vehicle_name']} (${b['base_cost']:,})" for b in bps]
        bp_choice = await ctx.bot.ui.getChoiceFromList(ctx, bp_options, "Select Blueprint to Produce:")
        if not bp_choice: return
        selected_bp = bps[bp_options.index(bp_choice)]

        # 3. Quantity
        qty = await textTools.getIntResponse(ctx, "Quantity to produce:")
        if qty <= 0: return

        total_cost = int(selected_bp['base_cost'] * qty)

        if faction_data['money'] < total_cost:
            return await ctx.send(f"Insufficient funds. Need ${total_cost:,}.")

        confirm = await ctx.bot.ui.getYesNoChoice(ctx,
                                                  f"Start production of {qty}x **{selected_bp['vehicle_name']}** for ${total_cost:,}?")
        if not confirm: return

        await self.bot.sql.databaseExecuteDynamic(
            "UPDATE campaignfactions SET money = money - $1 WHERE factionkey = $2",
            [total_cost, faction_data['factionkey']])

        # 5. Calculate Time (1 hour per vehicle / Factory Level)
        production_hours = (qty * 1.0) / selected_factory['factory_level']
        finish_time = datetime.datetime.now() + datetime.timedelta(hours=production_hours)

        await self.bot.sql.databaseExecuteDynamic(
            '''INSERT INTO campaign_production_queue 
               (faction_id, factory_id, item_id, item_name, quantity_ordered, start_time, finish_time_expected)
               VALUES ($1, $2, $3, $4, $5, $6, $7)''',
            [faction_data['factionkey'], selected_factory['factory_id'], selected_bp['vehicle_id'],
             selected_bp['vehicle_name'], qty, datetime.datetime.now(), finish_time]
        )

        await ctx.send(f"Production started! Expected completion: {finish_time.strftime('%Y-%m-%d %H:%M')}")

    @commands.command(name="inventory", description="View your stockpiles")
    async def inventory(self, ctx: commands.Context):
        faction_data = await ctx.bot.campaignTools.getUserFactionData(ctx)

        items = await self.bot.sql.databaseFetchdictDynamic(
            '''SELECT i.item_type, i.quantity, b.vehicle_name 
               FROM campaign_inventory i 
               LEFT JOIN blueprint_stats b ON i.item_id = b.vehicle_id 
               WHERE i.faction_id = $1 AND i.quantity > 0''',
            [faction_data['factionkey']]
        )

        embed = discord.Embed(title=f"Inventory: {faction_data['factionname']}", color=discord.Color.green())

        if not items:
            embed.description = "Warehouses are empty."
        else:
            for item in items:
                name = item['vehicle_name'] if item['vehicle_name'] else item['item_type']
                embed.add_field(name=name, value=f"Count: {item['quantity']}", inline=True)

        await ctx.send(embed=embed)

    @commands.command(name="productionQueue", description="View active production lines")
    async def productionQueue(self, ctx: commands.Context):
        faction_data = await ctx.bot.campaignTools.getUserFactionData(ctx)

        queue = await self.bot.sql.databaseFetchdictDynamic(
            '''SELECT * FROM campaign_production_queue WHERE faction_id = $1 ORDER BY finish_time_expected ASC''',
            [faction_data['factionkey']]
        )

        embed = discord.Embed(title=f"Production Queue", color=discord.Color.orange())

        if not queue:
            embed.description = "No active production lines."
        else:
            for q in queue:
                remaining = q['finish_time_expected'] - datetime.datetime.now()
                if remaining.total_seconds() < 0:
                    status = "Processing..."
                else:
                    status = f"{remaining.seconds // 3600}h {(remaining.seconds // 60) % 60}m remaining"

                embed.add_field(
                    name=f"{q['item_name']} (x{q['quantity_ordered']})",
                    value=status,
                    inline=False
                )

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(campaignFactoryFunctions(bot))