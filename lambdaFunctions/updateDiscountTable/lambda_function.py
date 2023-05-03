import requests
from bs4 import BeautifulSoup
import math
import boto3


def lambda_handler(event, context):
    url = "https://psdeals.net/ca-store/discounts/1?platforms=ps5&minMetascore=70"  # first page
    headers = {'User-Agent': 'My User Agent 1.0'}
    response = requests.get(url, headers=headers)  # this request is made so that we can get the total number of pages
    soup = BeautifulSoup(response.content, 'html.parser')
    games = {}  # dict that will hold all game pairs

    total = int("".join(filter(str.isdigit, soup.find('div', {'class': 'results'}).text)))  # total number of games
    pages = math.ceil(total / 36)  # 36 games in 1 page

    # iterate through the pages
    for i in range(1, pages + 1):
        url = f"https://psdeals.net/ca-store/discounts/{i}?platforms=ps5&minMetascore=70"
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')

        game_name = soup.findAll('span', {'class': 'game-collection-item-details-title'})
        percentage = soup.findAll('div', {'class': 'game-collection-item-discounts'})
        price = soup.findAll('div', {'class': 'game-collection-item-prices'})
        url = [i['href'] for i in soup.find_all('a', {'class': 'game-collection-item-link'}, href=True)]

        # this inserts games with all keys inside a dict
        for j in range(len(game_name)):
            games[game_name[j].text.replace(u"\u2122", "").replace(u"\u00AE", "")] = [percentage[j].text.split("-")[1],
                                                                                      price[j].text.split(" ")[0].
                                                                                      replace("\n", ""), url[j]]
    # populate database
    try:
        db_client = boto3.resource('dynamodb')
        table = db_client.Table('GameDiscounts')
        items = table.scan()['Items']
        items_id = []

        for item in items:
            items_id.append(item['ID'])

        initial_id = 1
        for i in games:
            table.put_item(
                Item={
                    'ID': initial_id,
                    'Name': i,
                    'Discount': games[i][0],
                    'Price': games[i][1],
                    'Url': games[i][2]
                }
            )
            initial_id += 1
    except Exception as err:
        return err
    return "Success", 200
