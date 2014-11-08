import re
import time
import datetime

# bot helpers.
import helpers

EMOTICON = "(officerpete) "

########################################################################################################################
class handler:
    """
    Timers, reminders and stopwatch.
    """

    ####################################################################################################################
    def __init__ (self, bot):
        self.bot = bot

        # register triggers.
        self.bot.register_trigger(self.timer_make,      "command", "timer")
        self.bot.register_trigger(self.timer_list,      "command", "timers")
        self.bot.register_trigger(self.timer_clear,     "command", "clear_timer")
        self.bot.register_trigger(self.timer_cron,      "cron")

        self.bot.register_trigger(self.reminder_make,   "command", "reminder")
        self.bot.register_trigger(self.reminder_list,   "command", "reminders")
        self.bot.register_trigger(self.reminder_clear,  "command", "clear_reminder")
        self.bot.register_trigger(self.reminder_reset,  "command", "reset_reminder")
        self.bot.register_trigger(self.reminder_snooze, "command", "snooze_reminder")
        self.bot.register_trigger(self.reminder_cron,   "cron")

        for alias in ["stopwatch", "sw"]:
            self.bot.register_trigger(self.stopwatch,   "command", alias)

        # register some pseudo natural language processing triggers.
        BOT = self.bot.config.AT_NAME

        self.bot.register_trigger(self._natural_reminder,    "regex", "(?i).*" + BOT + ".*remind me.*(every|in).*")
        self.bot.register_trigger(self._natural_reminders,   "regex", "(?i).*" + BOT + ".*reminders.*me.*")
        self.bot.register_trigger(self._natural_reminders,   "regex", "(?i).*" + BOT + ".*my.*reminders.*")
        self.bot.register_trigger(self._natural_timer,       "regex", "(?i).*" + BOT + ".*set.*timer.*")
        self.bot.register_trigger(self._natural_timer_clear, "regex", "(?i).*" + BOT + ".*clear.*timer.*")

        # define timer help.
        help_timers = """
            Think of timers as an egg timer or hour glass you set in a room. You may want to set a timer to expire in
            sync with a parking meter, or to revisit a certain task in a couple of minutes. Timers can be set, listed
            or cleared. Unlike reminders, they are not persistent.

            * create a timer: .timer <minutes> [optional message]

            * list timers: .timers

            * clear last created timer: .clear_timer
        """

        # define reminder help.
        help_reminders = """
            Think of reminders as a snoozable, persistent and periodic nudge that you can bind to a room. You may want
            to set a reminder to water the plants every four days, or to call your parents every week. Reminders can be
            created, lists, cleared (deleted), snoozed (pushed back a day or more) or reset (reset the count down).

            * create a reminder: .reminder <days> <reminder message>

            * list reminders: .reminders

            * reset a reminder: .reset_reminder <reminder message>

            * snooze last reminder: .snooze_reminder [days=1]

            * clear a reminder: .clear_reminder <reminder message>
        """

        # register help.
        self.bot.register_help("timers",    help_timers)
        self.bot.register_help("reminders", help_reminders)
        self.bot.register_help("stopwatch", self.stopwatch.__doc__)

        # these two data structures are mirrored in the bots memory.
        self.timers      = self.bot.memory_recall("timers",      {})
        self.reminders   = self.bot.memory_recall("reminders",   {})
        self.stopwatches = self.bot.memory_recall("stopwatches", {})

        # keep track of what reminder last went off for each user (for snoozing purposes).
        self.last_reminders = {}


    ####################################################################################################################
    def _natural_reminder (self, xmpp_message, room, nick, message):
        hit = re.search(self.bot.config.AT_NAME + ".*remind me\s+(.*)\s(every|in)[^\d]*(\d+).*", message, re.I)

        if hit:
            hits = hit.groups()

            return self.reminder_make(xmpp_message, room, nick, "%s %s" % (hits[2], hits[0]))


    ####################################################################################################################
    def _natural_reminders (self, xmpp_message, room, nick, message):
        return self.reminder_list(xmpp_message, room, nick, "")


    ####################################################################################################################
    def _natural_timer (self, xmpp_message, room, nick, message):
        hit = re.search(self.bot.config.AT_NAME + ".*set.*timer[^\d]*(\d+)", message, re.I)

        if hit:
            return self.timer_make(xmpp_message, room, nick, hit.groups()[0])


    ####################################################################################################################
    def _natural_timer_clear (self, xmpp_message, room, nick, message):
        return self.timer_clear(xmpp_message, room, nick, "")


    ####################################################################################################################
    def elapsed_time (self, start, finish=None):
        """
        Determine time elapsed in days, hours, minutes, seconds and milliseconds.

        @type  start:  time.time()
        @param start:  Starting time.
        @type  finish: time.time()
        @param finish: Finish time.

        @rtype:  Tuple
        @return: (days, hours, minutes, seconds, msecs)
        """

        if not finish:
            finish = time.time()

        uptime  = int(float(finish) - float(start))
        msecs   = finish - start - uptime
        days    = uptime  / 86400
        uptime -= days    * 86400
        hours   = uptime  / 3600
        uptime -= hours   * 3600
        minutes = uptime  / 60
        uptime -= minutes * 60
        seconds = uptime

        return days, hours, minutes, seconds, msecs


    ####################################################################################################################
    def reminder_make (self, xmpp_message, room, nick, args):
        """
        Set a reminder to expire after a set number of days at which point the bot will notify you and reset the clock.
        Usage: .reminder <days> <reminder message>
        """

        # argument parsing and sanitization.
        args = args.strip()

        # first space-delimited chunk of args is the number of days, second is optional description.
        try:
            days, message = args.split(" ", 1)
        except:
            return "%ssorry, but you're going to have to give me some details on what to remind you of." % EMOTICON

        # days must be a number.
        try:
            days = int(days)
        except:
            return "%shmmm, try again. i need to know how often would you'd like me to remind you." % EMOTICON

        # record the reminder.
        room_id    = self.bot.hipchat.room_jid2id(room)
        now        = datetime.datetime.now()
        expiration = (now + datetime.timedelta(days=days)).strftime("%Y-%m-%d 00:00:00")
        expiration = time.mktime(time.strptime(expiration, "%Y-%m-%d 00:00:00"))

        # set the reminder.
        self.reminders[nick] = self.reminders.get(nick, [])
        self.reminders[nick].append((room_id, expiration, days, message))

        # commit the data structure to memory.
        self.bot.memory_remember("reminders", self.reminders)

        return "%sok, i'll remind you '%s' every %d days." % (EMOTICON, message, days)


    ####################################################################################################################
    def reminder_list (self, xmpp_message, room, nick, args):
        """
        List the active reminders and how far they are from expiration.
        Usage: .reminders
        """

        report = []

        # iterate through each users reminders for this specific room.
        for nick, reminders in self.reminders.iteritems():

            # for each timer.
            for reminder in reminders:

                # break apart the tupple.
                room_id, expiration, days, message = reminder

                # calculate time to expiration.
                left   = expiration - time.time()
                entry  = "every %d days i remind you '%s'. which is coming up in %d days."
                entry %= (days, message, int(left / 86400) + 1)

                report.append(entry)

        if report:
            report.insert(0, "%shere's the items i'm waiting to remind you about..." % EMOTICON)
            return report
        else:
            return "%syou haven't asked me to remind you about anything in this room." % EMOTICON


    ####################################################################################################################
    def reminder_clear (self, xmpp_message, room, nick, existing_reminder):
        """
        Clear the reminder with the specified reminder message.
        Usage: .clear_reminder <existing reminder message>
        """

        # argument parsing and sanitization.
        existing_reminder = existing_reminder.strip(" \"'")

        if not existing_reminder:
            return "%shmmm, you must tell me which reminder you're referring to." % EMOTICON

        # find the reminder.
        found = False

        for reminder in self.reminders.get(nick, []):
            # break apart the reminder tuple.
            room_id, expiration, days, message = reminder

            if message.lower() == existing_reminder.lower():
                found = True
                break

        if not found:
            return "%ssorry, but i don't recall you ever asking me to remind you about that in this room." % EMOTICON

        # remove the reminder.
        self.reminders[nick].remove(reminder)

        # commit the data structure to memory.
        self.bot.memory_remember("reminders", self.reminders)

        return "%sok, i won't remind you about that anymore." % EMOTICON


    ####################################################################################################################
    def reminder_cron (self):
        """
        Check for expired reminders during at 6am every morning.
        """

        # timestamp.
        now = datetime.datetime.now()

        # run every day at 6am only.
        if now.hour != 6:
            return

        # only run once per day.
        if hasattr(self, "last_reminder_cron_day") and self.last_reminder_cron_day == now.day:
            return

        # record the last run day.
        self.last_reminder_cron_day = now.day

        # filter through each users reminders via reminder_filter().
        for nick, reminders in self.reminders.iteritems():

            # set this member variable for reminder_filter() to reference.
            self.current_nick = nick

            # filter through and process reminders.
            self.reminders[nick] = filter(self.reminder_filter, reminders)

        # commit the data structure to memory.
        self.bot.memory_remember("reminders", self.reminders)


    ####################################################################################################################
    def reminder_filter (self, reminder):
        """
        List filter function for reminders.
        """

        # pull out the various parts.
        room_id, expiration, days, message = reminder

        # check if time has expired.
        if int(time.time()) > expiration:
            self.last_reminders[self.current_nick].append(reminder)

            message = "%s, you wanted me to remind you %s. i'll remind you again in %d days." % \
                (self.bot.hipchat.user_nick2at(self.current_nick), message, days)

            # notify the room.
            self.bot.hipchat.rooms_message(room_id, message, color="purple", notify=1)

            # reminder is no longer active.
            return False

        # reminder is still active.
        return True


    ####################################################################################################################
    def reminder_reset (self, xmpp_message, room, nick, existing_reminder):
        """
        Reset the period for the reminder. If you don't specify the optional existing reminder message then the last
        reminder to trigger will be reset.
        Usage: .reset_reminder [existing reminder message]
        """

        # argument parsing and sanitization.
        existing_reminder = existing_reminder.strip()

        # if an existing reminder message was not supplied.
        found = False
        if not existing_reminder:

            # if there is something on the last reminders stack, use that...
            if self.last_reminders.has_key(nick) and self.last_reminders[nick]:
                reminder = self.last_reminders[nick].pop()
                found    = True

                # break apart the reminder tuple.
                room_id, expiration, days, message = reminder

            # ...otherwise, complain.
            else:
                return "%shmmm, please tell me which reminder you're referring to." % EMOTICON

        # search for the reminder by exact message match.
        if not found:

            # walk through reminders.
            for reminder in self.reminders.get(nick, []):

                # break apart the reminder tuple.
                room_id, expiration, days, message = reminder

                if message.lower() == existing_reminder.lower():
                    found = True
                    break

        # search for the reminder by close message match.
        if not found:

            # walk through reminders.
            for reminder in self.reminders.get(nick, []):

                # break apart the reminder tuple.
                room_id, expiration, days, message = reminder

                # try to find a minimal 85% match.
                acceptable_distance = min(.85 * len(existing_reminder), 3)

                if helpers.levenshtein_distance(message.lower(), existing_reminder.lower()) <= acceptable_distance:
                    found = True
                    break

        if not found:
            return "%ssorry, but i don't recall you ever asking me to remind you about that in this room." % EMOTICON

        # remove the reminder and add it back in with a fresh expiration.
        new_expiration = (datetime.datetime.now() + datetime.timedelta(days=days)).strftime("%Y-%m-%d 00:00:00")
        new_expiration = time.mktime(time.strptime(new_expiration, "%Y-%m-%d 00:00:00"))

        self.reminders[nick].remove(reminder)
        self.reminders[nick].append((room_id, new_expiration, days, message))

        # commit the data structure to memory.
        self.bot.memory_remember("reminders", self.reminders)

        if days == 1:
            return "%sok, we'll worry about that again tomorrow." % EMOTICON
        else:
            return "%sok, we'll worry about that again in %d days." % (EMOTICON, days)


    ####################################################################################################################
    def reminder_snooze (self, xmpp_message, room, nick, days_to_snooze):
        """
        Snooze the last triggered reminders for the specified number of days. If left blank, snooze is for 1 day.
        Usage: .snooze_reminder [days=1]
        """

        # argument parsing and sanitization.
        days_to_snooze = days_to_snooze.strip()

        if not days_to_snooze:
            days_to_snooze = 1
        else:
            try:
                days_to_snooze = int(days_to_snooze)
            except:
                return "%ssorry, how many days did you say you want me to snooze this reminder for?" % EMOTICON

        # grab the last reminder from the stack.
        reminder = None

        if self.last_reminders.has_key(nick) and self.last_reminders[nick]:
            reminder = self.last_reminders[nick].pop()

        if not reminder:
            return "%shuh? i didn't say anything." % EMOTICON

        # break apart the reminder tuple.
        room_id, expiration, days, message = reminder

        # remove the reminder and add it back in with a fresh expiration.
        new_expiration = (datetime.datetime.now() + datetime.timedelta(days=days_to_snooze))
        new_expiration = new_expiration.strftime("%Y-%m-%d 00:00:00")
        new_expiration = time.mktime(time.strptime(new_expiration, "%Y-%m-%d 00:00:00"))

        self.reminders[nick].remove(reminder)
        self.reminders[nick].append((room_id, new_expiration, days, message))

        # commit the data structure to memory.
        self.bot.memory_remember("reminders", self.reminders)

        if days_to_snooze == 1:
            return "%sok, we'll worry about that again tomorrow." % EMOTICON
        else:
            return "%sok, we'll worry about that again in %d days." % (EMOTICON, days_to_snooze)


    ####################################################################################################################
    def stopwatch (self, xmpp_message, room, nick, message):
        """
        Each user gets one stop watch. You can start it, check it and stop-reset it (ie: when you stop it, it resets).
        Your stopwatch can be started in one room and stopped in another.

        * start stopwatch: .stopwatch start

        * check elapsed time: .stopwatch

        * stop and reset stopwatch: .stopwatch stop

        Alias: sw
        """

        def format_stopwatch (elapsed_time_tuple):
            # break down the elapsed time.
            days, hours, minutes, seconds, milliseconds = elapsed_time_tuple

            report = ""

            if days:
                report += "%d days " % days

            if days or hours:
                report += "%d hours " % hours

            if days or hours or minutes:
                report += "%d minutes and " % minutes

            report += "%02.02f seconds" % (seconds + milliseconds)

            return report

        # this function is bound to a regex trigger so get the entire message line. let's chop off the leading '.stop'.
        message = message.lower()

        # start the clock.
        if "start" in message or "run" in message or "go" in message:
            self.stopwatches[nick] = time.time()

            # commit the data structure to memory.
            self.bot.memory_remember("stopwatches", self.stopwatches)

            return "%sstopwatch started!" % EMOTICON

        # stop/reset the clock. (see why we chopped off the .stop from earlier?)
        elif "stop" in message or "reset" in message:
            if not self.stopwatches.has_key(nick):
                return "%syou don't have a running stopwatch." % EMOTICON

            # pop the start time off the internal data structure.
            start = self.stopwatches.pop(nick)

            # commit the data structure to memory.
            self.bot.memory_remember("stopwatches", self.stopwatches)

            return "%sstopped! time: %s" % (EMOTICON, format_stopwatch(self.elapsed_time(start)))

        # check time elapsed (also matches "naked" command: .stopwatch),
        elif not message or "time" in message or "elapsed" in message:
            if not self.stopwatches.has_key(nick):
                return "%syou don't have a running stopwatch." % EMOTICON

            return "%selapsed time: %s" % (EMOTICON, format_stopwatch(self.elapsed_time(self.stopwatches[nick])))

        # invalid.
        else:
            return "%sthat's not a stopwatch button i recognize." % EMOTICON


    ####################################################################################################################
    def timer_make (self, xmpp_message, room, nick, args):
        """
        Set a timer to expire after a set number of minutes at which point the bot will notify you.
        Usage: .timer <minutes> [optional reminder message]
        """

        # argument parsing and sanitization.
        args   = args.strip()
        atname = self.bot.hipchat.user_nick2at(nick)

        # first space-delimited chunk of args is the number of minutes, second is optional description.
        if " " in args:
            minutes, message = args.split(" ", 1)
        else:
            minutes, message = args, ""

        # minutes must be a number.
        try:
            minutes = int(minutes)
        except:
            return "%stry again please. minutes should be an integer." % EMOTICON

        # record the timer.
        room_id    = self.bot.hipchat.room_jid2id(room)
        expiration = int(time.time() + minutes * 60)

        self.timers[nick] = self.timers.get(nick, [])
        self.timers[nick].append((room_id, expiration, message))

        # commit the data structure to memory.
        self.bot.memory_remember("timers", self.timers)

        return "%stimer set to go off in %d minutes." % (EMOTICON, minutes)


    ####################################################################################################################
    def timer_list (self, xmpp_message, room, nick, args):
        """
        List the active timers and how far they are from expiration.
        Usage: .timers
        """

        timesheet    = ""
        this_room_id = self.bot.hipchat.room_jid2id(room)

        # iterate through each users timers for this specific room.
        for nick, timers in self.timers.iteritems():

            # for each timer.
            for timer in timers:

                # break apart the tupple.
                room_id, expiration, message = timer

                # ignore timers outside this room.
                if room_id != this_room_id:
                    continue

                # calculate time to expiration.
                left = expiration - time.time()
                mins = int(left / 60)
                secs = left - (mins * 60)

                # times up.
                if not mins and not secs:
                    timesheet += "times up"

                # less than a minute.
                elif not mins:
                    timesheet += "in %d secs an alarm goes off" % secs

                # over a minute.
                else:
                    timesheet += "in %d mins %d secs an alarm goes off" % (mins, secs)

                # splice in message...
                if message:
                    timesheet += " for %s regarding %s.\n" % (nick, message)

                # ...or, not.
                else:
                    timesheet += " for %s.\n" % nick

        if timesheet:
            return "-- TPS REPORT --\n" + timesheet
        else:
            return "%sthere aren't any active timers in this room." % EMOTICON


    ####################################################################################################################
    def timer_clear (self, xmpp_message, room, nick, args):
        """
        Clear the last set timer for the user.
        Usage: .clear_timer
        """

        # get @mention name.
        atname = self.bot.hipchat.user_nick2at(nick)

        # user has no active timers.
        if not self.timers.has_key(nick) or not self.timers[nick]:
            return "%s%s has no active timers." % (EMOTICON, atname)

        # pop off the last timer appended for this user.
        room_id, expiration, message = self.timers[nick].pop()

        # commit the data structure to memory.
        self.bot.memory_remember("timers", self.timers)

        # determine how many minutes and seconds were left until this timer was set to expire.
        left = expiration - time.time()
        mins = int(left / 60)
        secs = left - (mins * 60)

        ret = "%s%s cleared timer expiring in %d mins %d secs" % (EMOTICON, atname, mins, secs)

        if message:
            return ret +  " with notice '%s'" % message
        else:
            return ret + "."


    ####################################################################################################################
    def timer_filter (self, timer):
        """
        List filter function for timers.
        """

        # pull out the various parts.
        room_id, expiration, message = timer

        # check if time has expired.
        if int(time.time()) > expiration:

            # get @mention name.
            atname = self.bot.hipchat.user_nick2at(self.current_nick)

            if message:
                message = "timer set by %s has expired: %s" % (atname, message)
            else:
                message = "timer set by %s has expired." % atname

            # notify the room.
            self.bot.hipchat.rooms_message(room_id, message, color="purple", notify=1)

            # timer is no longer active.
            return False

        # timer is still active.
        return True


    ####################################################################################################################
    def timer_cron (self):
        """
        Check for expired timers during every cron loop.
        """

        # filter through each users timers via timer_filter().
        for nick, timers in self.timers.iteritems():
            # set a member variable for time_filter() to reference.
            self.current_nick = nick

            # filter through timers.
            self.timers[nick] = filter(self.timer_filter, timers)

        # commit the data structure to memory.
        self.bot.memory_remember("timers", self.timers)
