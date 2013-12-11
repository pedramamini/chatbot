import time
import datetime

# bot helpers.
import helpers

LOG_CHATS_TO_CONSOLE = True

from pprint import pprint

class handler:
    """
    Chat logging.
    """

    ####################################################################################################################
    def __init__ (self, bot):
        self.bot = bot

        # process all messages.
        self.bot.register_trigger(self.log_message, "any")

        # initialize the chatlog table if it doesn't already exist.
        sql  = "CREATE TABLE IF NOT EXISTS chatlog ("
        sql += "  id         INTEGER PRIMARY KEY,"
        sql += "  room_id    INTEGER,"
        sql += "  room_name  TEXT,"
        sql += "  user_id    TEXT,"
        sql += "  user_name  TEXT,"
        sql += "  user_nick  TEXT,"
        sql += "  message    TEXT,"
        sql += "  stamp      TEXT)"

        self.bot.memory_query(sql)


    ####################################################################################################################
    def log_message (self, xmpp_message, room, nick, message):
        """
        Maintain a message log.
        """

        pprint(room)

        #room_id   = self.bot.hipchat.room_jid2id(room)
        room_id   = room
        room_name = self.bot.hipchat.room_decode(room)
        user_id   = self.bot.hipchat.user_from_xmpp_message(xmpp_message)
        user_name = nick
        user_nick = self.bot.hipchat.user_nick2at(user_name).lstrip("@")
        stamp     = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if LOG_CHATS_TO_CONSOLE and nick != self.bot.config.NICKNAME:
            self.bot._dbg("[%s] %s: %s" % (self.bot.hipchat.room_decode(room), nick, message))


        sql    = "INSERT INTO chatlog"
        sql   += " (room_id, room_name, user_id, user_name, user_nick, message, stamp)"
        sql   += " VALUES (?,?,?,?,?,?,?)"

        try:
            self.bot.memory_query(sql, (room_id, room, user_id, user_name, user_nick, message, stamp))
        except:
            raise
            # XXX - consider adding a more in-your-face notification on this.
            self.bot._err("Failed saving the above log entry.")