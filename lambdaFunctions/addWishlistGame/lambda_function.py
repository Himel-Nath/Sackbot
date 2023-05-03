import boto3


def lambda_handler(event, context):
    username = event['username']
    game = event['game']

    try:
        db_client = boto3.resource('dynamodb')
        table = db_client.Table('Wishlist')
        items = table.scan()['Items']

        items_id = []
        for item in items:
            items_id.append(item['ID'])

        if not items_id:
            new_id = 1  # no items in wishlist
        else:
            new_id = max(items_id) + 1  # get next id to add to

        table.put_item(
            Item={
                'ID': new_id,
                'UserName': username,
                'Game': game,
            }
        )
    except Exception as err:
        return err
    return "Success", 200
