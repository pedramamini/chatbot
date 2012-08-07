import random
import requests
import simplejson

# bot helpers.
import helpers

########################################################################################################################
class handler:
    """
    Urban dictionary lookup.
    """

    ####################################################################################################################
    def __init__ (self, bot):
        self.bot = bot

        # register triggers.
        for alias in ["urban_dictionary", "urban dictionary", "ud"]:
            self.bot.register_trigger(self.urban_dictionary, "command", alias)

        # register help.
        self.bot.register_help("urban dictionary", self.urban_dictionary.__doc__)


    ####################################################################################################################
    def urban_dictionary (self, xmpp_message, room, nick, term):
        """
        Lookup a term on Urban Dictionary.

        Usage: .ud <term>

        Alias: urban_dictionary
        """

        # term is required.
        if not term:
            return

        URL  = "http://www.urbandictionary.com/iphone/search/define?term=%s"
        HDRS = { "Host" : "www.urbandictionary.com" }

        try:
            data = requests.get(URL % requests.utils.quote(term), headers=HDRS).content
            data = simplejson.loads(helpers.sanitize(data))
        except:
            return "(facepalm) sorry. I encounted an error."

        # pick a random definision.
        ud = random.choice(data["list"])

        return [ud["permalink"], "%s\nExample: %s" % (ud["definition"], ud["example"])]
