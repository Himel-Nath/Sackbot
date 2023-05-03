import boto3
import json


def lambda_handler(event, context):
    lambda_client = boto3.client("lambda", region_name='us-east-1')

    # call both these lambda functions once a month since they only update tables
    try:
        response1 = lambda_client.invoke(FunctionName='updateGameReleaseDates', InvocationType='RequestResponse',
                                         Payload=json.dumps(event))
        response2 = lambda_client.invoke(FunctionName='updateDiscountTable', InvocationType='RequestResponse',
                                         Payload=json.dumps(event))
        print(response1, response2)
        return "Success", 200
    except Exception as err:
        return err
