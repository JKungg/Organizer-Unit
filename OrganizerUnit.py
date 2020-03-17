import discord, asyncio, os, random, time, json, requests, sqlite3, pickle
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from discord.ext import commands, tasks
from bs4 import BeautifulSoup

token = os.environ.get('DiscordToken')

client = commands.Bot(command_prefix = '.')
client.remove_command('help')

db = sqlite3.connect('discordVariables.sqlite')
cursor = db.cursor()


# TODO: Add Checks for Role, make sure the user has x role to use commands.


@client.command()
async def help(ctx):
    await ctx.send("""```css
        
        [*] Every Monday at around 12:25 your teams matches will be posted to the desired channel!

        [*] ".setchannel" (channel name)
            Set the channel you want to have your matches and scrims posted in.

        [*] ".setteam" (Team Name)
            Set your Team Name as spelt on the VRML Website.

        [*] ".setscrim" (Day, Time)
            Will post in desired channel your scrim time.

        [*] ".setmatch" (Day, Time)
            Will post in desired channel your game time.

        [*] ".sremind" (15, minutes)
            Will post in desired channel the time before your scrim.
            Coming soon > Automatic Reminding

        [*] ".sendmatch"
            Will send the matches you have throughout the week.
        ```""")

@client.command()
async def info(ctx):
    
    cursor.execute(f"""SELECT team FROM main WHERE guild_id = {ctx.guild.id}""")
    teaminfo = cursor.fetchone()
    team = teaminfo[0]

    cursor.execute(f"SELECT server_name FROM main WHERE guild_id = {ctx.guild.id}")
    server_name = cursor.fetchone()
    server_name = server_name[0]

    cursor.execute(f"SELECT channel_id FROM main WHERE guild_id = {ctx.guild.id}")
    matchinfo = cursor.fetchone()
    match = matchinfo[0]

    cursor.execute(f"SELECT role FROM main WHERE guild_id = {ctx.guild.id}")
    role = cursor.fetchone()
    role = role[0]
    await ctx.send(f"**{server_name} Information:**\nTeam : `{team}`\nMatch Channel : `{match}`\nTeam Role : `{role}`")


# Get matchChannel and Team Name and save it globally
# \/
@client.command()
@commands.has_permissions(administrator = True)
async def setchannel(ctx, arg1):
    await client.wait_until_ready()

    # arg1 = int(arg1)
    global guildID
    global matchChannel
    matchChannel = discord.utils.get(ctx.guild.text_channels, name=f'{arg1}')
    guildID = ctx.guild.id
    mchannel = str(matchChannel)

    print("Now Inserting Channel ID INTO Database...")
    sql_update_channelID = (f'''UPDATE main
        SET channel_id = ?
        WHERE guild_id = ?
        ''')
    info = (mchannel, guildID)
    cursor.execute(sql_update_channelID, info)
    db.commit()
    print("Channel Added to Database.")
    
    try:
        await matchChannel.send("Match Channel Set!")
    except:
        await ctx.send("Invalid Channel Name, Check if you wrote it correctly!")
        print("Error Setchannel Code 0")

@client.command()
@commands.has_permissions(administrator = True)
async def setrole(ctx, arg1):
    await client.wait_until_ready()
    guildID = ctx.guild.id
    teamrole = discord.utils.get(ctx.guild.roles, name=f'{arg1}')
    role = str(teamrole)
    try:
        role_set = (f"""UPDATE main
            SET role = ?
            WHERE guild_id = ?
            """)
        info = (role, guildID)
        cursor.execute(role_set, info)
        db.commit()
        print("Role Added to Database!")
    except:
        print("Error Adding Role to Database!")

    await ctx.send(f"{teamrole.mention} has been set as the Role!") 

@client.command()
@commands.has_permissions(administrator = True)
async def setteam(ctx, *args):
    await client.wait_until_ready()
    team = ' '.join(args)
    guildID = ctx.guild.id
    try:
        sql_team_set = (f"""UPDATE main
            SET team = ?
            WHERE guild_id = ?
            """)
        info = (team, guildID)
        cursor.execute(sql_team_set, info)
        db.commit()
        print("Team Added to Datebase")

        await ctx.send(f"You have set your team to : **{team}**")
    except:
        await ctx.send(f"Error setting team! Please try again and check the spelling.")
        print("Error SetTeam 0")


# /\

# .scrim command sending to match channel
@client.command()
async def setscrim(ctx, arg1, arg2):

    cursor.execute(f"""SELECT channel_id FROM main WHERE guild_id = {ctx.guild.id}""")
    channelid = cursor.fetchone()
    channelid = channelid[0]


    matchChannel = discord.utils.get(ctx.guild.text_channels, name=f'{channelid}')
    await matchChannel.send(f"Scrim Scheduled for: **{arg1.capitalize()} at {arg2.capitalize()}**")
    await ctx.message.delete()

# .setmatch command
# TODO: Web Scrape to make it automatic!

@client.command()
async def setmatch(ctx, arg1, arg2):

    cursor.execute(f"""SELECT channel_id FROM main WHERE guild_id = {ctx.guild.id}""")
    channelid = cursor.fetchone()
    channelid = channelid[0]

    matchChannel = discord.utils.get(ctx.guild.text_channels, name=f'{channelid}')
    await matchChannel.send(f"League Match Scheduled for: **{arg1.capitalize()} at {arg2.capitalize()}**")
    await ctx.message.delete()

