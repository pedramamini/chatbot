import random
import requests
import simplejson

# bot helpers.
import helpers


########################################################################################################################
class handler:
    """
    Starting the scaffolding for building out a memory backed (sql) personality engine.
    """

    ####################################################################################################################
    def __init__ (self, bot):
        self.bot = bot

        # register triggers.
        self.bot.register_trigger(self.ls_detected, "regex", "(?i).*(ls -l).*")


    ####################################################################################################################
    def ls_detected (self, xmpp_message, room, nick, message):
        """
        Super basic retort.
        """

        return "/code $ wrong window %s! but here you go:\n%s" % (nick, helpers.launch_command("ls -l ")[0])
