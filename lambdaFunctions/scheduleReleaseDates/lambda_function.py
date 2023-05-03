import boto3
from datetime import datetime
import requests
import json


def lambda_handler(event, context):
    # url to my channel
    webhook_url = "https://discord.com/api/webhooks/1095728958936469504/eL--Tvce-YnjJgnwhip8GusuMRFVeuRxva_UxYiBmjkutloEbe2JG0onG2_xIMi63Viq"

    # get the current date
    today = datetime.now()
    month = today.strftime("%B")
    date_number = int(today.strftime("%-d"))

    try:
        db_client = boto3.resource('dynamodb')
        table = db_client.Table('GameRelease')
        items = table.scan()['Items']

        for item in items:
            # if the date and month match, game is releasing today
            if item['Month'] == month and date_number == item['Date']:
                message = {"content": f"@everyone {item['Name']}releases today on {item['Platform']}!"}
                headers = {'Content-Type': 'application/json'}
                response = requests.post(webhook_url, json.dumps(message), headers=headers)
                print(response)

    except Exception as err:
        return err
