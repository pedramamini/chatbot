"""
Jumpshot HipChat Bot Configuration Parameters
"""

import os

# get these values from: http://www.hipchat.com/account/xmpp/
USERNAME            = os.environ.get("BOT_USERNAME", "")    # HipChat username (format: \d+_\d+)
PASSWORD            = os.environ.get("BOT_PASSWORD", "")    # HipChat password, leave blank to fill in from prompt.
NICKNAME            = os.environ.get("BOT_NICKNAME", "")    # HipChat room nickname, this must match the info at the above URL.

# list of room names to join.
ROOMS               = os.environ.get("BOT_ROOMS", "").split(",")

HIPCHAT_API_KEY     = os.environ.get("BOT_HIPCHAT_API_KEY",   "")
CRON_INTERVAL       = int(os.environ.get("BOT_CRON_INTERVAL", 10))   # interval bot cron jobs are processed.


# handler-specific configuration.
VT_API_KEY          = os.environ.get("BOT_VT_API_KEY",          "")
DEFAULT_WEATHER_ZIP = os.environ.get("BOT_DEFAULT_WEATHER_ZIP", "78701")           # default zip code for weather handler.
DEFAULT_SUBREDDIT   = os.environ.get("BOT_DEFAULT_SUBREDDIT",   "funny")           # default subreddit to pull from in reddit handler.
DOKUWIKI_USER       = os.environ.get("BOT_DOKUWIKI_USER",       "")                # dokuwiki XML-RPC username.
DOKUWIKI_PASS       = os.environ.get("BOT_DOKUWIKI_PASS",       "")                # dokuwiki XML-RPC password.
DOKUWIKI_HOST       = os.environ.get("BOT_DOKUWIKI_HOST",       "")                # dokuwiki XML-RPC hostname or IP address.
DOKUWIKI_NAMESPACE  = os.environ.get("BOT_DOKUWIKI_NAMESPACE",  "")                # optional dokuwiki namespace to prefix.

# shouldn't need to configured anything beyond this line.
PREAMBLE            = USERNAME.split("_")[0]             # slice the preamble off the username.
USER_ID             = int(USERNAME.split("_")[1])        # slice the user ID off the username.
AT_NAME             = "@" + NICKNAME.split()[0].lower()  # slice off the @mention name for ourself, @bot in this case.
