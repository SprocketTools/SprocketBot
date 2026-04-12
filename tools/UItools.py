import textwrap
import discord
from unicodedata import lookup
from discord.ext import commands
import os, platform, configparser, ast, json
import datetime, aiohttp
from PIL import Image, ImageChops, ImageDraw, ImageOps

import os
import asyncio
import io
import math
import subprocess
import discord
from PIL import Image
from discord.ext import commands
from typing import Literal, Union
import re
#import demjson3



class UItools:
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def getContestChoice(self, ctx: commands.Context, contestList: list, userPrompt: str):
        view = DropdownView(contestList)
        await ctx.send(content=userPrompt, view=view)
        await view.wait()
        return view.result

    async def getButtonChoice(self, ctx: commands.Context, inList: list):
        view = getButtonChoice(ctx, inList)
        messageOut = await ctx.send(view=view)
        await view.wait()
        try:
            await messageOut.delete()
        except discord.NotFound:
            pass  # Message was already deleted
        return view.value

    async def channel_block_check(self, channel_id: int, category: str) -> bool:
        if not category:
            return False
        try:
            result = await self.bot.sql.databaseFetchdictDynamic(
                '''SELECT * FROM channel_blocks WHERE channel_id = $1 AND category = $2;''',
                [channel_id, category.lower()]
            )
            if len(result) == 0:
                return False
            else:
                return True
        except Exception as ex:
            print(ex)
            print("consider running -setupChannelConfigTables")
            return False

    async def getButtonChoiceReturnID(self, ctx: commands.Context, inList: list):
        print(inList)
        try:
            view = getButtonChoiceReturnID_func(ctx, inList)
        except Exception as ex:
            print(ex)
            return None
        print(inList)
        msgOut = await ctx.send(view=view)
        await view.wait()
        await msgOut.delete()
        return view.id_out

    async def getYesNoChoice(self, ctx: commands.Context):
        view = YesNoButtons()
        await ctx.send(view=view)
        await view.wait()
        return view.value

    async def getYesNoModifyStopChoice(self, ctx: commands.Context):
        view = YesNoModifyStopButtons()
        await ctx.send(view=view)
        await view.wait()
        return view.value

    async def getResponse(self, ctx: commands.Context, prompt, action=None):
        promptMsg = await ctx.send(prompt)

        def check(m: discord.Message):
            return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id

        msg = await self.bot.wait_for('message', check=check, timeout=900)
        if msg.content.lower() == "cancel":
            raise ValueError("User termination")
        if action == "delete":
            await promptMsg.delete()
            await msg.delete()
        return msg.content

    async def getCategoryChoice(self, ctx: commands.Context, categoryList: list, userPrompt: str):
        chosen = False
        page = 0
        while not chosen:
            start_index = page * 20
            categoryListSlice = categoryList[start_index: start_index + 20]
            if not categoryListSlice:
                await ctx.send("No more options available.")
                return None

            view = categoryDropdownView(categoryListSlice, has_next_page=(len(categoryList) > start_index + 20))
            await ctx.send(content=userPrompt, view=view)
            await view.wait()
            result = view.result
            if result != "Next page":
                return result
            page += 1

    async def getContestTypeChoice(self, ctx: commands.Context):
        if ctx.channel.type is discord.ChannelType.private:
            return "Global"
        view = buttonConfirm()
        await ctx.send(content="Are you submitting into a global contest or a server-specific contest?", view=view)
        await view.wait()
        if view.value is None:
            await ctx.reply("Response timed out.")
        return "Global" if view.value else "Server"

    async def generate_jumpscare(self, ctx: commands.Context = None, memberin: discord.User = None,
                                 channelin: discord.TextChannel = None):
        """
        Modified to support both live commands and scheduled tasks.
        """
        memberin = memberin or (ctx.author if ctx else None)
        channelout = channelin or (ctx.channel if ctx else None)

        if not memberin or not channelout:
            print("[ERROR] Jumpscare failed: Target or Channel resolution failed.")
            return

        author_id = memberin.id
        avatar_url = memberin.display_avatar.url

        # 2. Permission Check (Only if ctx exists)
        # We wrap this in a check so it doesn't crash during automated replies
        if ctx and ctx.author.id != self.bot.owner_id:
            channelout = ctx.channel

        # --- FIX: Use Absolute Paths to prevent Windows confusion ---
        cwd = os.getcwd()
        temp_avatar_name = os.path.abspath(os.path.join(cwd, f"temp_avatar_{author_id}.png"))
        temp_output_name = os.path.abspath(os.path.join(cwd, f"final_output_{author_id}.gif"))
        background_path = os.path.abspath(os.path.join("assets", "jumpscare_background.gif"))
        shadow_path = os.path.abspath(os.path.join(cwd, "assets", "black_circle.png"))

        try:
            #await ctx.send("Generating your customized welcome...")

            # Download Avatar
            async with aiohttp.ClientSession() as session:
                async with session.get(avatar_url) as resp:
                    if resp.status != 200: return await ctx.send("Failed to download avatar.")
                    avatar_bytes = await resp.read()

            avatar_img = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")

            # 1. Force the image into a perfect square (512x512 is a good base)
            size = (280, 280)
            avatar_img = ImageOps.fit(avatar_img, size, Image.LANCZOS)

            # 2. Create a circular mask
            mask = Image.new('L', size, 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0) + size, fill=255)

            # 3. Apply the mask as the Alpha channel
            avatar_img.putalpha(mask)

            # 4. Save the "Circle Version" to the temp file
            avatar_img.save(temp_avatar_name)

            if not os.path.exists(shadow_path):
                return await ctx.send("Error: 'assets/shadow.png' is missing!")

            # Build the filter
            ffmpeg_filter = self._build_fade_overlay_filter()

            # --- FIX: Removed -loop to prevent 'Option not found' errors ---
            # We now handle the loop inside the filter_complex instead
            cmd = [
                'ffmpeg',
                '-threads', '0',
                '-i', background_path,
                '-i', temp_avatar_name,
                '-i', shadow_path,
                '-filter_complex', ffmpeg_filter,
                '-fps_mode', 'passthrough',  # Keeps the original background FPS
                '-y', temp_output_name
            ]

            process = await asyncio.to_thread(subprocess.run, cmd, capture_output=True, text=True)

            if process.returncode != 0:
                print(f"FFmpeg Error: {process.stderr}")
                return await ctx.send("FFmpeg failed to process the GIF.")

            await channelout.send(file=discord.File(temp_output_name, filename=f'jumpscare_{memberin.name}.gif'))

        finally:
            # Cleanup
            for f in [temp_avatar_name, temp_output_name]:
                if os.path.exists(f): os.remove(f)

    @staticmethod
    def _build_fade_overlay_filter() -> str:
        """
        High-Quality / Low-Resource Hybrid:
        - Internal loops for PNGs.
        - High-quality scaling (Lanczos).
        - Targeted PaletteGen (only scans the first 3s for perfect colors).
        - Smooth dithering (sierra2_4a) for the fade.
        """
        av_x, av_y = "55", "60"
        sh_x, sh_y = "35", "400"

        filter_str = (
            # Step A: Loop and Prep Avatar
            f"[1:v]loop=loop=-1:size=1:start=0,format=rgba,scale=280:280:flags=lanczos,fade=t=in:st=1.0:d=1.0:alpha=1[av_f];"

            # Step B: Loop and Prep Shadow
            f"[2:v]loop=loop=-1:size=1:start=0,format=rgba,scale=320:60:flags=lanczos,colorchannelmixer=aa=0.2,"
            f"fade=t=in:st=1.0:d=1.0:alpha=1[sh_f];"

            # Step C: Overlays
            f"[0:v][sh_f]overlay=x={sh_x}:y={sh_y}:shortest=1[bg_s];"
            f"[bg_s][av_f]overlay=x={av_x}:y={av_y}:shortest=1[v_c];"

            # Step D: Smart Palette (The Quality Fix)
            # trim=end=3 ensures it only spends CPU analyzing the intro fade
            f"[v_c]split[p_i][p_a];"
            f"[p_i]trim=end=3,palettegen=stats_mode=full:max_colors=256[pal];"
            f"[p_a][pal]paletteuse=dither=sierra2_4a:diff_mode=rectangle"
        )
        return filter_str

    async def getChoiceFromList(self, ctx: commands.Context, categoryList: list, userPrompt: str):
        categoryList = sorted(list(set(categoryList)))

        if len(categoryList) > 60:
            filtered_options = []
            while not filtered_options:
                options = ["AB", "CD", "EF", "GH", "IJ", "KL", "MN", "OP", "QR", "ST", "UV", "WX", "YZ", "No Sort",
                           "Search"]
                await ctx.send(f"There are {len(categoryList)} choices! Please filter them down.")
                sortChoice = await self.getButtonChoice(ctx, options)

                if sortChoice == "Search":
                    query = await self.getResponse(ctx, "Reply with your search query.")
                    filtered_options = [option for option in categoryList if query.lower() in option.lower()]
                elif sortChoice != "No Sort":
                    filtered_options = [option for option in categoryList if option and option[0].upper() in sortChoice]
                else:
                    filtered_options = categoryList  # Breaks the loop

                if not filtered_options:
                    await ctx.send("No options match your filter, please try again.")
                else:
                    categoryList = filtered_options

        if len(categoryList) == 0:
            return None
        if len(categoryList) == 1:
            return categoryList[0]

        page = 0
        while True:
            start_index = page * 20
            categoryListSlice = categoryList[start_index: start_index + 20]
            if not categoryListSlice:
                await ctx.send("No more options available.")
                return None

            view = listChoiceDropdownView(ctx, categoryListSlice, has_next_page=(len(categoryList) > start_index + 20))
            await ctx.send(content=userPrompt, view=view, ephemeral=True)
            await view.wait()
            result = view.result

            if result != "Next page":
                return result
            page += 1

    async def getDate(self, ctx: commands.Context, prompt: str) -> datetime.datetime:
        view = DateSelectorView(ctx)
        msg = await ctx.send(content=prompt, view=view)
        await view.wait()
        await msg.delete()
        return view.selected_date


