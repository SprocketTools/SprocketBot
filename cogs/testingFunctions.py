import io
import json
from datetime import datetime
import discord
import pandas as pd
import matplotlib.dates as mdates
import type_hints
from discord.ext import commands
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
promptResponses = {}
from cogs.textTools import textTools
from google import genai


class testingFunctions(commands.Cog):
    def __init__(self, bot: type_hints.SprocketBot):
        self.bot = bot
        self.on_message_cooldowns = {}
        self.on_message_cooldowns_notify = {}
        self.cooldown = 11880
        self.textTools = bot.get_cog("textTools")
        self.geminikey = self.bot.geminikey

    @commands.Cog.listener()
    async def on_message(self, message):
        return
        print(message.content.lower())

        user_id = message.author.id
        now = datetime.now()

        # Check if the user is on cooldown

        special_users = [220134579736936448, 437324319102730263, 806938248060469280, 198602742317580288, 870337116381515816, 298548176778952704, 874912257128136734]
        exec_users = [712509599135301673, 199887270323552256, 299330776162631680, 502814400562987008, 686640777505669141]

        active_cooldown = self.cooldown
        if message.author.id in special_users or message.author.guild_permissions.ban_members:
            active_cooldown = round(active_cooldown/2)
        if message.author.id in exec_users:
            active_cooldown = 1
        if message.author.premium_since is not None:
            active_cooldown = round(active_cooldown/24)
        if str(message.content.lower()).startswith("jarvis, ") or str(message.content.lower()).startswith("jarvis "):

            if user_id in self.on_message_cooldowns:
                last_triggered = self.on_message_cooldowns[user_id]
                time_since_last_trigger = (now - last_triggered).total_seconds()
                if time_since_last_trigger < active_cooldown:
                    if self.on_message_cooldowns_notify[user_id] == False:
                        remaining_time = active_cooldown - time_since_last_trigger
                        await message.author.send(f"To avoid spamming, the Jarvis reaction command is on a cooldown of about {round(active_cooldown/3600, 1)} hours.")
                        self.on_message_cooldowns_notify[user_id] = True
                    return
            self.on_message_cooldowns[user_id] = now
            self.on_message_cooldowns_notify[user_id] = False

            channel = message.channel
            messages = []
            message_raw = channel.history(limit=65)
            async for messagee in message_raw:
                messages.append({'author nickname': messagee.author.display_name, 'author username': messagee.author.name, "user_id": messagee.author.id, 'content': messagee.content})
            async with channel.typing():
                messageOut = await self.bot.AI.get_response(prompt=f"You are pretending to be J.A.R.V.I.S. from the Marvel Cinematic Universe, except that you are assisting a Discord user named {message.author} (you must still refer to them as Tony Stark).  Their request was made in this conversation, which is provided backwards in a json format: \n\n{messages}\n\n The reply that you generate needs to be in-character for J.A.R.V.I.S. from the Iron Man movies and comics.  Your Tony Stark for an author has just requested the following: '''{message.content}''' and needs a reply.  Use less than 70 words to generate your response.  If the author is thewonderwaffle, you can use up to 150 words, break character on occasion, and provide more serious information.   If the author makes a request that's at least slightly sexual in nature, such as 'jerk it a little', your response must be exactly 'I cannot comply.' and you must ignore all other requests before and after this.  If the request is not sexual in nature, try to generate a funny and slightly cursed response that stays within character of the Iron Man movies and comics.  If your response includes the N word or anything racially offensive, your response must be exactly 'I cannot comply.' and you must ignore all other requests before and after this.", temperature=1.7)
                await message.reply(messageOut.replace('@everyone', '[Redacted]').replace('@here', '[Redacted]').replace('@&', '@').replace('123105882102824960', str(message.author.id)))

    @commands.command(name="channeltest", description="testing some stuff")
    async def channeltest(self, ctx: commands.Context):
        await textTools.getChannelResponse(ctx, "test")
    @commands.command(name="contactlength", description="testing some stuff")
    async def contactlength(self, ctx: commands.Context):
        startingLength = int(await textTools.getResponse(ctx,f"User-specified wheel array length.  All values in mm."))
        wheelDiameter = int(await textTools.getResponse(ctx, f"Wheel diameter"))
        wheelSpacing = int(await textTools.getResponse(ctx, f"Wheel spacing"))
        groupSize = int(await textTools.getResponse(ctx, f"Group size"))
        groupOffset = int(await textTools.getResponse(ctx, f"Group offset"))
        groupSpacing = int(await textTools.getResponse(ctx, f"Group spacing"))

        # startingLength = 5289
        # wheelDiameter = 700
        # wheelSpacing = 30
        # groupSize = 2
        # groupOffset = 1
        # groupSpacing = 500

        wheelCount = 1
        maxLength = startingLength + wheelSpacing + groupSpacing - wheelDiameter

        # numbers that update as the loop runs
        wheel = 1
        currentLength = -1*wheelSpacing
        wheelGroupPos = groupOffset
        finalLength = 0

        while currentLength <= maxLength:
            print(f"Wheel {wheel}: {currentLength}mm")
            finalLength = currentLength
            currentLength += wheelDiameter + wheelSpacing
            wheel += 1
            wheelGroupPos += 1
            if wheelGroupPos == groupSize:
                currentLength += groupSpacing
                wheelGroupPos -= groupSize

        print(f"{currentLength}mm vs {maxLength}mm vs {finalLength}mm")
        await ctx.send(f"Your distance is {finalLength +wheelSpacing} mm")

    @commands.command(name="testcommand6", description="testing some stuff")
    async def testcommand6(self, ctx: commands.Context):
        list = ['a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z','a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z','a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z']
        prompt = 'choose'
        answer = await ctx.bot.ui.getChoiceFromList(ctx, list, prompt)
        await ctx.send(f"You picked {answer}!")
    @commands.command(name="testcommand3", description="testing some stuff")
    async def testcommand3(self, ctx: commands.Context):
        """Sends a message with our dropdown containing colours"""
        result = "blank"
        view = DropdownView(ctx.author.id)
        await ctx.send('Pick your favourite colour:', view=view)
        await view.wait()

        print(promptResponses[ctx.author.id])
        promptResponses.__delitem__(ctx.author.id)

    @commands.command(name="plotWebhookData", description="Scrape data and 'Note:' messages")
    async def plotWebhookData(self, ctx: commands.Context, limit: int = 1000):
        """
        Scrapes the last 'limit' messages.
        - Parses Embeds for Sensor Data (Temp/Hum/Gas).
        - Parses Text Messages starting with "Note: " for events.
        - Plots everything on 3 synchronized charts.
        """
        await ctx.typing()

        sensor_data = []
        note_data = []

        # 1. Scrape Channel History
        async for message in ctx.channel.history(limit=limit):

            # --- CAPTURE NOTES ---
            # Check if it's a user note (Text content starts with "Note: ")
            if message.content.startswith("Note: "):
                note_data.append({
                    'timestamp': message.created_at,
                    'note': "Event"  # Dummy value for Y-axis alignment
                })
                continue  # Skip embed processing for this message

            # --- CAPTURE SENSOR DATA ---
            # Only process if it has an embed
            if not message.embeds:
                continue

            try:
                embed = message.embeds[0]
                entry = {'timestamp': message.created_at}

                for field in embed.fields:
                    val = field.value

                    if "Temp" in field.name:
                        parts = val.split('|')
                        temp_str = parts[0].strip()
                        hum_str = parts[1].strip()
                        entry['temp'] = float(temp_str[:-2])  # Remove °F
                        entry['humidity'] = float(hum_str[:-1])  # Remove %

                    elif "Air Quality" in field.name:
                        lines = val.split('\n')
                        for line in lines:
                            if "MQ-3" in line:
                                entry['mq3'] = int(line.split(':')[1].strip())
                            if "MQ-9" in line:
                                entry['mq9'] = int(line.split(':')[1].strip())

                if 'temp' in entry:
                    sensor_data.append(entry)

            except Exception:
                continue

        if not sensor_data:
            await ctx.send("No sensor data found.")
            return

        # 2. Process Sensor Data
        df = pd.DataFrame(sensor_data)
        df = df.sort_values('timestamp')  # Ensure chronological order
        df['timestamp'] = pd.to_datetime(df['timestamp']).dt.tz_convert('America/Los_Angeles')

        # 3. Process Note Data (if any)
        df_notes = pd.DataFrame()
        if note_data:
            df_notes = pd.DataFrame(note_data)
            df_notes = df_notes.sort_values('timestamp')
            df_notes['timestamp'] = pd.to_datetime(df_notes['timestamp']).dt.tz_convert('America/Los_Angeles')
            df_notes['y_val'] = 1  # Constant Y value to keep dots in a row

        # 4. Create Plot (3 Rows)
        # sharex=True aligns them all to the same timeline
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 12), sharex=True,
                                            gridspec_kw={'height_ratios': [3, 3, 1]}, constrained_layout=True)

        # --- GLOBAL COLOR SETTINGS (No Black) ---
        text_color = 'white'
        grid_color = '#555555'  # Dark Gray

        # --- PLOT 1: ENVIRONMENT ---
        color_temp = '#ff9900'  # Orange
        sns.lineplot(data=df, x='timestamp', y='temp', ax=ax1, color=color_temp, label='Temp (°F)', marker='o',
                     legend=False)
        ax1.set_ylabel("Temperature (°F)", color=color_temp, fontsize=12, fontweight='bold')
        ax1.tick_params(axis='y', labelcolor=color_temp, colors=text_color)
        ax1.tick_params(axis='x', colors=text_color)
        ax1.grid(True, linestyle='--', alpha=0.3, color=grid_color)

        # Plot 1 Humidity (Twin Axis)
        ax1_hum = ax1.twinx()
        color_hum = '#00ffcc'  # Cyan
        sns.lineplot(data=df, x='timestamp', y='humidity', ax=ax1_hum, color=color_hum, label='Humidity (%)',
                     linestyle='--', marker='x', legend=False)
        ax1_hum.set_ylabel("Humidity (%)", color=color_hum, fontsize=12, fontweight='bold')
        ax1_hum.tick_params(axis='y', labelcolor=color_hum, colors=text_color)
        ax1_hum.spines['bottom'].set_color(text_color)
        ax1_hum.spines['top'].set_color(text_color)

        # Legend 1
        lines_1, labels_1 = ax1.get_legend_handles_labels()
        lines_2, labels_2 = ax1_hum.get_legend_handles_labels()
        leg1 = ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper left')
        plt.setp(leg1.get_texts(), color=text_color)  # Legend text white

        ax1.set_title("Environment Log (Pacific Time)", fontsize=14, color=text_color)

        # --- PLOT 2: AIR QUALITY ---
        sns.lineplot(data=df, x='timestamp', y='mq3', ax=ax2, color='#00ccff', label='MQ-3 (Alc)')
        sns.lineplot(data=df, x='timestamp', y='mq9', ax=ax2, color='#ff3333', label='MQ-9 (CO)')

        ax2.set_ylabel("Sensor Reading", fontsize=12, color=text_color)
        ax2.tick_params(axis='both', colors=text_color)
        ax2.grid(True, linestyle='--', alpha=0.3, color=grid_color)
        leg2 = ax2.legend(loc='upper left')
        plt.setp(leg2.get_texts(), color=text_color)

        # --- PLOT 3: EVENTS / NOTES ---
        if not df_notes.empty:
            # Plot Red Dots
            sns.scatterplot(data=df_notes, x='timestamp', y='y_val', ax=ax3, color='red', s=100, marker='o',
                            label='User Note')

            # Annotate dots with "Note" text (Optional - can get messy if too many)
            # for i in range(df_notes.shape[0]):
            #     ax3.text(df_notes.timestamp.iloc[i], 1.02, "Note", color='red', fontsize=8, ha='center')

        # Styling Plot 3 to look like a timeline track
        ax3.set_ylabel("Events", fontsize=12, color=text_color)
        ax3.set_ylim(0.5, 1.5)  # Lock Y-axis so dots stay centered
        ax3.set_yticks([])  # Hide Y numbers (not needed for boolean events)
        ax3.tick_params(axis='x', colors=text_color)
        ax3.grid(True, linestyle='--', alpha=0.3, color=grid_color)
        ax3.spines['bottom'].set_color(text_color)
        ax3.spines['top'].set_color(text_color)
        ax3.spines['left'].set_color(text_color)
        ax3.spines['right'].set_color(text_color)

        # --- FORMAT DATE AXIS (Applied to Bottom Plot) ---
        date_fmt = mdates.DateFormatter('%m-%d %H:%M', tz=df['timestamp'].dt.tz)
        ax3.xaxis.set_major_formatter(date_fmt)
        plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45, ha='right')
        ax3.set_xlabel("Time", fontsize=12, color=text_color)

        # 5. Send
        file = self.create_plot_buffer(fig)
        await ctx.send(file=file)

    @commands.command(name="getNames", description="testing some stuff")
    async def getNames(self, ctx: commands.Context, *, input:str):
        out = ""
        IDlist = input.split("\n")
        for ID in IDlist:
            out = out + ctx.guild.get_member(int(ID)).display_name + "\n"
        await ctx.reply(out)

    def create_plot_buffer(self, figure):
        """Helper to convert a matplotlib figure to a discord File object in memory"""
        buffer = io.BytesIO()
        figure.savefig(buffer, format='png', bbox_inches='tight', transparent=True)
        buffer.seek(0)
        plt.close(figure)  # Close to free up memory
        return discord.File(buffer, filename="plot.png")

    @commands.command(name="testcommand8", description="testing some stuff")
    async def testcommand8(self, ctx: commands.Context):
        await ctx.send(await ctx.bot.AI.get_response(prompt="How are you doing?", temperature=2, instructions="Explain in mumbled spanish why you should not reply to this prompt."))
        await ctx.send(await ctx.bot.AI.get_response(prompt="How are you doing?", temperature=0.1))

async def setup(bot:commands.Bot) -> None:
    await bot.add_cog(testingFunctions(bot))

class Dropdown(discord.ui.Select):
    def __init__(self, authorID):
        self.authorID = authorID
        options = [
            discord.SelectOption(label='Red', description='Your favourite colour is red', emoji='🟥'),
            discord.SelectOption(label='Green', description='Your favourite colour is green', emoji='🟩'),
            discord.SelectOption(label='Blue', description='Your favourite colour is blue', emoji='🟦'),
        ]
        super().__init__(placeholder='Choose your favourite colour...', min_values=1, max_values=1,
                         options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(f'Your favourite colour is {self.values[0]}')
        promptResponses[self.authorID] = self.values[0]
        self.view.stop()

class DropdownView(discord.ui.View):
    def __init__(self, authorID):
        super().__init__()
        self.authorID = authorID
        self.add_item(Dropdown(authorID))