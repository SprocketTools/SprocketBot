# Sprocket Bot functions

Sprocket Bot uses a wide range of functions to help simplify its code, reducing frequent multi-line code sections into a single line.  Below is a non-exhaustive list of those functions:
- `textTools.sanitize(str)`
    - Takes a string and removes potentially invalid characters from it, returning that "sanitized" string
        - `str`: string
- `textTools.mild_sanitize(str)`
    - The same as `sanitize`, but it only strips the symbols `@` and `;`.  Both of these symbols have the potential to cause issues with the bot.  All user input processed through functions shown later apply this sanitation
- `textTools.getResponse(ctx, prompt)`
    - This function asks the user for an input, using the prompt as the question, and returns a sanitized string value with no limit on its length.
        - `prompt`: string
    - All of the response functions will use this similar format, with different behaviors to suit different tasks.
    ```python
        @commands.command(name="adminGetTable", description="add a column to a SQL table")
        async def adminGetTable(self, ctx: commands.Context):
            if ctx.author.id == main.ownerID:
                await errorFunctions.sendError(ctx)
                return
            tablename = await errorFunctions.getResponse(ctx, "What is the table name?")
            await ctx.send(await SQLfunctions.databaseFetchdict(f"SELECT * FROM {tablename};"))
    ```
- `textTools.getCappedResponse(ctx, prompt, length)`
    - This function asks the user for an input, and returns a sanitized string value.  If the length of the user input exceeds the defined length, the command will try again.  This is recommended for most use cases, as string inputs shouldn't be so long that the bot cannot resend it.
        - `length`: integer
- `textTools.getIntResponse(ctx, prompt)`
    - A prompt function that returns an integer of any value.
- `textTools.getFlooredIntResponse(ctx, prompt, min)`
    - A prompt function that either returns the input integer `min`, or the user's input if it's bigger.  Useful to avoid negative number inputs.
- `textTools.getFloatResponse(ctx, prompt)`
    - A prompt function that returns a float of any value.
- `textTools.getFlooredFloatResponse(ctx, prompt, min)`
    - A prompt function that either returns the input float `min`, or the user's input if it's bigger.  Useful to avoid negative number inputs.
- `textTools.getPercentResponse(ctx, prompt)`
    - A prompt function that returns a ratio equivalent of a percentage input.  Note that the returned value will be divided by 100 compared to the user's input.
- `textTools.getChannelResponse(ctx, prompt)`
    - A prompt function that returns a channel ID.
- `textTools.getRoleResponse(ctx, prompt)`
    - A prompt function that returns a role ID.  Useful for restricting things to a specific role.
- `textTools.getFileResponse(ctx, prompt)`
    - A prompt function that returns a single Discord file attachment.  Useful for things like processing images.
- `textTools.getFileURLResponse(ctx, prompt)`
    - The same as `getFileResponse`, but it returns a URL to that file, instead of the file itself.  Useful for embedding images.
- `textTools.getManyFilesResponse(ctx, prompt)`
    - The same as `getFileResponse`, but instead returns a list of up to 10 discord file attachments.
- `textTools.getResponseThenDelete(ctx, prompt)`
    - The same as `getResponse`, but it immediately deletes the user's reply after sending it.  
- `textTools.addLine(inputOne, inputTwo):`
    - This function returns a string consisting of the two input strings merged together, with a newline seperator between them.
        - `inputOne`: string
        - `inputTwo`: string
- `errorFunctions.retrieveError(ctx):`
    - This function returns with a randomly-generated "error message" that is meant to add some humor to the bot.  
- `errorFunctions.sendError(ctx):`
    - This function sends a randomly-generated "error message."  Use this whenever an error occurs.  
- `SQLfunctions.databaseExecute(prompt)`
    - This function lets you perform a SQL operation on the SQL database.
        - `prompt`: string (specifically your SQL prompt)
- `SQLfunctions.databaseExecuteDynamic(prompt, values)`
    - This function performs a prepared SQL operation, where values are substituted into the SQL function to avoid SQL attacks.
        - `values`: list - the values need to align with the function
    ```python
        @commands.command(name="clearCampaignFactions", description="Remove all factions from a campaign")
        async def clearCampaignFactions(self, ctx: commands.Context):
            if campaignFunctions.isCampaignHost(ctx) == False:
                await ctx.send(await errorFunctions.retrieveError(ctx))
                return
            campaignData = await campaignFunctions.getUserCampaignData(ctx)
            campaignKey = campaignData["campaignkey"]
            await SQLfunctions.databaseExecuteDynamic('''DELETE FROM campaignfactions WHERE campaignkey = $1;''', [campaignKey])
            await SQLfunctions.databaseExecuteDynamic('''DELETE FROM campaignusers WHERE campaignkey = $1;''', [campaignKey])
            await ctx.send("## Done!\nYour campaign has been cleared of all factions.")
    ```
- `SQLfunctions.databaseFetch(prompt)`
    - This function lets you retrieve SQL data from the database.
- `SQLfunctions.databaseFetchDynamic(prompt, values)`
    - This function lets you use a prepared SQL operation to retrieve data.
- `SQLfunctions.databaseFetchdict(prompt)`
    - This function lets you use a SQL operation to retrieve data.  Data is formatted and returned as a dict.
