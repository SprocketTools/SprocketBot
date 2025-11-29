import asyncio
import io
import discord
import pandas as pd
from datetime import datetime, timedelta
from discord.ext import tasks, commands
import main

# --- Configuration Constants ---
UPDATE_FREQUENCY = 600  # seconds (Matches your latest upload)
SECONDS_IN_YEAR = 31536000 + 21600
STATUS_LOG_CHANNEL_ID = 1152377925916688484
BACKUP_CHANNEL_ID = 1156854471767367680


class campaignUpdateFunctions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        status_channel = self.bot.get_channel(STATUS_LOG_CHANNEL_ID)

        if self.bot.ishost:
            now = datetime.now()
            # Calculate seconds until the next aligned interval
            seconds_count = int(3600 - (now.minute * 60 + now.second)) % UPDATE_FREQUENCY

            minutes_wait = int(seconds_count / 60)
            seconds_wait = int(seconds_count % 60)

            if status_channel:
                await status_channel.send(
                    f"First campaign update is scheduled for: **{minutes_wait}m {seconds_wait}s** from now.")

            await asyncio.sleep(seconds_count)
            if not self.loopUpdate.is_running():
                self.loopUpdate.start()
        else:
            if status_channel:
                await status_channel.send("Not initiating campaign updates (Instance is not Host).")

    @tasks.loop(seconds=UPDATE_FREQUENCY)
    async def loopUpdate(self):
        status_channel = self.bot.get_channel(STATUS_LOG_CHANNEL_ID)

        try:
            current_time = int(datetime.now().timestamp())
            last_time = int(main.baseConfig["settings"].get('lastupdated', 0))

            # Catch up loop: If the bot was offline, run multiple updates to catch up
            while last_time + (UPDATE_FREQUENCY / 2) < current_time:
                if status_channel:
                    await status_channel.send(f"Update starting for cycle: <t:{last_time}:T>")

                # 1. Normalize Data (Clamp values)
                await self.normalize_data()

                # 2. Advance Time
                await self.updateTime()

                # 3. Process Transactions
                await self.runAutoTransactions()

                # 4. Update Economics & Demographics
                await self.updateHappiness()
                await self.updatePopulation()

                # --- DEBUG: Track Tax Collection ---
                await self.collectTaxes()

                await self.updateGDP()
                await self.updateEducation()
                await self.updateEspionage()
                await self.sendTimeUpdates()

                # 5. Finalize
                await self.updateLastUpdated()

                # Backup logic
                if datetime.now().minute < 2:
                    await self.sendBackup()
                else:
                    print(f"[{datetime.now()}] Campaign update triggered")

                # Update Config (Iterative)
                last_time += UPDATE_FREQUENCY
                main.baseConfig["settings"]['lastupdated'] = str(last_time)

                if status_channel:
                    await status_channel.send(
                        f"Campaigns have updated from <t:{last_time - UPDATE_FREQUENCY}:f> to <t:{last_time}:f>")

            # Save final state to file
            main.baseConfig["settings"]['lastupdated'] = str(current_time)
            with open(main.configurationFilepath, "w") as configfile:
                main.baseConfig.write(configfile)

        except Exception as e:
            print(f"CRITICAL UPDATE FAILURE: {e}")
            if status_channel:
                await status_channel.send(
                    f"⚠️ **CRITICAL UPDATE FAILURE** ⚠️\nError: `{e}`\nLoop is still running, but this tick failed.")

    async def normalize_data(self):
        """Clamps database values to prevent mathematical errors or runaways."""
        queries = [
            # Set minimums to prevent division by zero or logic errors
            "UPDATE campaignfactions SET happiness = 0.01 WHERE happiness < 0.01 AND iscountry = true AND hostactive = true;",
            "UPDATE campaignfactions SET popgrowth = 0.01 WHERE popgrowth < 0.01 AND hostactive = true;",
            "UPDATE campaignfactions SET averagesalary = 1 WHERE averagesalary < 1 AND iscountry = true AND hostactive = true;",
            "UPDATE campaignfactions SET lifeexpectancy = 0.01 WHERE lifeexpectancy < 0.01 AND iscountry = true AND hostactive = true;",
            "UPDATE campaignfactions SET infrastructureindex = 0.01 WHERE infrastructureindex < 0.01 AND iscountry = true AND hostactive = true;",
            "UPDATE campaignfactions SET educationindex = 0.01 WHERE educationindex < 0.01 AND iscountry = true AND hostactive = true;",
            "UPDATE campaignfactions SET gdp = 1 WHERE gdp < 0 AND iscountry = true;",
            "UPDATE campaignfactions SET landsize = 1 WHERE landsize < 1 AND iscountry = true;",
            # Prevent Div/0 in Population

            # Clamp maximums/minimums
            "UPDATE campaignfactions SET happiness = LEAST(GREATEST(happiness, 0.01), 1) WHERE iscountry = true AND hostactive = true;",
            "UPDATE campaignfactions SET socialspend = LEAST(GREATEST(socialspend, 0), 1) WHERE iscountry = true AND hostactive = true;",
            "UPDATE campaignfactions SET povertyrate = LEAST(GREATEST(povertyrate, 0), 1) WHERE iscountry = true AND hostactive = true;",
            "UPDATE campaignfactions SET popworkerratio = LEAST(GREATEST(popworkerratio, 1), 5) WHERE iscountry = true AND hostactive = true;",
            "UPDATE campaignfactions SET averagesalary = LEAST(GREATEST(averagesalary, 1), 50000) WHERE iscountry = true AND hostactive = true;",

            # Fill NULLs
            "UPDATE campaignfactions SET money = 12345678 WHERE money IS NULL;",
            "UPDATE campaignfactions SET corespend = 0.1 WHERE corespend IS NULL;",
            "UPDATE campaignfactions SET socialspend = 0.1 WHERE socialspend IS NULL;",
            "UPDATE campaignfactions SET defensespend = 0.1 WHERE defensespend IS NULL;"
        ]

        for query in queries:
            await self.bot.sql.databaseExecute(query)

    async def updateTime(self):
        await self.bot.sql.databaseExecuteDynamic(
            '''UPDATE campaigns
               SET timedate = timedate + (interval '1 second' * timescale * $1)
               WHERE active = true;''',
            [UPDATE_FREQUENCY]
        )

    async def updatePopulation(self):
        # FIX: Added GREATEST(..., 1.0) to LN inputs to prevent LN(<=0) crash
        pop_growth_query = f'''
            UPDATE campaignfactions 
            SET population = GREATEST(population + ROUND((
                (CAST ($1 AS FLOAT) / CAST ($2 AS FLOAT)) * population * (
                    (0.5 * ATAN(500000/landsize) + 0.3*(1-latitude/90) + 0.2*(LN(GREATEST(population, 1.0)) + LN(GREATEST(gdp, 1.0)))) + 
                    (1 - 0.3*educationindex) + 
                    (4 - lifeexpectancy/20) + 
                    (0.5 * POWER(povertyrate, 0.5) - 0.2)
                )
            ))::BIGINT, 0)
            FROM campaigns 
            WHERE campaignfactions.campaignkey = campaigns.campaignkey
              AND campaignfactions.iscountry = true 
              AND campaignfactions.hostactive = true;
        '''
        await self.bot.sql.databaseExecuteDynamic(pop_growth_query, [UPDATE_FREQUENCY, SECONDS_IN_YEAR])

        # Recalculate Population Growth Rate (for display stats)
        rate_query = '''
                     UPDATE campaignfactions
                     SET popgrowth = 0.005 * ((population * (
                         (0.5 * ATAN(500000 / landsize) + 0.3 * (1 - latitude / 90) + \
                          0.2 * (LN(GREATEST(population, 1.0)) + LN(GREATEST(gdp, 1.0)))) +
                         (1 - 0.3 * educationindex) +
                         (4 - lifeexpectancy / 20) +
                         (0.5 * POWER(povertyrate, 0.5) - 0.2)
                         )) / population) - 0.02
                     WHERE iscountry = true \
                       AND hostactive = true; \
                     '''
        await self.bot.sql.databaseExecute(rate_query)

    async def updatePoverty(self):
        # FIX: Added GREATEST(0.01, ...) to denominator to prevent Division by Zero or Negative Tax Reward
        query = '''
                UPDATE campaignfactions
                SET povertyrate = (2 * (ATAN(POWER((campaigns.energycost * campaigns.steelcost / 7 * popworkerratio) / \
                                                   (averagesalary * GREATEST(0.01, (1.0 - ((taxpoor / 1.112) + (taxrich / 10))))), 2)) / \
                                        PI())) FROM campaigns
                WHERE campaigns.campaignkey = campaignfactions.campaignkey
                  AND campaignfactions.iscountry = true
                  AND campaignfactions.hostactive = true; \
                '''
        await self.bot.sql.databaseExecute(query)

    async def collectTaxes(self):
        query = f'''
            UPDATE campaignfactions 
            SET money = money + ROUND(
                gdp * ((taxrich * 0.25) + (taxpoor * 0.75)) * ( CAST ($1 AS FLOAT) / CAST ($2 AS FLOAT) ) * campaigns.timescale * defensespend
            )::BIGINT 
            FROM campaigns
            WHERE campaignfactions.campaignkey = campaigns.campaignkey 
              AND campaignfactions.iscountry = true 
              AND campaignfactions.hostactive = true;
        '''
        await self.bot.sql.databaseExecuteDynamic(query, [UPDATE_FREQUENCY, SECONDS_IN_YEAR])

    async def updateGDP(self):
        # FIX: Clamped result to GREATEST(1.0, ...) to prevent Ratio from becoming 0 or negative
        await self.bot.sql.databaseExecute(
            "UPDATE campaignfactions SET popworkerratio = GREATEST(1.0, 4.0 - (5.02 * CAST(povertyrate AS numeric))/2.01);"
        )

        gdp_growth_query = '''
                           UPDATE campaignfactions
                           SET gdpgrowth = campaigns.defaultgdpgrowth + (0.25 * (
                               0.4 * 2 * ATAN(2 * (infrastructureindex - 0.5)) +
                               0.6 * 2 * ATAN(4 * (0.5 - taxpoor)) +
                               0.4 * 2 * ATAN(4 * (0.5 - taxrich)) -
                               0.25 * 2 * ATAN(2 * (povertyrate - 0.5)) +
                               0.4 * 2 * ATAN(2 * (educationindex - 0.5)) - 2
                               )) / (2.71 * PI()) FROM campaigns
                           WHERE campaignfactions.campaignkey = campaigns.campaignkey
                             AND iscountry = true
                             AND hostactive = true; \
                           '''
        await self.bot.sql.databaseExecute(gdp_growth_query)

        await self.bot.sql.databaseExecute(
            "UPDATE campaignfactions SET corespend = (1.0 - (socialspend + infrastructurespend + defensespend)) WHERE iscountry = true AND hostactive = true;"
        )

        salary_query = f'''
            UPDATE campaignfactions 
            SET averagesalary = averagesalary + averagesalary * gdpgrowth * ( CAST ($1 AS FLOAT) / CAST ($2 AS FLOAT) ) * campaigns.timescale  
            FROM campaigns 
            WHERE campaignfactions.campaignkey = campaigns.campaignkey
              AND iscountry = true 
              AND hostactive = true;
        '''
        await self.bot.sql.databaseExecuteDynamic(salary_query, [UPDATE_FREQUENCY, SECONDS_IN_YEAR])

        await self.bot.sql.databaseExecute(
            "UPDATE campaignfactions SET gdp = (population * averagesalary / popworkerratio)::BIGINT WHERE iscountry = true AND hostactive = true;"
        )

    async def updateIncome(self):
        pass

    async def updateEspionage(self):
        query = '''
                UPDATE campaignfactions
                SET espionagestaff = ROUND((
                                               ((gdp * ((taxrich * 0.25) + (taxpoor * 0.75))) * espionagespend) / \
                                               (averagesalary * 10) - espionagestaff
                                               ) * 0.1 + espionagestaff)::INT
                WHERE iscountry = true AND hostactive = true; \
                '''
        await self.bot.sql.databaseExecute(query)
        await self.bot.sql.databaseExecute(
            "UPDATE campaignfactions SET espionagestaff = 0 WHERE espionagestaff < 0 AND iscountry = true AND hostactive = true;"
        )

    async def updateEducation(self):
        # FIX: Protected LN inputs with GREATEST(..., 1.0)
        queries = [
            '''
            UPDATE campaignfactions
            SET lifeexpectancy = GREATEST((
                                              (65 + 30 * (0.2 * happiness -
                                                          1 * LN(GREATEST(povertyrate + taxpoor + 1.5 - socialspend, 1.0)) +
                                                          0.4 * infrastructureindex)) - lifeexpectancy
                                              ) * 0.902 + lifeexpectancy, 0)
            WHERE iscountry = true
              AND hostactive = true;
            ''',
            '''
            UPDATE campaignfactions
            SET infrastructureindex = GREATEST((
                                                   (1.6 * ATAN(infrastructurespend *
                                                               (gdp * ((taxrich * 0.25) + (taxpoor * 0.75))) /
                                                               population) / PI() + 0.1 * governance) -
                                                   infrastructureindex
                                                   ) * 0.902 + infrastructureindex, 0)
            WHERE iscountry = true
              AND hostactive = true;
            ''',
            '''
            UPDATE campaignfactions
            SET educationindex = LEAST(GREATEST((
                                                    (0.5 *
                                                     LN(GREATEST(socialspend * (gdp * ((taxrich * 0.25) + (taxpoor * 0.75))) /
                                                        population + 0.1, 1.0)) +
                                                     0.3 / (1 + EXP(-0.1 * (population / landsize))) +
                                                     0.2 * governance) - educationindex
                                                    ) * 0.902 + educationindex, 0.005), 1)
            WHERE iscountry = true
              AND hostactive = true;
            ''',
            '''
            UPDATE campaignfactions
            SET socialspend = corespend * (0.5 + governance / 2)
            WHERE iscountry = true
              AND hostactive = true;
            '''
        ]
        for q in queries:
            await self.bot.sql.databaseExecute(q)

    async def updateHappiness(self):
        # FIX: Protected LN inputs
        query = '''
                UPDATE campaignfactions
                SET happiness = LEAST(1, GREATEST(
                        (2 / PI()) * ATAN(0.5 * (
                            (1 - povertyrate) * \
                            (ATAN(socialspend * (1 - (0.75 * taxpoor + 0.75 * taxrich)) + (5 / 9)) / 2) +
                            0.3 * (lifeexpectancy / 80) +
                            0.2 * (LN(GREATEST((gdp / population) + 0.25, 1.0)) / ln(1.25)) +
                            0.1 * ((governance + 1)^2) + 
                    0.1 * (taxpoor * 5 * (4 - governance))
                )), 0
                                         ))
                WHERE iscountry = true \
                  AND hostactive = true; \
                '''
        await self.bot.sql.databaseExecute(query)

    async def updateLastUpdated(self):
        await self.bot.sql.databaseExecute("UPDATE campaigns SET lastupdated = timedate;")

    async def runAutoTransactions(self):
        campaigns_due = await self.bot.sql.databaseFetchdict(
            "SELECT * FROM campaigns where EXTRACT(MONTH FROM timedate) != EXTRACT(MONTH FROM lastupdated);"
        )

        for campaign_data in campaigns_due:
            private_channel = self.bot.get_channel(campaign_data['privatemoneychannelid'])
            if private_channel:
                formatted_date = f"{campaign_data['timedate'].strftime('%B')} {campaign_data['timedate'].strftime('%Y')}"
                await private_channel.send(f"---Transactions for: {formatted_date}---")

            transactions = await self.bot.sql.databaseFetchdictDynamic(
                "SELECT * FROM transactions WHERE repeat > 0 AND campaignkey = $1;",
                [campaign_data['campaignkey']]
            )

            print(f"There are {len(transactions)} auto transactions queued for {campaign_data['campaignname']}")

            for tx in transactions:
                try:
                    game_date = datetime.strptime(str(campaign_data['timedate']).split(" ")[0], "%Y-%m-%d")
                    if (game_date.month - 1) % tx['repeat'] == 0:
                        await self._process_single_transaction(tx, campaign_data)
                except Exception as e:
                    error_channel = self.bot.get_channel(STATUS_LOG_CHANNEL_ID)
                    if error_channel:
                        await error_channel.send(
                            f"An automatic transaction failed.\nDescription: {tx.get('description', 'Unknown')}\nError: {e}")

        return "Complete!"

    async def _process_single_transaction(self, tx, campaign_data):
        """Helper to process a single transaction row to clean up the main loop."""
        money_add = tx['cost']
        transaction_type = tx['type']
        customer_key = int(tx['customerkey'])
        seller_key = int(tx['sellerkey'])

        # --- HELPER: Auto-Delete Logic ---
        async def delete_zombie_transaction(reason):
            """Deletes the broken transaction to prevent future errors."""
            await self.bot.sql.databaseExecuteDynamic(
                '''DELETE
                   FROM transactions
                   WHERE customerkey = $1
                     AND sellerkey = $2
                     AND description = $3
                     AND cost = $4
                     AND campaignkey = $5
                     AND type = $6;''',
                [customer_key, seller_key, tx['description'], money_add, tx['campaignkey'], transaction_type]
            )
            # Raise error to stop processing this specific transaction
            raise ValueError(f"Auto-Cancellation: {reason}. Transaction deleted from database.")

        # --- 1. RESOLVE FACTIONS ---
        customer_data = None
        seller_data = None

        # Fetch Customer (if exists)
        if customer_key and customer_key != 0:
            try:
                customer_data = await self.bot.campaignTools.getFactionData(customer_key)
                if not customer_data: raise ValueError()
            except:
                await delete_zombie_transaction(f"Customer faction (ID: {customer_key}) no longer exists")

        # Fetch Seller (if exists)
        if seller_key and seller_key != 0:
            try:
                seller_data = await self.bot.campaignTools.getFactionData(seller_key)
                if not seller_data: raise ValueError()
            except:
                await delete_zombie_transaction(f"Seller faction (ID: {seller_key}) no longer exists")

        # --- 2. EXECUTE TRANSFER & PREPARE LOGGING ---
        customer_name = "Unknown"
        seller_name = "Unknown"
        primary_faction_for_log = None

        if transaction_type == "sales of equipment to civilians":
            if not seller_data:
                await delete_zombie_transaction(f"Invalid Civilian Sale: Seller ID {seller_key} missing")

            # Money IN to Seller
            await self.bot.sql.databaseExecuteDynamic(
                "UPDATE campaignfactions SET money = money + $1 WHERE factionkey = $2;",
                [money_add, seller_key]
            )
            customer_name = f"Citizens of {seller_data['factionname']}"
            seller_name = seller_data['factionname']
            primary_faction_for_log = seller_data

        elif transaction_type == "maintenance payments":
            if not seller_data:
                await delete_zombie_transaction(f"Invalid Maintenance: Payer ID {seller_key} missing")

            # Money OUT from Seller (Payer)
            await self.bot.sql.databaseExecuteDynamic(
                "UPDATE campaignfactions SET money = money - $1 WHERE factionkey = $2;",
                [money_add, seller_key]
            )
            customer_name = f"Citizens of {seller_data['factionname']}"
            seller_name = seller_data['factionname']
            primary_faction_for_log = seller_data

        else:
            # Standard Transfer: Customer -> Seller
            if not customer_data or not seller_data:
                # This catch-all shouldn't trigger due to checks above, but safe to have
                await delete_zombie_transaction("One or both parties in this transaction no longer exist")

            # Money IN to Seller
            await self.bot.sql.databaseExecuteDynamic(
                "UPDATE campaignfactions SET money = money + $1 WHERE factionkey = $2;",
                [money_add, seller_key]
            )
            # Money OUT from Customer
            await self.bot.sql.databaseExecuteDynamic(
                "UPDATE campaignfactions SET money = money - $1 WHERE factionkey = $2;",
                [money_add, customer_key]
            )
            customer_name = customer_data['factionname']
            seller_name = seller_data['factionname']
            primary_faction_for_log = customer_data

        # --- 3. LOGGING ---
        time_str = await self.bot.campaignTools.getTime(campaign_data['timedate'])
        embed = discord.Embed(title="Automatic transaction log", color=discord.Color.random())
        embed.add_field(name="Customer:", value=customer_name)
        embed.add_field(name="Seller", value=seller_name)
        embed.add_field(name="Cost",
                        value=f"{campaign_data['currencysymbol']}{money_add} {campaign_data['currencyname']}")
        embed.add_field(name="Time of purchase", value=time_str, inline=False)
        embed.add_field(name="Details", value=tx['description'], inline=False)

        if primary_faction_for_log and primary_faction_for_log.get('flagurl'):
            embed.set_thumbnail(url=primary_faction_for_log['flagurl'])

        # Calculate Completion Date
        ship_date_months = tx['repeat']
        completion_date = campaign_data['timedate'] + timedelta(days=ship_date_months * 30)
        embed.add_field(name="Completion date:", value=completion_date.strftime("%A %B %d, %Y"), inline=False)

        if tx['repeat'] > 0:
            embed.add_field(name="Repeat frequency:", value=f"{tx['repeat']} months", inline=False)

        # Send Embeds
        private_channel = self.bot.get_channel(int(campaign_data["privatemoneychannelid"]))
        if private_channel:
            await private_channel.send(embed=embed)

        # Also log to the counterparty's channel if it's a P2P trade
        if transaction_type != "sales of equipment to civilians" and transaction_type != "maintenance payments":
            if seller_data and 'logchannel' in seller_data:
                log_channel = self.bot.get_channel(int(seller_data["logchannel"]))
                if log_channel:
                    await log_channel.send(embed=embed)

    async def sendBackup(self):
        tables = await self.bot.sql.databaseFetchdict(
            "SELECT table_schema, table_name FROM information_schema.tables WHERE table_type = 'BASE TABLE' AND table_schema NOT IN ('pg_catalog', 'information_schema');"
        )

        backup_channel = self.bot.get_channel(BACKUP_CHANNEL_ID)
        if not backup_channel:
            print("Backup channel not found.")
            return

        for table in tables:
            tablename = table['table_name']
            data = await self.bot.sql.databaseFetchdict(f'SELECT * FROM {tablename};')

            if not data:
                continue

            df = pd.DataFrame(data)
            buffer = io.StringIO()
            df.to_csv(buffer, index=False)
            buffer.seek(0)

            filename = f"{tablename}-{datetime.now().strftime('%Y%m%d-%H%M')}.csv"
            await backup_channel.send(file=discord.File(buffer, filename))

    async def sendTimeUpdates(self):
        data = await self.bot.sql.databaseFetchdict(
            "SELECT * FROM campaigns where EXTRACT(YEAR FROM timedate) != EXTRACT(YEAR FROM lastupdated);"
        )
        for campaign_data in data:
            channel = self.bot.get_channel(campaign_data['publiclogchannelid'])
            if channel:
                dt = campaign_data['timedate']
                await channel.send(
                    f"## Happy new year! :tada:\nThe year is now **{dt.year}** in **{campaign_data['campaignname']}**")

    # --- Manual Commands ---

    @commands.command(name="backup", description="Force a manual database backup")
    async def backup(self, ctx):
        await self.sendBackup()
        await ctx.send("Backup process initiated.")

    @commands.command(name="forceTransactions", description="Force run auto transactions")
    async def forceTransactions(self, ctx: commands.Context):
        await self.runAutoTransactions()
        await ctx.send("Transactions processed!")

    @commands.command(name="forceUpdate", description="Force a full campaign update tick")
    async def forceUpdate(self, ctx: commands.Context):
        current_time = int(datetime.now().timestamp())

        status_channel = self.bot.get_channel(STATUS_LOG_CHANNEL_ID)
        await status_channel.send("Forced Update is starting!")

        await self.normalize_data()
        await status_channel.send("DEBUG: Data normalized.")
        await self.updatePoverty()
        await status_channel.send("DEBUG: Poverty updated.")
        await self.updateTime()
        await status_channel.send("DEBUG: Time updated.")
        await self.updatePopulation()
        await status_channel.send("DEBUG: Populations updated.")
        await self.updatePoverty()
        await status_channel.send("DEBUG: Poverty update completed.")
        await self.collectTaxes()
        await status_channel.send("DEBUG: Taxes collected.")
        await self.updateGDP()
        await status_channel.send("DEBUG: GDP updated.")
        await self.updateIncome()
        await status_channel.send("DEBUG: Income updated.")
        await self.updateHappiness()
        await status_channel.send("DEBUG: Happiness updated.")
        await self.updateEducation()
        await status_channel.send("DEBUG: Education data updated.")
        await self.sendTimeUpdates()
        await status_channel.send("DEBUG: Time updates completed.")
        await self.updateEspionage()
        await status_channel.send("DEBUG: Espionage data updated.")
        await self.updateLastUpdated()
        await status_channel.send("DEBUG: Global time increment updated.")

        try:
            # FIX: Corrected logic to use main.baseConfig
            main.baseConfig["settings"]['lastupdated'] = str(current_time)
            with open(main.configurationFilepath, "w") as configfile:
                # FIX: Write with the config object
                main.baseConfig.write(configfile)
        except Exception as e:
            await status_channel.send(f"⚠️ Config save error (Non-critical): {e}")

        await status_channel.send("Forced Update is complete!")
        await ctx.send("## Done!")

    async def softUpdate(self):
        """Runs a partial update (GDP and Happiness) for small edits."""
        await self.updateGDP()
        await self.updateHappiness()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(campaignUpdateFunctions(bot))