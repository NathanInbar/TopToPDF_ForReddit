#Written with Python 3.7.0

#Required modules listed by 'pip' name (Default modules omitted):
#Requests, Praw, Pillow, Reportlab. redditAuthentication contains my personal reddit Authentication id/secret/agent/username/password.

#Reddit Authentication is required to run this script.
#Create an authorized Reddit script to get your personal Authentication info here: https://www.reddit.com/prefs/apps/
#then fill in the Authentication variables in redditAuthentication.py with your information
from TopPostsToPDF import executeOrder66

executeOrder66()
