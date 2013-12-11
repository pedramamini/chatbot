# python modules.
import os
import re
import sys
import time
import types
import pickle
import sqlite3
import logging
import getpass
import traceback

# external dependencies.
import requests
import sleekxmpp
import simplejson

# import options from config.py.
import config

# bot helpers.
import helpers

# import our HipChat API.
import hipchat


# Python versions before 3.0 do not use UTF-8 encoding
# by default. To ensure that Unicode is handled properly
# throughout SleekXMPP, we will set the default encoding
# ourselves to UTF-8.
if sys.version_info < (3, 0):
    reload(sys)
    sys.setdefaultencoding('utf8')
else:
    raw_input = input
    
########################################################################################################################
class jumpbot (sleekxmpp.ClientXMPP):
    """
    HipChat XMPP Bot
    """

    ####################################################################################################################
    def __init__ (self, username, password):
    
        sleekxmpp.ClientXMPP.__init__(self, username, password)

        # register callbacks for XMPP events.
        self.add_event_handler("session_start",     self._xmpp_on_startup)
        self.add_event_handler("groupchat_message", self._xmpp_on_message)

        # internals.
        self.config   = config                                              # internal reference to config options.
        self.help     = {}                                                  # handler documentation data structure.
        self.path     = os.path.dirname(os.path.abspath(__file__))          # absolute path to directory containing bot.
        self.triggers = {"any":[], "command":[], "cron":[], "regex":[]}     # handler trigger mapping data structure.
        self.hipchat  = hipchat.api(config.HIPCHAT_API_KEY)                 # interface to HipChat API.

        # establish memory connectivity. sets: self.conn, self.memory.
        self._memory_connect()

        # handler loading occurs at the end of _xmpp_on_startup().


    #####################################################################################################################
    def _dbg (self, message):
        try:
            sys.stdout.write("[--] %s\n" % message)
        except Exception as e:
            pass

    def _err (self, message):
        try:
            sys.stderr.write("[!!] %s\n" % message)
        except Exception as e:
            pass


    #####################################################################################################################
    def _exception_handler (self, message, e=None, fatal=False):
        """
        Helper function to process exceptions. Outputs exception description and stack trace. If fatal is raised then
        a hard exist is performed via os._exit(1).

        @type  message: String
        @param message: Error message.
        @type  e:       Exception
        @param e:       Fatal exception.
        @type  fatal:   Boolean
        @param fatal:   Flag signalling that the exception is fatal and a hard exit should be performed.
        """

        if e:
            v, t, tb    = sys.exc_info()
            stack_trace = "".join(traceback.format_tb(tb))

            self._err("%s\n\n%s\n\n%s" % (message, e, stack_trace))
        else:
            self._err("%s" % message)

        if fatal:
            # we perform a hard exit here to kill all threads.
            os._exit(1)


    ####################################################################################################################
    def _load_handlers (self):
        """
        Dynamically load all available handlers in self.path/"handlers".
        """

        # resolve path to handlers.
        path_handlers = self.path + os.sep + "handlers"

        # for each file in the handlers path.
        for handler in os.listdir(path_handlers):

            # look for files whose names end with ".py".
            if os.path.isfile(path_handlers + os.sep + handler) and handler.lower().endswith(".py"):

                # chop off the ".py" extension.
                handler = handler[:-3]

                if handler.lower() != "__init__":
                    self._dbg("loading handler: %s" % handler)

                    try:
                        # dynamically import the handler and call its initialization routine.
                        __import__("handlers.%s" % handler, fromlist=["handlers"]).handler(self)

                    except Exception as e:
                        self._exception_handler("unable to load handler: %s" % handler, e, fatal=True)

        self._dbg("all handlers loaded.")


    ####################################################################################################################
    def _memory_connect (self):
        """
        Initialize connection to memory.
        """

        # sqlite3 REGEXP implementation.
        # reference: http://stackoverflow.com/questions/5365451/problem-with-regexp-python-and-sqlite
        def regexp (expression, item):
            return re.compile(expression).search(item) is not None

        # determine path to memory file and if officer pete is a new born (no prior memories).
        memory_path = self.path + os.sep + "officer_pete.memory"
        new_born    = True

        if os.path.exists(memory_path):
            new_born = False

        # instantiate a new connection.
        self.conn = sqlite3.connect(memory_path, check_same_thread=False)

        # bind REGEXP -> regexp().
        self.conn.create_function("REGEXP", 2, regexp)

        # this next line allows us to access rows by field name.
        self.conn.row_factory = sqlite3.Row

        # this next line switches the text objects returned from sqlite from unicode to str.
        self.conn.text_factory = str

        # instantiate a cursor.
        self.memory = self.conn.cursor()

        # initialize memory if officer pete is a new born and record his birthday.
        if new_born:
            self.memory.execute("CREATE TABLE cerebellum (tag TEXT UNIQUE, memory TEXT)")
            self.memory_remember("my birthday", time.time())


    ####################################################################################################################
    def _process_cron (self):
        """
        Called every config.CRON_INTERVAL seconds from the main thread. Executes each registered job in serial.

        @note: Cron handlers should be mindful of serial processing and thread out if they intend on operating for long.
        """

        for callback in self.triggers["cron"]:
            callback()


    ####################################################################################################################
    def _xmpp_on_message (self, xmpp_message):
        """
        Called for each message both sent and received by the bot. The logic for parsing messages and appropriately
        multiplexing out to handlers happens here.
        """

        room, nick, message = xmpp_message["mucroom"], xmpp_message["mucnick"], xmpp_message["body"]

        # process all handlers bound to "any".
        for callback in self.triggers["any"]:
            try:
                # process callback and speak results.
                self.speak(xmpp_message, callback(xmpp_message, room, nick, message))

            except Exception as e:
                self._exception_handler("exception in handler-all-%s()." % callback.__name__, e, fatal=True)

        # ensure the other handlers don't talk to themselves.
        if nick == config.NICKNAME:
            return

        # sanitize any non-printables out of message. handlers can access the raw messag via xmpp_message if they wish.
        message = helpers.sanitize(message)

        # make a lower case copy of the message as we we'll use this a few times below.
        message_lower = message.lower()

        # the first handler to get triggered is called. "command" takes precedence over "regex".
        for category in ["command", "regex"]:
            for callback, trigger in self.triggers[category]:

                trigger_lower = trigger.lower()     # lower case version of trigger.
                trigger_match = False               # whether or not a trigger was matched.
                arguments     = None                # trigger arguments, extracted below.

                # command triggers are either prefixed with a dot...
                if category == "command" and \
                    (
                        message_lower.startswith("." + trigger_lower + " ") or \
                        message_lower.endswith  ("." + trigger_lower)       or \
                        message_lower.startswith("/" + trigger_lower + " ") or \
                        message_lower.endswith  ("/" + trigger_lower)
                    ):

                    # the arguments begin after the trigger, preserve the original case.
                    arguments     = message[len(trigger) + 1:].strip()  # +1 for the dot or slash (./)
                    trigger_match = True

                # ...or triggers prefixed with an @mention.
                elif category == "command" and config.AT_NAME in message_lower:

                    # the trigger and arguments being after the @message.
                    remainder = message[message_lower.index(config.AT_NAME) + len(config.AT_NAME):].strip().lstrip("./")

                    # if the remainder starts with our trigger (no dot prefix required here).
                    if remainder.lower().startswith(trigger_lower):

                        # the arguments begin after the trigger, preserve the original case.
                        arguments     = remainder[len(trigger):].strip()
                        trigger_match = True

                # ...or triggers prefixed with a generic mention of @bot.
                elif category == "command" and "@bot" in message_lower:

                    # the trigger and arguments being after the @message.
                    remainder = message[message_lower.index("@bot") + 4:].strip().lstrip("./")

                    # if the remainder starts with our trigger (no dot prefix required here).
                    if remainder.lower().startswith(trigger_lower):

                        # the arguments begin after the trigger, preserve the original case.
                        arguments     = remainder[len(trigger):].strip()
                        trigger_match = True

                # look for regular expression match (not search, want to be more strict here).
                elif category == "regex" and re.match(trigger, message):

                    # the entire message is the argument.
                    arguments     = message
                    trigger_match = True

                # if a trigger was matched, launch the callback.
                if trigger_match:
                    try:
                        # process callback, speak the results and return
                        self.speak(xmpp_message, callback(xmpp_message, room, nick, arguments))
                        return

                    except Exception as e:
                        # fata exception.
                        self._exception_handler("handler %s-%s()." % (category, callback.__name__), e, fatal=True)


    ####################################################################################################################
    def _xmpp_on_startup (self, xmpp_event):
        """
        Called upon successful connection to HipChat server. Joins configured rooms then calls load handler routine.
        """

        # required by XMPP.
        self.send_presence()
        self.get_roster()

        # for each configured room.
        for room in config.ROOMS:
            self._dbg("joining room: %s" % room)

            # convert room name to HipChat suitable format.
            try:
                encoded = self.hipchat.room_encode(room)
            except Exception as e:
                self._err("failed hipchat-ifying room named: %s" % room)

            try:
                # enter the room via MUC plugin.
                self.plugin["xep_0045"].joinMUC(encoded, config.NICKNAME)
            except:
                self._err("failed xmpp joining %s (%s)" % (room, encoded))

        # now that we're connected to the server, we can process handlers.
        self._load_handlers()


    ####################################################################################################################
    def memory_forget (self, tag):
        """
        Forget a memory.

        @type  tag:   String
        @param tag:   Tag identifying this memory, tags are lower cased.
        """

        # normalize tag.
        tag = tag.lower()

        self.memory_query("DELETE FROM cerebellum WHERE tag=?", (tag,))


    ####################################################################################################################
    def memory_query (self, query, params=()):
        """
        Query memory.
        """

        query          = query.lstrip().rstrip()
        succeeded      = False
        attempts       = 0
        MAX_ATTEMPTS   = 5

        # try up to MAX_ATTEMPTS times to execute the SQL query.
        while not succeeded and attempts < MAX_ATTEMPTS:
            try:
                self.memory.execute(query, params)
                self.conn.commit()
                succeeded = True
            except sqlite3.Error, e:
                message  = "sqlite3: %s\n\n" % e
                message += "query:   %s\n"   % query
                message += "params:  %s\n\n" % str(params)

                self._err(message)

                attempts += 1
                time.sleep(.5)

        # if execute() failed, now is the time to whine about it.
        if not succeeded:
            raise Exception("sqlite failure count exceeded max of %d" % MAX_ATTEMPTS)

        # return database cursor.
        return self.memory


    ####################################################################################################################
    def memory_recall (self, tag, dunno=None):
        """
        Recall a memory.

        @type  tag:   String
        @param tag:   Tag identifying this memory, tags are lower cased.
        @type  dunno: Mixed
        @param dunno: What to return if no memory was found.

        @rtype:  Mixed
        @return: Memory
        """

        tag     = tag.lower()
        synapse = self.memory_query("SELECT memory FROM cerebellum WHERE tag=?", (tag,)).fetchone()

        if not synapse:
            return dunno
        else:
            return pickle.loads(synapse["memory"])


    ####################################################################################################################
    def memory_remember (self, tag, memory):
        """
        Remember something.

        @type  tag:    String
        @param tag:    Tag identifying this memory, tags are lower cased.
        @type  memory: Mixed
        @param memory: Whatever we want to remember.

        @rtype:  Boolean
        @return: True if remembered, False otherwise.
        """

        # normalize tag.
        tag = tag.lower()

        # use pickle to handle complex types.
        try:
            memory = pickle.dumps(memory)
        except:
            self._err("unable to marshal: %s" % memory)
            return False

        # if this memory already exists, forget it.
        if self.memory_recall(tag, "beats me") != "beats me":
            self.memory_forget(tag)

        # create the memory.
        self.memory_query("INSERT INTO cerebellum (tag, memory) VALUES (?, ?)", (tag, memory))

        # memory successfully formed.
        return True


    ####################################################################################################################
    def register_help (self, topic, description):
        """
        Register a command name-description pair with the bot's self help documentation.

        @type  topic:       String
        @param topic:       Topic title.
        @type  description: String
        @param description: Topic description.
        """

        # remove leading tabs.
        description = description.strip().replace("    ", "")

        # replace single new lines with a space, and replace double new lines with a single new line.
        self.help[topic] = "".join([line + " " if line else "\n" for line in description.split("\n")])


    ####################################################################################################################
    def register_trigger (self, callback, category, trigger=None):
        """
        Map a trigger to a specific handler method. Triggers can be bound to: any message (any), period (cron), messages
        which begin with a dot or are @mentioned to the bot (command), or messages that match a specified regular
        expression (regex). Command triggers are case insensitive. For case insensitive regular expression triggers,
        start the trigger pattern with "(?i).

        @type  callback: Handler Method
        @param callback: Handler method to call when trigger fires.
        @type  category: String
        @param category: One of "any", "command", "cron", or "regex".
        @type  trigger:  String
        @param trigger:  Trigger string

        @raise: Exception on API usage error.
        """

        # normalize category and sanity check.
        category = category.lower()

        # categories "any" and "cron" don't have triggers.
        if category in ["any", "cron"]:

            # append the callback and we're done.
            self._dbg("    registering %s-trigger -> handler-%s()" % (category, callback.__name__))
            self.triggers[category].append(callback)

        # categories "command" and "regex" are paired with triggers.
        elif category in ["command", "regex"]:

            # search for a possible trigger overlap.
            for x_callback, x_trigger in self.triggers[category]:

                # overlap found, error out.
                if trigger.lower() == x_trigger.lower():
                    error  = "failed registering %s-trigger '%s' -> handler-%s(), already defined in handler-%s()"
                    error %= (category, trigger, callback.__name__, x_callback.__name__)

                    raise Exception(error)

            # append the callback-trigger pair.
            self._dbg("    registering %s-trigger '%s' -> hander-%s()" % (category, trigger, callback.__name__))
            self.triggers[category].append((callback, trigger))

        # invalid category.
        else:
            raise Exception("register_trigger() called with invalid category: %s" % category)


    ####################################################################################################################
    def speak (self, xmpp_message, phrase_or_phrases):
        """
        Make bot speak a single phrase or a list of phrases.

        @type  xmpp_message:      XMPP message
        @param xmpp_message:      XMPP message
        @type  phrase_or_phrases: ["", "", ...] or ""
        @param phrase_or_phrases: Phrase or list of phrases to speak.
        """

        if not phrase_or_phrases:
            return

        # normalize to list.
        if type(phrase_or_phrases) is not list:
            phrase_or_phrases = [phrase_or_phrases]

        # extract and decode room.
        room = self.hipchat.room_decode(xmpp_message["mucroom"])

        # speak each phrase.
        for phrase in phrase_or_phrases:
            self._dbg("[%s] %s: %s..." % (room, self.config.NICKNAME, phrase.split("\n")[0][:140]))
            self.send_message(mto=xmpp_message["from"].bare, mtype="groupchat", mbody=phrase)


