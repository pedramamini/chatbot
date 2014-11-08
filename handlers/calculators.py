import re
import requests
import simplejson

# bot helpers.
import helpers

########################################################################################################################
class handler:
    """
    Various calculator functionality.
    """

    ####################################################################################################################
    def __init__ (self, bot):
        self.bot = bot

        # register triggers.
        for alias in ["calculator", "=", "calc"]:
            self.bot.register_trigger(self.calculator, "command", alias)

        for alias in ["gcalc"]:
            self.bot.register_trigger(self.google_calculator, "command", alias)

        # register help.
        self.bot.register_help("calculator",        self.calculator.__doc__)
        self.bot.register_help("google calculator", self.google_calculator.__doc__)

        # keep track of last answer per command, and per room and per person.
        self.calc_answers  = {}
        self.gcalc_answers = {}


    ####################################################################################################################
    def calculator (self, xmpp_message, room, nick, expression):
        """
        Help humans calculate. Use 'result', 'res', 'answer', 'ans' or '_' to reference the result of the calculation.
        Results are tracked individually per person, room and calculator type.

        Usage: .calc <expression>

        Aliases: =, calculator
        """

        # an expression is required.
        if not expression:
            return

        # ensure local storage exists for this user...
        if not self.calc_answers.has_key(nick):
            self.calc_answers[nick] = {}

        # ...and in this specific room.
        if not self.calc_answers[nick].has_key(room):
            self.calc_answers[nick][room] = 0

        # normalize ans -> answer -> res -> result -> _
        expression = expression.replace("answer", "_").replace("ans", "_").replace("result", "_").replace("res", "_")

        # check for invalid characters.
        if re.search("[^0-9a-fA-F\+\-\*\/\(\)\.\sx_]", expression):
            err = "%s Valid characters include (and spaces): 0xdeadbeef numbers + - * / . ()"
            return err % helpers.random_emoticon_fail()

        # ensure we're not asked to do something too difficult.
        if expression.count("**") > 2 or len(expression) > 25:
            return "%s I'm going to let you work that one out yourself ;-)" % helpers.random_emoticon_fail()

        # splice in the last value.
        if "_" in expression:
            expression = expression.replace("_", str(self.calc_answers[nick][room]))

        try:
            self.calc_answers[nick][room] = answer = float(eval(expression))

            return "%f (0x%x)" % (answer, answer)
        except:
            return "(facepalm) sorry. I encounted an error."


    ####################################################################################################################
    # def google_calculator (self, xmpp_message, room, nick, expression):
    #     """
    #     Help humans calculate. Use 'result', 'res', 'answer', 'ans' or '_' to reference the result of the calculation.
    #     Results are tracked individually per person, room and calculator type.

    #     Usage: .gcalc <expression>

    #     Alias: gc
    #     """

    #     URL = "https://www.google.com/ig/calculator?hl=en&q="

    #     # an expression is required.
    #     if not expression:
    #         return

    #     # ensure local storage exists for this user.
    #     if not self.gcalc_answers.has_key(nick):
    #         self.gcalc_answers[nick] = {}

    #     # ...and in this specific room.
    #     if not self.gcalc_answers[nick].has_key(room):
    #         self.gcalc_answers[nick][room] = 0

    #     # normalize ans -> answer -> _
    #     expression = expression.replace("answer", "_").replace("ans", "_")

    #     # splice in the last value.
    #     if "_" in expression:
    #         expression = expression.replace("_", str(self.gcalc_answers[nick][room]))

    #     try:
    #         data = requests.get(URL + requests.utils.quote(expression)).content
    #         data = helpers.sanitize(data)
    #     except:
    #         return "(facepalm) sorry. I encounted a JSON parsing error."

    #     try:
    #         # normalize the JavaScript JSON into properly quoted JSON.
    #         # ex: {lhs: "200 pounds",rhs: "90.718474 kilograms",error: "",icc: false}
    #         for token in ["lhs", "rhs", "error", "icc"]:
    #             data = data.replace(token + ":", '"%s":' % token)

    #         data = simplejson.loads(data)
    #         ans  = data["rhs"]

    #         if ans:
    #             self.gcalc_answers[nick][room] = ans
    #             return "%s" % ans
    #         else:
    #             return "(thumbsdown) could not compute."
    #     except:
    #         return "(facepalm) oops. I encountered an error."
