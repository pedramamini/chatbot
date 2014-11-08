import re
import requests
import simplejson

# bot helpers.
import helpers

# twisted.
from twisted.conch.manhole     import ColoredManhole
from twisted.conch.insults     import insults
from twisted.conch.telnet      import TelnetTransport, TelnetBootstrapProtocol
from twisted.conch.manhole_ssh import ConchFactory, TerminalRealm
from twisted.internet          import protocol
from twisted.application       import internet, service
from twisted.cred              import checkers, portal

########################################################################################################################
class handler:
    """
    Remote manhole support.
    """

    ####################################################################################################################
    def __init__ (self, bot):
        self.bot = bot

        # register triggers.
        self.bot.register_trigger(self.make_manhole, "command", "manhole")


    ####################################################################################################################
    def make_manhole (self, xmpp_message, room, nick, message):
        """
        Open up a manhole and announce our currentl ip.
        """

        # control args.
        args = \
        {
            'protocolFactory' : ColoredManhole,
            'protocolArgs'    : (None,),
            'telnet'          : 6023,
            'ssh'             : 6022,
        }

        # protocol factory.
        def chainProtocolFactory():
            return insults.ServerProtocol(
                args['protocolFactory'],
                *args.get('protocolArgs', ()),
                **args.get('protocolKwArgs', {}))

        # server factory.
        f          = protocol.ServerFactory()
        f.protocol = lambda: TelnetTransport(TelnetBootstrapProtocol,
                                             insults.ServerProtocol,
                                             args['protocolFactory'],
                                             *args.get('protocolArgs', ()),
                                             **args.get('protocolKwArgs', {}))

        # checker, realms.
        checker                    = checkers.InMemoryUsernamePasswordDatabaseDontUse(pedram="iampedram")
        tsvc                       = internet.TCPServer(args['telnet'], f)
        rlm                        = TerminalRealm()
        rlm.chainedProtocolFactory = chainProtocolFactory
        ptl                        = portal.Portal(rlm, [checker])
        f                          = ConchFactory(ptl)
        csvc                       = internet.TCPServer(args['ssh'], f)
        m                          = service.MultiService()
        application                = service.Application("Interactive Python Interpreter")

        # scaffold.
        tsvc.setServiceParent(m)
        csvc.setServiceParent(m)
        m.setServiceParent(application)

        # determine IP address and announce.
        ipaddr = requests.get("http://ifconfig.me/all.json").json()['ip_addr']
        return "(successful) manhole opened @ %s" % ipaddr

