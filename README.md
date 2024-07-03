# SackBot 

## Mechanisms

### EC2
* Host the app on an EC2 instance
* Contains code that needs to be always accessible 

### Lambda Functions
* Code that isn't run all the time
* Code that runs in the background
* Integrations with other mechanisms

### DynamoDB
* Consists the main tables for Game releases, Wish list, Rating system and Game discounts

### S3
* Single file to hold link to latest blog posts

### API Gateway
* One REST API with several endpoints to call lambda functions

### EventBridge Schedular
* Remind when a game releases using webhooks
* Update the latest blog post 

### Backup
* Backup all tables regularly to preserve user data

## Functionality

Run commands using / (slash commands) after the bot is added to your server

#### Current list of commands:
1. New games in a month
2. HowLongToBeat stats
3. Metacritic game scores
4. Playtime using PSN
5. Rate games
6. Wishlist games
7. Find games with discounts
8. Popular games this week

### Future Plans
* Need to improve speed of queries
* More commands
* Frontend Dashboard

### Demo

<a href="https://www.youtube.com/watch?v=Elgp9GkWQOE" target="_blank" >Click Here</a>


