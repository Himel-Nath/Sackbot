import boto3


def lambda_handler(event, context):
    average_user = ''
    average_id = 0
    items_id = []
    game = event['game']

    # total stats
    total_score = 0
    total_players = 0

    try:
        db_client = boto3.resource('dynamodb')
        table = db_client.Table('GameScore')
        items = table.scan()['Items']

        # find the total number of users who played the game and add their total score
        for item in items:
            items_id.append(item['ID'])
            # getting average user (stores average value for !userscore command)
            if item['UserName'] == "Average" and item['Game'] == game:
                average_id = item['ID']
                average_user = "Average"

            if item['Game'] == game and item['UserName'] != 'Average':
                total_players += 1
                total_score += item['Score']

        average_score = total_score / total_players
        item_id = max(items_id) + 1

        # average user does not exist, so we create a new entry
        if average_user == "":
            table.put_item(
                Item={
                    'ID': item_id,
                    'UserName': "Average",
                    'Game': game,
                    'Score': average_score
                }
            )
        else:
            # average user exists, so we just have to update the score
            table.put_item(
                Item={
                    'ID': average_id,
                    'UserName': average_user,
                    'Game': game,
                    'Score': average_score
                }
            )
    except Exception as err:
        return err
    return "Success", 200
