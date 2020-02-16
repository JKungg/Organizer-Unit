import discord, asyncio, os, random, time, json, requests, sqlite3
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from discord.ext import commands, tasks
from bs4 import BeautifulSoup

token = os.environ.get('DiscordToken')

client = commands.Bot(command_prefix = '.')
client.remove_command('help')

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

    cursor.execute(f"SELECT channel_id FROM main WHERE guild_id = {ctx.guild.id}")
    matchinfo = cursor.fetchone()
    match = matchinfo[0]
    await ctx.send(f"Team >> ***{team}***\nMatch Channel >> ***{match}***")
# DATABASE CONNECTION FOR USE IN MULTIPLE SERVERS!



db = sqlite3.connect('discordVariables.sqlite')
cursor = db.cursor()



# Get matchChannel and Team Name and save it globally
# \/
@client.command()
@commands.has_permissions(administrator = True)
async def setchannel(ctx, arg1):
    await client.wait_until_ready()

    # arg1 = int(arg1)
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
        print("Error SetChannel Code 0")




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
async def sremind(ctx, arg1, arg2, arg3):

    cursor.execute(f"""SELECT channel_id FROM main WHERE guild_id = {ctx.guild.id}""")
    channelid = cursor.fetchone()
    channelid = channelid[0]

    matchChannel = discord.utils.get(ctx.guild.text_channels, name=f'{channelid}')
    await matchChannel.send(f"Reminder you have a scrim in >>> {arg2} {arg3}")
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

    cursor.execute(f"""SELECT team FROM main WHERE guild_id = {ctx.guild.id}""")
    team = cursor.fetchone()
    team = team[0]

    matchChannel = discord.utils.get(ctx.guild.text_channels, name=f'{channelid}')

    getTeams()
 
    teamCount = 0
    counter = 0
    for teams in bteams:
        if teams == team:
            teamCount += 1
            orangeTeam = oteams[counter]
            await matchChannel.send(f'@everyone {team} vs {orangeTeam}')
        counter += 1


    counter = 0
    for teams in oteams:
        if teams == team:
            teamCount += 1
            blueTeam = bteams[counter]
            await matchChannel.send(f'@everyone {team} vs {blueTeam}')
        counter += 1

    if teamCount == 0:
        await matchChannel.send("You do not have any matches!")
# COMMAND TO CHECK WHENEVER /\


# SCHEDULER EVERY MONDAY

async def sendScrape():
# 
    await client.wait_until_ready()
    matchchannel = client.get_channel(676243741811671050)

    getTeams()
# 
    counter = 0
    for team  in bteams:
        if team == "Team Jokr":
            orangeTeam = oteams[counter]
            await matchchannel.send(f'@everyone Team Jokr vs {orangeTeam}')
        counter += 1


    counter = 0
    for team in oteams:
        if team == "Team Jokr":
            blueTeam = bteams[counter]
            await matchchannel.send(f'@everyone Team Jokr vs {blueTeam}')
        counter += 1



scheduler = AsyncIOScheduler()
scheduler.add_job(sendScrape, 'cron', day_of_week=0, hour=17, minute=25)
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
        channel_id TEXT    
        )
        ''')
    db.commit()

    print('------')
    print("Loading Succesful...")
    print(client.user.name)
    print('------')

client.run(token)