- `SQLfunctions.databaseFetchrow(prompt)`
    - This function lets you use a SQL operation to retrieve data.  The first row of data is formatted and returned as a dict.
- `SQLfunctions.databaseFetchlist(prompt)`
    - This function lets you use a SQL operation to retrieve data.  The first row of data is formatted and returned as a list.
- `SQLfunctions.databaseFetchdictDynamic(prompt, values)`
    - This function lets you use a prepared SQL operation to retrieve data.  Data is formatted and returned as a dict.
    ```python
        @commands.command(name="errorLeaderboard", description="Leaderboard of errors!")
        async def errorLeaderboard(self, ctx: commands.Context):
            totalErrors = len(await SQLfunctions.databaseFetchdict(f'SELECT error FROM errorlist;'))
            embed = discord.Embed(title="Error Stats", description=f'''There are {totalErrors} error messages in the bot's collection!''',color=discord.Color.random())
            userSetList = await SQLfunctions.databaseFetchdict(f'''SELECT userid, COUNT(userid) AS value_occurrence FROM errorlist GROUP BY userid ORDER BY value_occurrence DESC LIMIT 5;''')
            for user in userSetList:
                embed.add_field(name=self.bot.get_user(user['userid']), value=user['value_occurrence'], inline=False)
            currentUser = (await SQLfunctions.databaseFetchdictDynamic(f'''SELECT userid, COUNT(userid) AS value_occ FROM errorlist WHERE userid = $1 GROUP BY userid;''', [ctx.author.id]))[0]['value_occ']
            print(currentUser)
            embed.set_footer(text=f"You have {currentUser} errors registered with the bot!")
            await ctx.send(embed=embed)
        ```
- `SQLfunctions.databaseFetchrowDynamic(prompt, values)`
    - This function lets you use a prepared SQL operation to retrieve data.  The first row of data is formatted and returned as a dict.
- `SQLfunctions.databaseFetchlistDynamic(prompt, values)`
    - This function lets you use a prepared SQL operation to retrieve data.  The first row of data is formatted and returned as a list.
- `discordUIfunctions.getYesNoChoice(ctx)`
    - Returns a true or false boolean depending on user input.
- `discordUIfunctions.getYesNoModifyStopChoice(ctx)`
    - Returns a string corresponding to the user's input.  Possible returns are `yes`, `no`, `modify`, or `stop`.
- `discordUIfunctions.getChoiceFromList(ctx, optionlist, prompt)`
    - This function asks the user to select an option, and returns a string of that option once the user selects it.
        - `optionlist`: list - string list of options
        - `prompt`: string - the question given to the user
- `campaignFunctions.getUserFactionData(ctx)`
    - This function asks the user to pick a faction, then returns a dict containing data about that faction.
- `campaignFunctions.getFactionData(factionkey)`
    - This function returns a dict containing data about the faction corresponding to the input key.
        - `factionkey`: int
- `campaignFunctions.getFactionName(factionkey)`
    - This function returns a string containing the name of the faction corresponding to the input key.
        - `factionkey`: int
- `campaignFunctions.pickCampaignFaction(ctx, prompt)`
    - This function asks the user to select a campaign faction of their choice.  It then returns both the name of the faction, and a dict containing its data.
- `campaignFunctions.pickCampaignCountry(ctx, prompt)`
    - Similar to `pickCampaignFaction`, except that it only allows selecting countries.
- `campaignFunctions.getUserCampaignData(ctx)`
    - This function returns a dict containing data about the server's campaign's settings.  
- `campaignFunctions.getGovernmentType(ctx)`
    - This function returns a float value between 0.8 and 1.2 based upon the government type that the user selects.  Use this value to determine other statistics when setting up a country.
- `campaignFunctions.getGovernmentName(ctx)`
    - Basically the inverse of `getGovernmentType` - it takes in the scalar value and returns the corresponding name of the government type, ex: "Direct Democracy".
- `campaignFunctions.getFarmingLatitudeScalar(ctx)`
    - This function takes in a degree number between -90 and 90, and returns a scalar between 1 and 0.25.  Use this to determine debuffs to polar countries, such as for their factory efficiency.
- `campaignFunctions.showFinances(ctx, variablesList)`
    - This function sends an embedded message showing the financial situation of countries based on the variables list.  Companies will not have their stats displayed.
        - `variablesList`: dict - this should contain all the data that is spat out by functions like `getFactionData`
- `campaignFunctions.showStats(ctx, variablesList)`
    - This function sends an embedded message showing general statistics for companies and countries in a campaign.
- `campaignFunctions.getCampaignName(campaignkey)`
    - This function returns the name of a campaign based on the input key.
        - `campaignkey`: int
- `campaignFunctions.getCampaignKey(ctx)`
    - This function returns the campaign key (as an integer) of the server's campaign.
- `campaignFunctions.isCampaignManager(ctx)`
    - This function returns a boolean for if the user is a campaign manager (within the server) or not.  Use this to restrict actions based on whether a user has adequate permissions or not.
- `campaignFunctions.isCampaignHost(ctx)`
    - This function returns a boolean for if the user is a manager of the server's campaign or not.  This function will only return true if ran inside the server that owns the ongoing campaign.  Use this to restrict actions based on whether a user has adequate permissions or not.
