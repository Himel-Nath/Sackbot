import boto3


def lambda_handler(event, context):
    username = event['username']
    game = event['game']
    score = int(event['score'])

    try:
        db_client = boto3.resource('dynamodb')
        table = db_client.Table('GameScore')
        items = table.scan()['Items']
        items_id = []   # stores ids of items in table
        item_id = 0     # initial id

        for item in items:
            items_id.append(item['ID'])

            # if the user has already rated the game before, get the ID so that you can update the same game
            if item['UserName'] == username and item['Game'] == game:
                item_id = item['ID']

        # no score by this user for this game, so the id is the next id
        if item_id == 0:
            item_id = max(items_id) + 1

        table.put_item(
            Item={
                'ID': item_id,
                'UserName': username,
                'Game': game,
                'Score': score
            }
        )
    except Exception as err:
        return err
    return "Success", 200
