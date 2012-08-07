"""
Jumpshot HipChat Bot Configuration Parameters
"""

# get these values from: http://www.hipchat.com/account/xmpp/
USERNAME            = ""                # HipChat username (format: \d+_\d+)
PASSWORD            = ""                # HipChat password, leave blank to fill in from prompt.
NICKNAME            = "Officer Pete"    # HipChat room nickname, this must match the info at the above URL.

# list of room names to join.
ROOMS               = ["Jumpshot", "Water Cooler", "Development", "Brainstorming"]


HIPCHAT_API_KEY     = ""                # a HipChat admin API key for some bot/plug-in functionality.
CRON_INTERVAL       = 10                # interval bot cron jobs are processed.


# handler-specific configuration.
VT_API_KEY          = ""                # API key for Virus Total handler.
DEFAULT_WEATHER_ZIP = "78701"           # default zip code for weather handler.
DEFAULT_SUBREDDIT   = "funny"           # default subreddit to pull from in reddit handler.
DOKUWIKI_USER       = ""                # dokuwiki XML-RPC username.
DOKUWIKI_PASS       = ""                # dokuwiki XML-RPC password.
DOKUWIKI_HOST       = ""                # dokuwiki XML-RPC hostname or IP address.
DOKUWIKI_NAMESPACE  = ""                # optional dokuwiki namespace to prefix.

# shouldn't need to configured anything beyond this line.
PREAMBLE            = USERNAME.split("_")[0]             # slice the preamble off the username.
USER_ID             = int(USERNAME.split("_")[1])        # slice the user ID off the username.
AT_NAME             = "@" + NICKNAME.split()[0].lower()  # slice off the @mention name for ourself, @bot in this case.
