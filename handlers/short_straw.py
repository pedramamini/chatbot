import random
import requests
import simplejson

########################################################################################################################
class handler:
    """
    Determine who in the current room drew the short straw.
    """

    ####################################################################################################################
    def __init__ (self, bot):
        self.bot = bot

        # register triggers.
        self.bot.register_trigger(self.short_straw, "regex", "(?i).*(short.straw).*")


    ####################################################################################################################
    def short_straw (self, xmpp_message, room, nick, message):
        """
        Draw straws between everyone in the room, not including the bot.
        """

        if not self.bot.config.HIPCHAT_API_KEY:
            return "(disapproval) HipChat Admin API key not defined."

        # look for a wordmatch on "short straw" in all messages.
        if "short straw" not in message.lower():
            return

        # find the active room.
        try:
            room_id = self.bot.hipchat.room_jid2id(room)
        except:
            self.bot._err("api.room_jid2id('%s') failed." % room)
            return

        # make a list of users in the room.
        candidates = []

        for participant in self.bot.hipchat.rooms_show(room_id)["participants"]:
            if participant["user_id"] != self.bot.config.USER_ID:
                candidates.append(self.bot.hipchat.user_nick2at(participant["name"]))

        # randomly choose a candidate.
        the_chosen  = "raise your hand if you drew the short straw (freddie) %s (from %d candidates)"
        the_chosen %= random.choice(candidates), len(candidates)

        return the_chosen
