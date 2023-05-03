import requests
from bs4 import BeautifulSoup
import boto3


def lambda_handler(event, context):
    url = 'https://www.thegamer.com/video-game-release-dates-2023/'
    headers = {'User-Agent': 'My User Agent 1.0'}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    release = dict()
    count = 0

    # scrape content
    for th in soup.find_all('th'):
        day = th.text.split(' ')[0]
        month = th.text.split(' ')[1]
        release[count] = [day, month]
        count += 1

    count = 0
    for tr in soup.find_all('tr'):
        game = tr.find_all('td')[0].text
        platform = tr.find_all('td')[1].text
        if count < len(release):
            release[count].append(game)
            release[count].append(platform)
        count += 1

    db_client = boto3.resource('dynamodb')
    table = db_client.Table('GameRelease')

    for i in range(0, len(release), 1):
        table.put_item(
            Item={
                'ID': i+1,
                'Date': int(release[i][1]),
                'Month': release[i][0],
                'Name': release[i][2],
                'Platform': release[i][3],
                'Year': 2023
            }
        )
    return "Success", 200
