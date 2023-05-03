import discord
from discord.ext import commands
import asyncio
from flask import Flask
import boto3
from bs4 import BeautifulSoup
import requests
from howlongtobeatpy import HowLongToBeat   # https://pypi.org/project/howlongtobeatpy/
from psnawp_api import PSNAWP   # https://pypi.org/project/PSNAWP/
import math
from aws_requests_auth.aws_auth import AWSRequestsAuth  # https://github.com/DavidMuller/aws-requests-auth
from dotenv import load_dotenv  # https://pypi.org/project/python-dotenv/
import os
from discord import app_commands

load_dotenv()
access_key = os.getenv("ACCESS_KEY")
secret_key = os.getenv("SECRET_KEY")
session_token = os.getenv("SESSION_TOKEN")
npsso = os.getenv("NPSSO")
bot_token = os.getenv("BOT_TOKEN")

auth = AWSRequestsAuth(aws_access_key=access_key,
                       aws_secret_access_key=secret_key,
                       aws_host='moxrfvo7t4.execute-api.us-east-1.amazonaws.com',
                       aws_region='us-east-1',
                       aws_service='execute-api')


def get_session():
    session = boto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        aws_session_token=session_token,
        region_name='us-east-1'
    )
    return session


app = Flask(__name__)
app.debug = True


# get list of all games for !playtime command
def get_games(user):
    titles_with_stats = user.title_stats()
    games = []

    for item in titles_with_stats:
        games.append([item.name, item.play_duration])
    return games


