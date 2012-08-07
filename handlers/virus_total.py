import re
import requests
import simplejson

########################################################################################################################
class handler:
    """
    Interface with Virus Total API.
    """

    ####################################################################################################################
    def __init__ (self, bot):
        self.bot = bot

        # register triggers.
        for alias in ["virus_total", "vt"]:
            self.bot.register_trigger(self.virus_total, "command", alias)

        regex = "(?i).*" + "[\s'\"\[\(]*" + "([0-9a-f]{32}|[0-9a-f]{40})" + "[\s'\"\]\)]*" + ".*"
        self.bot.register_trigger(self._natural_hash_seen, "regex", regex)

        # register help.
        self.bot.register_help("virus total", self.virus_total.__doc__)


    ####################################################################################################################
    def _natural_hash_seen (self, xmpp_message, room, nick, message):
        # try the longer hash, sha1, first.
        hit = re.search("([0-9a-f]{40})", message, re.I)

        if not hit:
            # next try md5.
            hit = re.search("([0-9a-f]{32})", message, re.I)

        if hit:
            # pass the args to the virus total routine.
            response = self.virus_total(xmpp_message, room, nick, "%s" % hit.groups()[0])

            # ensure it's a known hash.
            if "never seen" not in response:

                # extract confidence.
                confidence = response.rsplit(" ", 1)[1]

                if confidence != "0%":
                    return "hey guys. i'm %s sure that hash you're talking about is a virus." % confidence


    ####################################################################################################################
    def virus_total (self, xmpp_message, room, nick, hash):
        """
        Given a hash, return the percent confidence it is malware.

        Usage: .virus_total <hash>

        Alias: vt
        """

        URL = "https://www.virustotal.com/api/get_file_report.json"

        if not self.bot.config.VT_API_KEY:
            return "(disapproval) missing config.VT_API_KEY"

        # check for invalid characters.
        if re.search("[^0-9a-fA-F]", hash):
            return "(huh) Invalid characters in hash."

        try:
            data = requests.post(URL, data={"resource":hash, "key":self.bot.config.VT_API_KEY}).content
            data = simplejson.loads(data)
        except:
            return "(facepalm) sorry. I encounted a JSON parsing error."

        # check for API errors.
        if   data["result"] ==  0: return "(dumb) never seen that hash before."
        elif data["result"] == -1: return "(ohcrap) API key isn't working."
        elif data["result"] == -2: return "(ohcrap) API key is over limit."

        # grab and parse report.
        report   = data["report"][1]
        detected = 0

        if not report:
            return "(dumb) hmmm. never seen that hash before."

        # count how many vendors detected this hash as malware.
        for av, name in report.iteritems():
            if name:
                detected += 1

        confidence = int(float(detected) / float(len(report.keys())) * 100)

        return "How confident I am this is malware: %d%%" % confidence