########################################################################################################################
if __name__ == "__main__":
    # satisfy sleekxmpp logging
    logging.basicConfig(level="CRITICAL", format="%(levelname)-8s %(message)s")

    # if the password isn't specified in the config module, read it in now.
    if not config.PASSWORD:
        config.PASSWORD = getpass.getpass("HipChat Password for %s: " % config.NICKNAME)

    # instatiate bot. the "/bot" suffix ensures no message history is delivered to the bot.
    officer_pete = jumpbot(config.USERNAME + "@chat.hipchat.com/bot", config.PASSWORD)

    # service discovery.
    officer_pete.register_plugin("xep_0030")

    # XMPP Multi-User Chat (MUC). HipChat does *not* support Groupchat 1.0 protocol.
    officer_pete.register_plugin("xep_0045")

    # XMPP ping, set frequency to 60 because HipChat said so (http://www.hipchat.com/help/category/xmpp).
    officer_pete.register_plugin("xep_0199", {"keepalive":True, "frequency":60})

    # connect to HipChat server and thread out the bot.
    if officer_pete.connect(("conf.hipchat.com", 5222)):
        officer_pete.process(threaded=True)
    else:
        officer_pete._exception_handler("connection failure.")

    # process cron jobs at the specified interval.
    #while 1:
        #officer_pete._process_cron()
        #time.sleep(config.CRON_INTERVAL)