@app.route("/")
def sackbot():
    intents = discord.Intents.all()
    bot = commands.Bot(command_prefix='!', intents=intents)
    bot.remove_command('help')
    # client = discord.Client(intents=intents)

    # help list all commands
    # @bot.tree.command(name = "help", description="helpp ahh")
    # async def help(interaction):
    #     embed = discord.Embed(title="All commands currently supported by Sackbot", color=0x39FF14)
    #     embed.add_field(name="!score", value="Get the score of any game available on PS4, PS5. Please use the full name of the game", inline=False)
    #     embed.add_field(name="!new <month name>", value="List all the games releasing on the specified month", inline=False)
    #     embed.add_field(name="!hltb <game name>", value="Find the game time stats from HowLongToBeat", inline=False)
    #     embed.add_field(name="!popular", value="Displays popular games ranked by number of players", inline=False)
    #     embed.add_field(name="!playtime <PSN ID>", value="See all your PS4/PS5 game play time stats! Use arrows to flip through pages", inline=False)
    #     embed.add_field(name="!rate <game name>", value="Rate games by clicking on the emotes from 1 to 5!", inline=False)
    #     embed.add_field(name="!ratings", value="View all your ratings", inline=False)
    #     embed.add_field(name="!userscore <game name>", value="Get the average user score rated by multiple players", inline=False)
    #     embed.add_field(name="!wishlist [add/remove] <game name>", value="Add or remove a game into your own wishlist. "
    #                                                                      "Use **!wishlist all** if you want to see all "
    #                                                                      "games in your list", inline=False)
    #     embed.add_field(name="!discounts", value="Finds games that are currently discounted in your wishlist", inline=False)
    #     await interaction.response.send_message(embed=embed)

    # get score from metacritic by scraping
    @bot.tree.command(name="score", description="Get the score of any game available on PS4, PS5. Please use the full name of the game")
    async def score(interaction, *, name:str):
        site = name.lower().replace(" ", "-")
        url = 'https://www.metacritic.com/game/playstation-5/' + site
        user_agent = {'User-agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=user_agent)

        soup = BeautifulSoup(response.text, 'html.parser')
        game = soup.find("span", itemprop="ratingValue")

        if response.status_code == 404 or game is None:     # page doesn't exist or no scores for game, try ps4 game
            url = 'https://www.metacritic.com/game/playstation-4/' + site
            user_agent = {'User-agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=user_agent)

        soup = BeautifulSoup(response.text, 'html.parser')
        game = soup.find("span", itemprop="ratingValue")

        if game is None:    # no ps4 or ps5 game
            await interaction.response.send_message("Please enter the full name of a game available on PlayStation 4 or PlayStation 5")
            return

        reviews = soup.find("span", itemprop="ratingValue").text
        image = soup.find('div', class_='product_image').find('img')['src']

        embed = discord.Embed(title=name.title(), description=f'The current critic score is **{reviews}**!', color=0x39FF14)
        embed.set_thumbnail(url=image)
        await interaction.response.send_message(embed=embed)

    # get all the new games by specifying a month
    @bot.tree.command(name="new", description="List all the games releasing on the specified month")
    async def release(interaction, month:str):
        month = month.capitalize()

        try:
            session = get_session()
            db_client = session.resource("dynamodb", region_name="us-east-1")
            table = db_client.Table('GameRelease')

            items = table.scan()['Items']
            data = {}

            for item in items:
                if item['Month'] == month:
                    data[item['Name']] = [item['Date'], item['Platform']]

        except Exception as err:
            return err

        data = dict(sorted(data.items(), key=lambda game: game[1][0]))  # sort the games according to release date
        url = "https://www.thegamer.com/video-game-release-dates-2023/"
        embed = discord.Embed(title=f"Games Releasing in {month} 2023", color=0x39FF14, url=url)

        if not data:    # no games for the month
            embed.add_field(name=f"There are no games currently scheduled to release during {month}", value="")
        else:
            for games in data:
                embed.add_field(name=f"{games} - {data[games][0]}", value=data[games][1], inline=False)

        await interaction.response.send_message(embed=embed)

    # getting hltb values using api
    @bot.tree.command(name='hltb', description="Find the game time stats from HowLongToBeat")
    async def hltb(interaction, *, name:str):
        result = HowLongToBeat().search(name)

        if not result:
            await interaction.response.send_message("Please enter the full name of the game")
        else:
            game = result[0]    # most similar game from the list
            embed = discord.Embed(title=f"How long to beat {game.game_name}?", color=0x39FF14)
            embed.add_field(name="Main", value=f"{game.main_story} Hours", inline=False)
            embed.add_field(name="Main + Extra", value=f"{game.main_extra} Hours", inline=False)
            embed.add_field(name="Completionist", value=f"{game.completionist} Hours", inline=False)
            embed.set_thumbnail(url=game.game_image_url)

            await interaction.response.send_message(embed=embed)

    # get play time using psn api
    @bot.tree.command(name="playtime", description="See all your PS4/PS5 game play time stats! Use arrows to flip through pages")
    async def psn(interaction, *, user_id: str):
        psnawp = PSNAWP(npsso)     # npsso token

        try:
            user = psnawp.user(online_id=user_id)
        except Exception as err:
            await interaction.response.send_message("This user does not exist! Please enter a valid PSN online ID")
            return err

        await interaction.response.defer()
        url = user.profile()['avatars'][0]['url']
        games = get_games(user)
        count = len(games)

        pages = math.ceil(count / 21)   # 21 titles in 1 page
        embeds = []
        for i in range(pages):
            embed = discord.Embed(title=f"Playtime for {user_id}", description=f"Page {i + 1} of {pages}", color=0x39FF14)
            embed.set_thumbnail(url=url)
            embeds.append(embed)

        # add all the games in the embed pages
        for i in range(pages-1):
            for j in range(i*21, (i+1)*21, 1):
                embeds[i].add_field(name=games[j][0], value=games[j][1])

        # add the extra games in the final embed page
        for i in range(((pages-1) * 21), len(games)):
            embeds[pages-1].add_field(name=games[i][0], value=games[i][1])

        # resource for multi-page embed:
        # How to use pagination for Multiple Page Embeds in Discord PY!, https://www.youtube.com/watch?v=izXfHCTlD6M
        # alphascript

        buttons = [u"\u23EA", u"\u25C0", u"\u25B6", u"\u23E9"]      # python unicode for arrow emojis
        current = 0
        await interaction.followup.send(embed=embeds[current])
        message = await interaction.original_response()

        for button in buttons:
            await message.add_reaction(button)

        # render buttons with a time out of 30s
        while True:
            try:
                reaction, user = await bot.wait_for("reaction_add", check=lambda reaction, user: user == interaction.user and reaction.message == message and reaction.emoji in buttons, timeout=30.0)
            except asyncio.TimeoutError:
                embed = embeds[current]
                embed.set_footer(text="Timed out")
                await message.clear_reactions()

            else:
                previous_page = current

                if reaction.emoji == u"\u23EA":
                    current = 0
                elif reaction.emoji == u"\u25C0":
                    if current > 0:
                        current -= 1
                elif reaction.emoji == u"\u25B6":
                    if current < len(embeds) - 1:
                        current += 1
                elif reaction.emoji == u"\u23E9":
                    current = len(embeds) - 1

                await message.remove_reaction(reaction.emoji, interaction.user)

                if current != previous_page:
                    await message.edit(embed=embeds[current])

    # getting popular games of the week by scraping psn profiles
    @bot.tree.command(name="popular", description="Displays popular games ranked by number of players")
    async def popular(interaction):
        url = 'https://psnprofiles.com'
        user_agent = {'User-agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=user_agent)

        soup = BeautifulSoup(response.text, 'html.parser')
        table = soup.find_all("table", class_="zebra")

        games = []  # list of popular games
        image_url = table[5].find('tr').find("img").get('src')  # image of the most played game

        for item in table[5].find_all('tr'):
            game = list(filter(None, item.text.split("\n")))
            games.append(game)

        embed = discord.Embed(title="POPULAR PS GAMES THIS WEEK", url='https://psnprofiles.com', color=0x39FF14)
        embed.set_thumbnail(url=image_url)

        for game in games:
            embed.add_field(name=game[0], value=f"{game[2].replace('Players', '')} Players", inline=False)

        await interaction.response.send_message(embed=embed)

    # rate games using emojis
    @bot.tree.command(name="rate", description="Rate games by clicking on the emotes from 1 to 5!")
    async def rate(interaction, *, name: str):
        result = HowLongToBeat().search(name)

        if not result:
            await interaction.response.send_message("Please enter the full name of the game")
            return

        game = result[0]

        embed = discord.Embed(title=f"What do you rate {game.game_name}?", description="Use the emotes to rate!", color=0x39FF14)
        embed.set_thumbnail(url=game.game_image_url)

        buttons = ['1⃣', '2⃣', '3⃣', '4⃣', '5⃣']

        await interaction.response.send_message(embed=embed)
        message = await interaction.original_response()
        for button in buttons:
            await message.add_reaction(button)

        value = 0   # rating
        while True:
            try:
                reaction, user = await bot.wait_for("reaction_add", check=lambda reaction, user: user == interaction.user and reaction.message == message and reaction.emoji in buttons, timeout=30.0)
            except asyncio.TimeoutError:
                embed.set_footer(text="Timed out")
                await message.clear_reactions()

            else:
                if reaction.emoji == '1⃣':
                    value = 1
                elif reaction.emoji == '2⃣':
                    value = 2
                elif reaction.emoji == '3⃣':
                    value = 3
                elif reaction.emoji == '4⃣':
                    value = 4
                elif reaction.emoji == '5⃣':
                    value = 5

                edit_embed = discord.Embed(title=f"What do you rate {game.game_name}?", description=f'You have rated '
                                                                                                    f'{game.game_name},'
                                                                                                    f' {value}/5 \u2B50'
                                           , color=0x39FF14)
                edit_embed.set_thumbnail(url=game.game_image_url)
                await message.edit(embed=edit_embed)

                # post to my api with my ratings to call the lambda functions to add the new score and update
                # average score
                body1 = {'username': str(interaction.user), 'game': game.game_name, 'score': str(value)}
                body2 = {'game': game.game_name}
                response1 = requests.post('https://moxrfvo7t4.execute-api.us-east-1.amazonaws.com/dev/adduserscore',
                                          json=body1, auth=auth, headers={})
                response2 = requests.post('https://moxrfvo7t4.execute-api.us-east-1.amazonaws.com/dev/updateaveragescore',
                                          json=body2, auth=auth, headers={})

                print(response1, response2)
                await message.remove_reaction(reaction.emoji, interaction.user)

    # get the average user score of a game
    @bot.tree.command(name="userscore", description="Get the average user score rated by multiple players")
    async def average(interaction, *, name: str):
        result = HowLongToBeat().search(name)

        if not result:
            await interaction.response.send_message("Please enter the full name of the game")
            return

        game = result[0]

        session = get_session()
        db_client = session.resource("dynamodb", region_name="us-east-1")
        table = db_client.Table('GameScore')

        items = table.scan()['Items']
        average_score = 0
        total = 0

        # get total number of gamers and current average score
        for item in items:
            if item['Game'] == game.game_name:
                total += 1
                if item['UserName'] == 'Average':
                    average_score = item['Score']

        if average_score != 0:
            embed = discord.Embed(title=f"Average User Score for {game.game_name}", description=f"The current average "
                                                                                                f"score is "
                                                                                                f"{average_score}/5 "
                                                                                                f"\u2B50 rated by "
                                                                                                f"{total - 1} gamers"
                                  , color=0x39FF14)
            embed.set_thumbnail(url=game.game_image_url)

        # no one has rated the game
        else:
            embed = discord.Embed(title=f"{game.game_name} has not been rated yet",
                                  description="You can be the first to rate it by using the **!rate** command!",
                                  color=0x39FF14)
            embed.set_thumbnail(url=game.game_image_url)

        await interaction.response.send_message(embed=embed)

    # get a list of all your ratings
    # future plan - add pages
    @bot.tree.command(name="ratings", description="View all your ratings")
    async def get_ratings(interaction):
        session = get_session()
        db_client = session.resource("dynamodb", region_name="us-east-1")
        table = db_client.Table('GameScore')
        items = table.scan()['Items']

        embed = discord.Embed(title="Here are all your ratings!", color=0x39FF14)
        url = interaction.user.avatar
        embed.set_image(url=url)

        have_ratings = False
        for item in items:
            if item['UserName'] == str(interaction.user):
                have_ratings = True
                embed.add_field(name=item['Game'], value=f"{item['Score']} out of 5 \u2B50", inline=False)

        if not have_ratings:
            await interaction.response.send_message("Uh oh! Looks like you have no ratings.\nUse the **!rate** command followed by the game "
                           "name to add your rating!")
            return

        await interaction.response.send_message(embed=embed)

    # personalized wishlist system
    # future plans - add pages
    @bot.tree.command(name="wishlist", description="add/remove/all games to your wishlist")
    @app_commands.choices(action=[
        app_commands.Choice(name='all', value=1),
        app_commands.Choice(name='add', value=2),
        app_commands.Choice(name='remove', value=3)
    ])
    async def wishlist(interaction, action: app_commands.Choice[int], *, name: str = ""):
        session = get_session()
        db_client = session.resource("dynamodb", region_name="us-east-1")
        table = db_client.Table('Wishlist')
        items = table.scan()['Items']

        embed = discord.Embed(title=f"{str(interaction.user)}'s Wishlist", color=0x39FF14)
        embed.set_thumbnail(url=interaction.user.avatar)

        if action.name == "all":     # !wishlist all
            for item in items:
                if item['UserName'] == str(interaction.user):
                    embed.add_field(name=f"{item['Game']}", value="", inline=False)
            await interaction.response.send_message(embed=embed)

        else:
            # name = name.split(" ", 1)[1]    # 1 index is for second keyword in command
            result = HowLongToBeat().search(name)

            if not result:
                await interaction.response.send_message("Please enter the full name of the game")
                return
            else:
                game = result[0]

            have_game = False
            body = {'username': str(interaction.user), 'game': game.game_name}

            # if game already in wishlist
            for item in items:
                if item['UserName'] == str(interaction.user) and item['Game'] == game.game_name:
                    have_game = True
                    break

            # if game is in wishlist then return or else call the api
            if action.name == "add":
                await interaction.response.defer()
                if have_game:
                    await interaction.followup.send(f"{game.game_name} is already in your wishlist!")
                    return

                print(requests.post('https://moxrfvo7t4.execute-api.us-east-1.amazonaws.com/dev/addwishlistgame', auth=auth,
                                    json=body, headers={}))

                embed = discord.Embed(title=f"Added {game.game_name} to your wishlist!",
                                      description="Use **/wishlist remove** if you want to remove "
                                                  "it from your wishlist or use **/wishlist all** to "
                                                  "see all the games in your wishlist", color=0x39FF14)
                embed.set_thumbnail(url=game.game_image_url)
                await interaction.followup.send(embed=embed)

            # can remove only if game exists in list
            elif action.name == "remove":
                await interaction.response.defer()
                if have_game:
                    print(requests.post(
                        'https://moxrfvo7t4.execute-api.us-east-1.amazonaws.com/dev/removewishlistgame', json=body, auth=auth,
                        headers={}))

                    await interaction.followup.send(f"The game has been removed from your wishlist.")
                else:
                    await interaction.followup.send(f"This game is not in your wishlist. Please enter the name "
                                   f"of a game already in your wishlist. Type **/wishlist all** to see all of your "
                                   f"games.")

    # get a list with all the discounts matching games in your wishlist
    # add region support
    @bot.tree.command(name="discounts", description="Finds games that are currently discounted in your wishlist")
    async def get_discount(interaction):
        session = get_session()
        db_client = session.resource("dynamodb", region_name="us-east-1")
        table1 = db_client.Table('Wishlist')
        wishlist_items = table1.scan()['Items']

        table2 = db_client.Table('GameDiscounts')
        discount_items = table2.scan()['Items']

        embed = discord.Embed(title=f"Discounts for games in {str(interaction.user)}'s Wishlist", color=0x39FF14)
        embed.set_thumbnail(url=interaction.user.avatar)

        games_with_discounts = False
        for i in wishlist_items:
            for j in discount_items:

                # remove special characters from names to compare them
                game1 = ''.join(e for e in i['Game'] if e.isalnum())
                game2 = ''.join(e for e in j['Name'] if e.isalnum())

                if game1 in game2 and i['UserName'] == str(interaction.user):
                    games_with_discounts = True
                    url = f"https://psdeals.net{j['Url']}"
                    embed.add_field(name=j['Name'], value=f"The game is {j['Discount']} off at {j['Price']}! "
                                                          f"[Click here]({url})", inline=False)

        if not games_with_discounts:
            await interaction.response.send_message(f"{interaction.user.mention} Currently there aren't any discounts for games in your wishlist. "
                           f"Check back later for new discounts!")
            return
        await interaction.response.send_message(embed=embed)

    # @bot.tree.command
    # async def command(interaction):
    #     pass

    @bot.event
    async def on_ready():
        await bot.tree.sync()

    bot.run(bot_token)