# Note: The view/button classes below this point do not need `self` added to their methods
# unless they are calling other methods on the UItools instance. They are self-contained.
# --- Helper classes for UItools ---
class Dropdown(discord.ui.Select):
    def __init__(self, contestList):
        options = [discord.SelectOption(label=contest["name"], emoji='🏆', value=contest["name"]) for contest in
                   contestList]
        super().__init__(placeholder='Select an option here...', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        self.view.result = self.values[0]
        await interaction.response.defer()
        self.view.stop()


class DropdownView(discord.ui.View):
    def __init__(self, contestList):
        super().__init__()
        self.result = None
        self.add_item(Dropdown(contestList))


class buttonConfirm(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

    @discord.ui.button(label='Global', emoji='🌎', style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label='Server', emoji='🌆', style=discord.ButtonStyle.blurple)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        await interaction.response.defer()
        self.stop()


class categoryDropdown(discord.ui.Select):
    def __init__(self, categoryList, has_next_page=False):
        options = [discord.SelectOption(label=cat["categoryname"], emoji='🏆', value=cat["categoryname"]) for cat in
                   categoryList]
        if has_next_page:
            options.append(discord.SelectOption(label="Next page", emoji='➡️', value="Next page"))
        super().__init__(placeholder='Select an option here...', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        self.view.result = self.values[0]
        await interaction.response.defer()
        self.view.stop()


class categoryDropdownView(discord.ui.View):
    def __init__(self, categoryList, has_next_page=False):
        super().__init__()
        self.result = None
        self.add_item(categoryDropdown(categoryList, has_next_page))


class listChoiceDropdown(discord.ui.Select):
    def __init__(self, ctx: commands.Context, itemList, has_next_page=False):
        self.ctx = ctx
        options = []
        for item in itemList:
            emoji = '❔'
            if item and item[0].isalpha():
                emoji = chr(127462 + ord(item[0].upper()) - ord('A'))  # A-Z flag emojis
            options.append(discord.SelectOption(label=item, emoji=emoji, value=item))

        if has_next_page:
            options.append(discord.SelectOption(label="Next page", emoji='➡️', value="Next page"))
        super().__init__(placeholder='Select an option here...', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id == self.ctx.author.id:
            self.view.result = self.values[0]
            await interaction.response.defer()
            self.view.stop()
        else:
            await interaction.response.send_message(content="This menu is not for you.", ephemeral=True)


class listChoiceDropdownView(discord.ui.View):
    def __init__(self, ctx: commands.Context, categoryList, has_next_page=False):
        super().__init__()
        self.result = None
        self.add_item(listChoiceDropdown(ctx, categoryList, has_next_page))


class YesNoButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=360)
        self.value = None

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def callbackYes(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = True
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="No", style=discord.ButtonStyle.red)
    async def callbackNo(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = False
        await interaction.response.defer()
        self.stop()


class YesNoModifyStopButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=360)
        self.value = None

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green)
    async def callbackYes(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = "yes"
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="No", style=discord.ButtonStyle.red)
    async def callbackNo(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = "no"
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="Modify", style=discord.ButtonStyle.grey)
    async def callbackModify(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = "modify"
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.blurple)
    async def callbackStop(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = "stop"
        await interaction.response.defer()
        self.stop()


class buttonList(discord.ui.Button):
    def __init__(self, ctx: commands.Context, value: str, row: int):
        self.ctx = ctx
        style = discord.ButtonStyle.primary
        if value.lower() in ["exit", "0", "stop", "cancel"]:
            style = discord.ButtonStyle.red
        elif row % 2 == 0:
            style = discord.ButtonStyle.blurple
        else:
            style = discord.ButtonStyle.green
        super().__init__(style=style, label=value, row=row)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id == self.ctx.author.id:
            self.view.value = self.label
            await interaction.response.defer()
            self.view.stop()
        else:
            await interaction.response.send_message(content="This button is not for you.", ephemeral=True)


class getButtonChoice(discord.ui.View):
    def __init__(self, ctx: commands.Context, listIn: list):
        super().__init__(timeout=600)
        self.value = None
        for i, item in enumerate(listIn):
            self.add_item(buttonList(ctx, item, i // 5))





class buttonListReturnID(discord.ui.Button):
    # https://github.com/Rapptz/discord.py/blob/master/examples/views/tic_tac_toe.py
    def __init__(self, ctx: commands.Context, value: str, id_in: str, pos: int):
        self.id_out = id_in
        self.value = value
        self.row = int(pos/5)
        self.ctx = ctx
        if value.lower() in ["exit", "0", "stop", "return", "only a catgirl would say that", "insult", "attack"]:
            super().__init__(style=discord.ButtonStyle.red, label=value, row=self.row)
        elif value.lower() in ["cancel", "GIF"]:
            super().__init__(style=discord.ButtonStyle.grey, label=value, row=self.row)
        elif pos % 2 == 0:
            super().__init__(style=discord.ButtonStyle.green, label=value, row=self.row)
        else:
            super().__init__(style=discord.ButtonStyle.blurple, label=value, row=self.row)

    async def callback(self, interaction: discord.Interaction):
        print(interaction.user)
        print(interaction.message.author)
        if interaction.user == self.ctx.author:
            assert self.view is not None
            view: getButtonChoiceReturnID_func = self.view
            self.view.id_out = self.id_out
            await interaction.response.defer()
            view.stop()
        else:
            await interaction.response.send_message(content="### Ouchie!  \n[Don't touch my buttons, they aren't yours!](<https://www.youtube.com/watch?v=a6pbjksYUHY>)\n", ephemeral=True)

class getButtonChoiceReturnID_func(discord.ui.View):
    value = ""
    def __init__(self, ctx: commands.Context, listIn: list):
        super().__init__(timeout=600)
        self.list = listIn
        for i, item in enumerate(listIn):
            self.add_item(buttonListReturnID(ctx, item[0], item[1], i))

class DayInputModal(discord.ui.Modal, title="Click here to enter day"):
    day_input = discord.ui.TextInput(
        label="Day of Month",
        placeholder="e.g. 15",
        min_length=1,
        max_length=2,
        required=True
    )

    def __init__(self, view):
        super().__init__()
        self.view = view

    async def on_submit(self, interaction: discord.Interaction):
        try:
            val = int(self.day_input.value)
            if 1 <= val <= 31:
                self.view.day = val
                # Update button visual to show selected day
                self.view.btn_set_day.label = f"Day: {val}"
                self.view.btn_set_day.style = discord.ButtonStyle.success
                await interaction.response.edit_message(view=self.view)
            else:
                await interaction.response.send_message("Day must be between 1 and 31.", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("Please enter a valid number.", ephemeral=True)

class DateSelectorView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.selected_date = None
        self.month = None
        self.day = None
        self.year = None

        # --- Row 0: Quick Select Buttons ---

        # --- Row 1: Month Select ---
        months = ["January", "February", "March", "April", "May", "June",
                  "July", "August", "September", "October", "November", "December"]
        self.month_select = discord.ui.Select(
            placeholder="Select Month",
            options=[discord.SelectOption(label=m, value=str(i + 1)) for i, m in enumerate(months)],
            row=1
        )
        self.month_select.callback = self.month_callback
        self.add_item(self.month_select)

        # --- Row 2: Year Select ---
        current_year = datetime.datetime.now().year
        self.year_select = discord.ui.Select(
            placeholder="Select Year",
            options=[discord.SelectOption(label=str(y), value=str(y)) for y in range(current_year, current_year + 5)],
            row=2
        )
        self.year_select.callback = self.year_callback
        self.add_item(self.year_select)

    # --- QUICK SET BUTTONS (Row 0) ---
    @discord.ui.button(label="1 day from now", style=discord.ButtonStyle.blurple, row=0)
    async def quick_1_day(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author: return
        self.selected_date = datetime.datetime.now() + datetime.timedelta(days=1)
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="1 week from now", style=discord.ButtonStyle.blurple, row=0)
    async def quick_1_week(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author: return
        self.selected_date = datetime.datetime.now() + datetime.timedelta(weeks=1)
        await interaction.response.defer()
        self.stop()

    @discord.ui.button(label="1 month from now", style=discord.ButtonStyle.blurple, row=0)
    async def quick_1_month(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author: return
        # Approximate 1 month as 30 days
        self.selected_date = datetime.datetime.now() + datetime.timedelta(days=30)
        await interaction.response.defer()
        self.stop()

    # --- CUSTOM SELECTION HANDLERS ---
    async def month_callback(self, interaction: discord.Interaction):
        self.month = int(self.month_select.values[0])
        await interaction.response.defer()

    async def year_callback(self, interaction: discord.Interaction):
        self.year = int(self.year_select.values[0])
        await interaction.response.defer()

    # --- MANUAL ENTRY (Row 3 & 4) ---

    @discord.ui.button(label="Set Day", style=discord.ButtonStyle.secondary, row=3)
    async def btn_set_day(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author: return
        # Open the modal
        await interaction.response.send_modal(DayInputModal(self))

    @discord.ui.button(label="Confirm Custom Date", style=discord.ButtonStyle.green, row=4)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author: return

        if not self.month or not self.day or not self.year:
            return await interaction.response.send_message("❌ Please select a Month, Day, and Year.", ephemeral=True)

        try:
            # Attempt to create date
            dt = datetime.datetime(self.year, self.month, self.day)

            # Check if in past
            if dt < datetime.datetime.now():
                return await interaction.response.send_message("❌ Deadline cannot be in the past!", ephemeral=True)

            self.selected_date = dt
            await interaction.response.defer()
            self.stop()

        except ValueError:
            await interaction.response.send_message("❌ Invalid date (e.g., February 30th). Please correct it.",
                                                    ephemeral=True)

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.grey, row=4)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user != self.ctx.author: return
        self.selected_date = None
        await interaction.response.defer()
        self.stop()