"""
Jumpshot HipChat v2 API Interface
"""

# python modules.
import string

# import options from config.py.
import config

# external dependencies.
import requests
import simplejson

from pprint import pprint

########################################################################################################################
class api:
    """
    Interface to HipChat v2 API's.
    """

    ####################################################################################################################
    def __init__ (self, key):
        self.host    = "api.hipchat.com"
        self.version = "1"
        self.params  = {"auth_token" : key}
        self.headers = {"Host" : self.host}
        self.data    = {}


    ####################################################################################################################
    def _get (self, routine, headers={}, params={}):
        headers.update(self.headers)
        params.update(self.params)

        data = requests.get("https://%s/v%s/%s" % (self.host, self.version, routine), params=params, headers=headers)
        json = simplejson.loads(data.content)

        return json


    ####################################################################################################################
    def _post (self, routine, headers={}, params={}, data={}):
        headers.update(self.headers)
        params.update(self.params)
        data.update(self.data)

        data = requests.post("https://%s/v%s/%s" % (self.host, self.version, routine), headers=headers, params=params, data=data)
        json = simplejson.loads(data.content)

        return json


    ####################################################################################################################
    # straight forward wrappers.
    def rooms_history (self):     return self._get("rooms/history")["rooms"]
    def rooms_list    (self):     return self._get("rooms/list")["rooms"]
    def users_list    (self):     return self._get("users/list")["users"]
    def rooms_show    (self, id): return self._get("rooms/show", params={"room_id":id})["room"]
    def users_show    (self, id): return self._get("users/show", params={"user_id":id})["user"]


    ####################################################################################################################
    def room_decode (self, name):
        """
        Convert "pedrams_corner" to "Pedrams Corner". (I know, we lost a quote)

        @note: NOT a perfect match to original name!

        @type  name: String
        @param name: Room name to decode.

        @rtype:  String
        @return: Human readable room name.
        """

        try:
            return name.split("@")[0].split("_", 1)[1].replace("_", " ").title()
        except:
            # this functionality isn't critical, so we can just silently ignore the error and return the original.
            return name


    ####################################################################################################################
    def room_encode (self, name):
        """
        Convert "Pedram's Corner" to "pedrams_corner".

        @type  name: String
        @param name: Room name to encode.

        @rtype:  String
        @return: Protocol formatted room name.

        @raises: Encounted exception, if any.
        """

        try:
            encoded = name.lower().replace(" ", "_")
            encoded = "".join(c for c in encoded if c in string.ascii_lowercase + string.digits + "_")
            encoded = "%s_%s@conf.hipchat.com" % (config.PREAMBLE, encoded)

            return encoded
        except:
            raise Exception("room_encode() failure on: %s" % name)


    #####################################################################################################################
    def room_jid2id (self, jid):
        """
        Convert a rooms XMPP JID to a HipChat room ID. JID is the 'room' argument to handlers.

        @type  jid: String
        @param jid: XMPP JID

        @rtype:  Integer
        @return: HipChat room ID.
        """

        # iterate through each room,
        for room in self.rooms_list():

            # if the names match.
            if room["xmpp_jid"] == jid:

                # return the ID.
                return room["room_id"]

        # raise an exception if no match was found.
        raise Exception("room_jid2id() could not resolve '%s'" % jid)


    ####################################################################################################################
    def rooms_message (self, id, message, notify=0, color="yellow"):
        """
        Post a message to a room. Message can contain XHTML with the following supported basic tags::

            a, b, i, strong, em, br, img, pre, code

        @type  id:      Integer
        @param id:      HipChat room id.
        @type  message: String
        @param message: The message body.
        @type  notify:  Integer
        @param notify:  0 for True, 1 for False.
        @type  color:   String
        @param color:   Background color, one of: "yellow", "red", "green", "purple", or "random".

        @rtype:  Boolean
        @return: True on success, False otherwise.
        """

        data = \
        {
            "room_id" : id,
            "from"    : config.NICKNAME,
            "message" : message,
            "notify"  : notify,
            "color"   : color,
        }

        try:
            # if the POST fails or the status isn't successful. we failed.
            response = self._post("rooms/message", data=data)

            assert response["status"] == "sent"
            return True
        except:
            return False


    ####################################################################################################################
    def user_from_xmpp_message (self, xmpp_message):
        """
        Extract HipChat user ID from xmpp_message and return.

        @note: This routine MUST be wrapped with an exception handler.

        @type  xmpp_message: XMPP Message
        @param xmpp_message: XMPP Message

        @rtype:  String
        @return: HipChat username (format: \d+_\d+).

        @raise: Raises exception if match is not found, which does happen on system messages.
        """

        try:
            return repr(xmpp_message).split("<sender>")[1].split("@")[0]
        except:
            return "API"


    ####################################################################################################################
    def user_nick2at (self, nick):
        """
        Convert a nickname to an @mention-able name.
        """

        return "@" + nick.split()[0].lower()
