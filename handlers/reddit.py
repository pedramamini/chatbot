import re
import random
import requests
import simplejson

########################################################################################################################
class handler:
    """
    Interface with Reddit.
    """

    ####################################################################################################################
    def __init__ (self, bot):
        self.bot = bot

        # register triggers.
        self.bot.register_trigger(self.reddit, "command", "reddit")

        # register help.
        self.bot.register_help("reddit", self.reddit.__doc__)

        # keep track of recent reddits per subreddit and per room.
        self.recent = {}


    ####################################################################################################################
    def reddit (self, xmpp_message, room, nick, subreddit):
        """
        Grab a random item from a subreddit feed. Keeps track of recently retrieve items per room and per subreddit
        to prevent repetition.

        Usage: .reddit [subreddit]
        """

        URL = "http://www.reddit.com/r/%s/.json"

        if not subreddit:
            subreddit = self.bot.config.DEFAULT_SUBREDDIT

        # check for invalid characters.
        if re.search("[^0-9a-zA-Z]", subreddit):
            return "(reddit) alphanumeric characters only for subreddit wise guy."

        try:
            data = requests.get(URL % subreddit).content
            data = simplejson.loads(data)["data"]
        except:
            return "(reddit) no such subreddit."

        # ensure local storage exists for this room...
        self.recent[room] = self.recent.get(room, {})

        # ...and this specific subreddit.
        self.recent[room][subreddit] = self.recent[room].get(subreddit, [])

        # try up to to thirty times to pick a unique entry.
        for i in xrange (30):
            entry = random.choice(data["children"])

            # we haven't delivered this one recently.
            if entry["data"]["id"] not in self.recent[room][subreddit]:
                self.recent[room][subreddit].append(entry["data"]["id"])

                # keep track of 10 most recent URLs.
                if len(self.recent[room][subreddit]) > 10:
                    self.recent[room][subreddit].pop(0)

                break

        return "%s: %s" % (entry["data"]["title"], entry["data"]["url"])

