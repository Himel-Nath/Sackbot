import json
from psnawp_api import PSNAWP


def lambda_handler(event, context):
    psnawp = PSNAWP(event['npsso'])
    user = psnawp.user(online_id=event['online_id'])

    titles_with_stats = user.title_stats()
    games = []

    for item in titles_with_stats:
        games.append([item.name, item.play_duration])

    return {"payload": json.dumps(games),
            "statusCode": 200}
