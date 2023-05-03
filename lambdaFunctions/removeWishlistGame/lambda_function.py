import boto3


def lambda_handler(event, context):
    username = event['username']
    game = event['game']

    try:
        db_client = boto3.resource('dynamodb')
        table = db_client.Table('Wishlist')
        items = table.scan()['Items']

        item_id = 0
        for item in items:
            if item['UserName'] == username and item['Game'] == game:
                item_id = item['ID']

        table.delete_item(
            Key={
                'ID': item_id,
            }
        )

    except Exception as err:
        return err
    return "Success", 200
