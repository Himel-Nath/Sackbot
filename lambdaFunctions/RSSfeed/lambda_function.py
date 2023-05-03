import json
import requests
import feedparser
import boto3


def lambda_handler(event, context):
    # url to my channel
    webhook_url = "https://discord.com/api/webhooks/1095728958936469504/eL--Tvce-YnjJgnwhip8GusuMRFVeuRxva_UxYiBmjkutloEbe2JG0onG2_xIMi63Viq"

    # get the link to the last post stored in s3
    s3 = boto3.resource('s3')
    s3_client = boto3.client('s3')
    try:
        last_post = s3_client.get_object(Bucket="rsspost", Key="latest_blog_post")['Body'].read().decode()
    except s3_client.exceptions.NoSuchKey:
        last_post = None

    rss_url = 'https://blog.playstation.com/feed/'
    feed = feedparser.parse(rss_url)
    post = feed.entries[0]  # get the latest post in the last 5 mins

    # if there is no last post or if this is a new link, we can post this link
    if post.link != last_post or last_post is None:
        s3.Object("rsspost", "latest_blog_post").put(Body=post.link)

        message = {"content": f"@everyone New post on the PlayStation Blog: {post.title}\n{post.link}"}
        headers = {'Content-Type': 'application/json'}
        response = requests.post(webhook_url, json.dumps(message), headers=headers)
        print(response)
        return "Success", 200

    return "No new posts", 200
