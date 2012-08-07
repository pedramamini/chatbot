import random

# bot helpers.
import helpers

########################################################################################################################
class handler:
    """
    Self help.
    """

    ####################################################################################################################
    def __init__ (self, bot):
        self.bot = bot

        # register triggers.
        self.bot.register_trigger(self.help, "command",  "help")


    ####################################################################################################################
    def help (self, xmpp_message, room, nick, topic):
        """
        List topics or provide help for a specific one. Compensates for some fat fingering.
        """

        # if no specific topic was specified, list all of them.
        if not topic:
            topics = self.bot.help.keys()
            topics.sort()

            ret = ["I can offer help on the following topics: " + ", ".join(topics)]
            ret.append("For help on a specific topic, try: .help topic")

            return ret

        # otherwise, provide the description for the specified topic.
        topic_lower = topic.lower()

        for k, v in self.bot.help.iteritems():
            if topic_lower == k.lower():
                return v

        # no match was found, try to compensate for any fat fingering before giving up.
        acceptable_distance = min(.85 * len(topic), 3)

        for k, v in self.bot.help.iteritems():
            if helpers.levenshtein_distance(topic_lower, k) <= acceptable_distance:
                return ["(goodnews) i think you probably meant '%s'..." % k, v]

        # pick a random emotion of disappointment.
        emotion = random.choice(["disapproval", "areyoukiddingme", "facepalm", "sadpanda"])

        return "(%s) don't know anything about that topic." % emotion
