import requests
import simplejson

########################################################################################################################
class handler:
    """
    Google maps.
    """

    ####################################################################################################################
    def __init__ (self, bot):
        self.bot = bot

        # register triggers.
        for alias in ["map", "gmap"]:
            self.bot.register_trigger(self.google_map, "command",  alias)

        for alias in ["triangulate_ssid", "ssid2loc", "locate_ssid"]:
            self.bot.register_trigger(self.triangulate_ssid, "command",  alias)

        # register help.
        self.bot.register_help("maps",               self.google_map.__doc__)
        self.bot.register_help("ssid triangulation", self.triangulate_ssid.__doc__)


    ####################################################################################################################
    def google_map (self, xmpp_message, room, nick, marker):
        """
        Google map the supplied address, providing a thumbnail map and full browser link.

        Usage: .map <address>

        Alias: gmap
        """

        URL_BASE = "https://maps.google.com/maps"
        URL_IMG  = URL_BASE + "/api/staticmap?size=200x200&maptype=roadmap&sensor=false&format=png&zoom=14&markers="
        URL_LINK = URL_BASE + "?hl=en&sll=30.267153,-97.743061&sspn=0.8006,1.454315&&t=m&z=10&z=15&q="
        marker   = requests.utils.quote(marker)

        return [URL_IMG + marker, "browser-link:" + URL_LINK + marker]


    ####################################################################################################################
    def triangulate_ssid (self, xmpp_message, room, nick, mac_address):
        """
        Attempt to triangulate a WiFi AP SSID to a physical location.

        Usage: .triangulate_ssid <MAC>

        Aliases: ssid2loc, locate_ssid
        """

        url  = "https://www.google.com/loc/json"
        hdrs = { "Content-Type" : "text/xml;" }
        data = simplejson.dumps \
               ({
                   "version"         : "1.1.0",
                   "request_address" : True,
                   "wifi_towers"     : [{
                                           "mac_address"     : mac_address,
                                           "ssid"            : "",
                                           "signal_strength" : -50,
                                        }]
               })

        try:
            data = requests.post("https://www.google.com/loc/json", headers=hdrs, data=data).content
            data = simplejson.loads(data)
            data = data["location"]

            return "located at: http://maps.google.com/maps?q=%s,%s" % (data["latitude"], data["longitude"])
        except:
            return "(facepalm) sorry. I encounted an error."
