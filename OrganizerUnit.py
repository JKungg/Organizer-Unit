import discord, asyncio, os, random, time, json, requests
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from discord.ext import commands, tasks
from bs4 import BeautifulSoup

# token = os.environ.get('AuthToken')
token = 'NjY4OTgwNzY1MDk4Mzc3MjE2.XiuoqA.JvRokkcui9VsQOU1Eq2VfxtMZck'

client = commands.Bot(command_prefix = '.')
client.remove_command('help')

@client.command()
async def help(ctx):
    await ctx.send("```Here are the working commands : ```")



# Get matchChannel and Team Name and save it globally
# \/
@client.command()
@commands.has_permissions(administrator = True)
async def setchannel(ctx, arg1):
    global matchChannel
    await client.wait_until_ready()
    arg1 = int(arg1)
    if isinstance(arg1, int):
        matchChannel = client.get_channel(arg1)
        try:
            await matchChannel.send("Match Channel Set!")
        except:
            await ctx.send("Invalid Channel ID, Check if you wrote it correctly!")
    else:
        await ctx.send("Invalid Channel ID; Right click the channel and click **'Copy ID'**!")

@client.command()
@commands.has_permissions(administrator = True)
async def setteam(ctx, *args):
    global team
    await client.wait_until_ready()

    team = ' '.join(args)
    print(team)
    await ctx.send(f"You have set your team to : **{team}**")



# /\

# .scrim command sending to match channel
@client.command()
async def setscrim(ctx, arg1, arg2):
    await matchChannel.send(f"Scrim Scheduled for: **{arg1.capitalize()} at {arg2.capitalize()}**")
    await ctx.message.delete()

# .setmatch command
# TODO: Web Scrape to make it automatic!

@client.command()
async def setmatch(ctx, arg1, arg2):
    await matchChannel.send(f"League Match Scheduled for: **{arg1.capitalize()} at {arg2.capitalize()}**")
    await ctx.message.delete()

# .sremind command
# TODO: Make it get .scrim time and remind 15 minutes before!
@client.command()
async def sremind(ctx, arg1, arg2):
    await matchChannel.send(f"```Reminder you have a scrim in >>> {arg1} {arg2}```")
    await ctx.message.delete()

# Web Scrapper
# \/
def getTeams():

    page = requests.get("https://vrmasterleague.com/EchoArena/Matches/")
    soup = BeautifulSoup(page.content, 'html.parser')
    matchNode = soup.find(id='MatchesScheduled_MatchesNode')
    matchesHidden = matchNode.find_all(class_ = 'rows-hider-body rows-hider-hidden')
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

    getTeams()
 
    counter = 0
    for teams in bteams:
        if teams == team:
            orangeTeam = oteams[counter]
            await matchChannel.send(f'@everyone {team} vs {orangeTeam}')
        counter += 1


    counter = 0
    for teams in oteams:
        if teams == team:
            blueTeam = bteams[counter]
            await matchChannel.send(f'@everyone {team} vs {blueTeam}')
        counter += 1

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
scheduler.add_job(sendScrape, 'cron', day_of_week=0, hour=17, minute=15)
scheduler.start()

# Ready Message
@client.event
async def on_ready():
    print('------')
    print("Loading Succesful...")
    print(client.user.name)
    print('------')

client.run(token)