# .sremind command
# TODO: Make it get .scrim time and remind 15 minutes before!
@client.command()
async def sremind(ctx, arg1, arg2):

    cursor.execute(f"""SELECT channel_id FROM main WHERE guild_id = {ctx.guild.id}""")
    channelid = cursor.fetchone()
    channelid = channelid[0]

    matchChannel = discord.utils.get(ctx.guild.text_channels, name=f'{channelid}')

    await matchChannel.send(f"Reminder you have a scrim in >>> {arg1} {arg2}")
    await ctx.message.delete()
# Web Scrapper
# \/
def getTeams():

    page = requests.get("https://vrmasterleague.com/EchoArena/Matches/")
    soup = BeautifulSoup(page.content, 'html.parser')
    matchNode = soup.find(id='MatchesScheduled_MatchesNode')
    # matchesHidden = matchNode.find_all(class_ = 'rows-hider-body rows-hider-hidden')
    orangeCell = matchNode.find_all(class_ = 'home_team_cell')
    blueCell = matchNode.find_all(class_ = 'away_team_cell')

    global oteams
    global bteams
    # Get Teams in LIST \/ \/
    bteams = list()
    for teams in blueCell:
        bteams.append(teams.get_text())

    oteams = list()
    for teams in orangeCell:
        oteams.append(teams.get_text())

# SendScrape
# \/
@client.command()
async def sendmatch(ctx):
    
    await client.wait_until_ready()
    cursor.execute(f"""SELECT channel_id FROM main WHERE guild_id = {ctx.guild.id}""")
    channelid = cursor.fetchone()
    channelid = channelid[0]
    print(channelid)

    cursor.execute(f"""SELECT team FROM main WHERE guild_id = {ctx.guild.id}""")
    team = cursor.fetchone()
    team = team[0]
    print(team)

    cursor.execute(f"SELECT role FROM main WHERE guild_id = {ctx.guild.id}")
    role = cursor.fetchone()
    role = role[0]
    print(role)

    matchChannel = discord.utils.get(ctx.guild.text_channels, name=f'{channelid}')
    role = discord.utils.get(ctx.guild.roles, name=f'{role}')

    getTeams()
    await matchChannel.send(f"{role.mention} Upcoming Matches!")

    teamCount = 0
    counter = 0
    for teams in bteams:
        if teams.startswith(f"{team}"):
            teamCount += 1
            orangeTeam = oteams[counter]
            await matchChannel.send(f'**Blue** : {team} vs **Orange** : {orangeTeam}')
        counter += 1


    counter = 0
    for teams in oteams:
        if teams.startswith(f"{team}"):
            teamCount += 1
            blueTeam = bteams[counter]
            await matchChannel.send(f'**Blue** : {blueTeam} vs **Orange** : {team}')
        counter += 1

    if teamCount == 0:
        await matchChannel.send("You do not have any matches!")
# COMMAND TO CHECK WHENEVER /\


# SCHEDULER EVERY MONDAY

async def sendScrape():
    await client.wait_until_ready()
    cursor.execute(f"""SELECT channel_id FROM main WHERE guild_id = {guildID}""")
    channelid = cursor.fetchone()
    channelid = channelid[0]

    cursor.execute(f"""SELECT team FROM main WHERE guild_id = {guildID}""")
    team = cursor.fetchone()
    team = team[0]

    cursor.execute(f"SELECT role FROM main WHERE guild_id = {guildID}")
    role = cursor.fetchone()
    role = role[0]

    matchChannel = discord.utils.get()
    getTeams()
    await matchChannel.send(f"{role.mention} Upcoming Matches!")

    teamCount = 0
    counter = 0
    for teams in bteams:
        if teams.startswith(f"{team}"):
            teamCount += 1
            orangeTeam = oteams[counter]
            await matchChannel.send(f'**Blue** : {team} vs **Orange** : {orangeTeam}')
        counter += 1


    counter = 0
    for teams in oteams:
        if teams.startswith(f"{team}"):
            teamCount += 1
            blueTeam = bteams[counter]
            await matchChannel.send(f'**Blue** : {blueTeam} vs **Orange** : {team}')
        counter += 1

    if teamCount == 0:
        await matchChannel.send("You do not have any matches!")



scheduler = AsyncIOScheduler()
scheduler.add_job(sendScrape, 'cron', day_of_week=0, hour=16, minute=20)
scheduler.start()

@client.event
async def on_guild_join(guild):

    server_name = str(guild)
    guild_id = guild.id

    db.execute('INSERT INTO main(server_name, guild_id) values(?,?)',
    (server_name, guild_id))
    db.commit()
    print("New Guild Inserted to Database.")

@client.event
async def on_guild_remove(guild):

    server_name = str(guild)
    guild_id = guild.id

    db.execute(f'DELETE FROM main WHERE guild_id = {guild_id}')
    db.commit()
    print(f"Bot removed from {server_name}, database has been updated!")
   
# Ready Message
@client.event
async def on_ready():

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS main(
        server_name TEXT,
        guild_id INTEGER,
        team TEXT,
        role TEXT,
        channel_id TEXT    
        )
        ''')
    db.commit()

    print('------')
    print("Loading Succesful...")
    print(client.user.name)
    print('------')

client.run(token)