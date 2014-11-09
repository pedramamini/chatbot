import random
import requests
import simplejson

LS_OUT = """
$ wrong window %s! but here's what I see in my directory:
Procfile            config.py           go.sh               handlers            helpers.pyc
hipchat.pyc         local.config.py     pg-tickle.py        runtime.txt         venv
README.md           config.pyc          goped.sh            helpers.py          hipchat.py
jumpbot.py          officer_pete.memory requirements.txt    sample.config.py
""".strip()


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

        return LS_OUT % nick
