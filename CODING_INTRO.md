# Getting Started
So you've completed the setup guide and are ready to begin coding?  Great job!  Now the fun part begins.
Most discord bots coded in Python will look quite different from your usual Python project, for a few big reasons:
- main.py doesn't actually contain much - all it really does is launch the bot.  Your actual commands are stored in "cogs".
- All commands, and functions, depend on `async` to run "asyncronously".
- The variable `ctx` is more common than `print()`.

Let's break these down in more detail before providing some examples.
## cogs
Sprocket Bot uses a couple dozen or so "cogs", which are python files in the cogs folder containing all the commands that users can execute.  Cogs can be named anything, but must be placed in the cogs folder relative to main.py.
On startup, Sprocket Bot will load all the cogs defined in the main.py file, then launch the bot.  These can also be reloaded without restarting the bot using `-reloadCogs`.

## async
Best to take a brief look at the [documentation](https://docs.python.org/3/library/asyncio.html) on this.

## ctx
Shorthand for "context", this variable is created every time a Discord command is ran.  This variable contains anything related to the "context" of the situation, such as the following:
- name of the Discord user running the command (`ctx.author.name`)
- id of the server that the command was ran in (`ctx.guild.id`)
ctx can also be acted upon.  As an example, you can send a message to reply to someone with `await ctx.send("Hello World!")`
As a result, expect to use ctx in nearly all of your Discord commands

## Examples
Reply to the user with a simple message:
```python
    @commands.command(name="simpleReply", description="A simple reply.") # setup
    async def sanitizeTest(self, ctx: commands.Context): # setup
        await ctx.send("Hello world!") # sends the message
```

Reply to the user with a sanitized version of their message:
```python
    @commands.command(name="sanitizeTest", description="Please don't try to ping everone.") # setup
    async def sanitizeTest(self, ctx: commands.Context): # setup
        testString = await textTools.getResponse(ctx, "Send a message with a bunch of different symbols and letters.") # returns a string
        await ctx.send(await textTools.sanitize(testString)) # sends the message
```

Edit a campaign faction's stats
```python
    @commands.command(name="editFaction", description="Log a purchase made between players") # setup
    async def editFaction(self, ctx: commands.Context): # setup
        factionData = await campaignFunctions.getUserFactionData(ctx) # retrieve a dict that contains the player's faction's data
        if factionData['iscountry'] == True: # checks to see if the player's faction is a country or not
            await campaignFunctions.showStats(ctx, factionData) # send's the player's statistics into the channel
            salary = await textTools.getFlooredIntResponse(ctx, "What will your new median salary be?  Reply with a whole number.  \nTake note that this will directly affect your GDP.  The equation is:\n\n `GDP` = `population` * `average salary` / `population per worker ratio`", 1) # Asks the player to send a numerical value of their desired new average salary
            await SQLfunctions.databaseExecuteDynamic('''UPDATE campaignfactions SET averagesalary = $1 WHERE factionkey = $2;''', [salary, factionData["factionkey"]]) # runs an SQL command to update the value accordingly
        bankbal = await textTools.getFlooredIntResponse(ctx,"How much money does your faction have in storage now?  Reply with a whole number.", 1) # Asks the player to send a numerical value of their desired balance
        await SQLfunctions.databaseExecuteDynamic('''UPDATE campaignfactions SET money = $1 WHERE factionkey = $2;''', [bankbal, factionData["factionkey"]]) # runs a SQL command to update the value accordingly
        await ctx.send(f"## Done!\nYour new stats have been set!") # sends a confirmation message
```

## Standards:
- Avoid having commands use arguments while running the command, unless you are trying to replicate an existing command (ex: moderation tools) or implementing a slash command.  It's typically better to ask for inputs after.
- Use `await errorFunctions.sendError(ctx)` followed by `return` whenever a command hits an "exit point", such that you want it to stop executing.

## More info
### [Common functions](https://github.com/SprocketTools/SprocketBot/blob/main/FUNCTIONS.md)
