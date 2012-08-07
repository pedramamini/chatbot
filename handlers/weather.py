import re
import requests
import simplejson

########################################################################################################################
class handler:
    """
    Weather forecasting.
    """

    ####################################################################################################################
    def __init__ (self, bot):
        self.bot = bot

        # register triggers.
        for alias in ["weather", "forecast"]:
            self.bot.register_trigger(self.weather, "command", alias)

        self.bot.register_trigger(self._natural_weather, "regex", "(?i).*weather.*")
        self.bot.register_trigger(self._natural_weather, "regex", "(?i).*forecast.*")

        # register help.
        self.bot.register_help("weather", self.weather.__doc__)


    ####################################################################################################################
    def _natural_weather (self, xmpp_message, room, nick, message):
        hit = re.search("weather[^\d]*(\d\d\d\d\d)", message, re.I)

        if hit:
            return self.weather(xmpp_message, room, nick, "%s" % hit.groups()[0])

        message = message.lower()

        if "weather forecast" in message or "forecast looking" in message or "weather looking" in message:
            return self.weather(xmpp_message, room, nick, self.bot.config.DEFAULT_WEATHER_ZIP)


    ####################################################################################################################
    def weather (self, xmpp_message, room, nick, zipcode):
        """
        Give the weather report for the specified zip code.

        Usage: .weather [zip code]

        Alias: forecast
        """

        URL = "http://query.yahooapis.com/v1/public/yql/jonathan/weather?format=json&zip="

        if not zipcode:
            zipcode = self.bot.config.DEFAULT_WEATHER_ZIP

        try:
            data = requests.get(URL + zipcode).content
            data = simplejson.loads(data)
            data = data["query"]["results"]["channel"]
        except:
            return "(facepalm) sorry. I encounted a JSON parsing error."

        # not sure which of these fields are guaranteed to be present, so we'll be careful about gleaning them all.
        try:
            humidity = data["atmosphere"]["humidity"]
        except:
            humidity = None

        try:
            sunrise = data["astronomy"]["sunrise"]
            sunset  = data["astronomy"]["sunset"]
        except:
            sunrise = sunset = None

        try:
            temperature = "Temp: %s %s" % (data["item"]["condition"]["temp"], data["item"]["condition"]["text"])
        except:
            temperature = None

        try:
            forecasts = []

            for fc in data["item"]["forecast"]:
                forecasts.append("%s %s H:%s L:%s" % (fc["day"], fc["text"], fc["high"], fc["low"]))

            forecast = ", ".join(forecasts)
        except:
            forecast = None

        report = ""

        if temperature:
            report += temperature

            if humidity:
                report += " %s%% humidity" % humidity

            report += "\n"

        if sunrise and sunset:
            report += "Sunrise: %s, Sunset: %s\n" % (sunrise, sunset)

        if forecast:
            report += forecast + "\n"

        if report:
            return "The forecast for %s is...\n%s" % (zipcode, report)
        else:
            return "The forecast for %s is... (stare)(stare)(stare) DOOM! (stare)(stare)(stare)" % zipcode
