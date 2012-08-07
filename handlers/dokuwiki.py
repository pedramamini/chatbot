import xmlrpclib

########################################################################################################################
class handler:
    """
    Dokuwiki integration.
    """

    ####################################################################################################################
    def __init__ (self, bot):
        self.bot = bot

        # register triggers.
        for alias in ["note to self", "notetoself", "note_to_self", "note2self"]:
            self.bot.register_trigger(self.note_to_self, "command", alias)

        # register help.
        self.bot.register_help("notes to self", self.note_to_self.__doc__)


    ####################################################################################################################
    def note_to_self (self, xmpp_message, room, nick, note):
        """
        Leave a note for yourself on DokuWiki.

        Usage: .note_to_self <note>

        Aliases: note to self, note2self, notetoself
        """

        host = self.bot.config.DOKUWIKI_HOST
        usr  = self.bot.config.DOKUWIKI_USER
        pwd  = self.bot.config.DOKUWIKI_PASS
        ns   = self.bot.config.DOKUWIKI_NAMESPACE

        # establish an XML-RPC connection to dokuwiki.
        if host and usr and pwd:
            xmlrpc_uri = "http://%s:%s@%s/lib/exe/xmlrpc.php" % (usr, pwd, host)
            wiki       = xmlrpclib.ServerProxy(xmlrpc_uri, allow_none=1).wiki

        # failed to connect.
        else:
            return "(sadpanda) could not establish XML-RPC connection to Dokuwiki."

        # deterine the correct wiki page name.
        nick      = nick.split(" ")[0].lower()
        page_name = "%s%s" % (ns, nick)

        try:
            # get the current page and append the new note to it.
            p = wiki.getPage(page_name).rstrip("\n") + "\n\n" + note
        except:
            return "(sadpanda) failed connecting to Dokuwiki."

        try:
            # re-commit the page as a minor change.
            wiki.putPage(page_name, p, { "minor" : True })
        except:
            return "(sadpanda) failed setting Dokuwiki page."

        return "(thumbsup) note to self recorded."
