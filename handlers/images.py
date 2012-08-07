import re
import random
import requests
import simplejson
import BeautifulSoup

########################################################################################################################
class handler:
    """
    Various image search and manipulation functionality.
    """

    ####################################################################################################################
    def __init__ (self, bot,):
        self.bot = bot

        # register triggers.
        self.bot.register_trigger(self.dribbble,      "command", "dribbble")
        self.bot.register_trigger(self.mustachify,    "command", "mustachify")

        for alias in ["img", "image"]:
            self.bot.register_trigger(self.google_images, "command", alias)

        # register help.
        self.bot.register_help("dribbble",     self.dribbble.__doc__)
        self.bot.register_help("image search", self.google_images.__doc__)
        self.bot.register_help("mustachify",   self.mustachify.__doc__)

        # keep track of recent image results per room.
        self.recent_google_images   = {}
        self.recent_dribbble_images = {}


    ####################################################################################################################
    def dribbble (self, xmpp_message, room, nick, keywords):
        """
        Search dribbble.com for images matching keywords.

        Usage: .dribbble <keywords>
        """

        # keywords required.
        if not keywords:
            return

        URL = "http://dribbble.com/search?p=%d&q=%s"

        # get a few pages of data and concatenate it together.
        results = []

        for page in xrange(1, 4):
            data = requests.get(URL % (page, requests.utils.quote(keywords))).content

            # parse it out.
            soup = BeautifulSoup.BeautifulSoup(data)

            for div in soup.findAll("div", "dribbble-img"):
                url     = "http://dribbble.com" + div.find("a")["href"]
                img_url = "http://dribbble.com" + div.find("img")["src"]

                try:
                    desc = div.find("span").getText()
                except:
                    desc = ""

                results.append((url, img_url, desc))

        # if no results were collected, return now.
        if not results:
            return "(thumbsdown) no hits under that keyword sir."

        # initialize local storage.
        self.recent_dribbble_images[room] = self.recent_dribbble_images.get(room, [])

        # try up to to 25 times to pick a unique URL.
        for i in xrange (25):
            url, img_url, desc = random.choice(results)

            # we haven't delivered this one recently.
            if url not in self.recent_dribbble_images[room]:
                self.recent_dribbble_images[room].append(url)

                # keep track of 10 most recent URLs.
                if len(self.recent_dribbble_images[room]) > 10:
                    self.recent_dribbble_images[room].pop(0)

                break

        # decided against returning the description for now.
        return [img_url, url]


    ####################################################################################################################
    def google_images (self, xmpp_message, room, nick, keywords):
        """
        Search Google images for keywords and return a random result.

        Usage: .img <keywords>

        Alias: image
        """

        URL = "https://ajax.googleapis.com/ajax/services/search/images?v=1.0&rsz=8&q="

        # keywords are required.
        if not keywords:
            return

        try:
            data = requests.get(URL + requests.utils.quote(keywords), timeout=5).content
            data = simplejson.loads(data)["responseData"]["results"]
        except:
            return "(facepalm) sorry. I encounted a JSON parsing error."

        # initialize local storage.
        self.recent_google_images[room] = self.recent_google_images.get(room, [])

        # try up to to ten times to pick a unique URL.
        for i in xrange (10):
            url = random.choice(data)["url"]

            # we haven't delivered this one recently.
            if url not in self.recent_google_images[room]:
                self.recent_google_images[room].append(url)

                # keep track of 3 most recent URLs.
                if len(self.recent_google_images[room]) > 3:
                    self.recent_google_images[room].pop(0)

                break

        return url


    ####################################################################################################################
    def mustachify (self, xmpp_message, room, nick, url):
        """
        Add a mustache to an image URL. Leave URL argument out to apply to last Google image hit in channel.

        Usage: .mustachify [http://...]
        """

        URL = "http://mustachify.me/?src="

        # initialize local storage.
        self.recent_google_images[room] = self.recent_google_images.get(room, [])

        # if no URL is specified, see if we can pull it from Google image search history for the room.
        if not url and len(self.recent_google_images[room]):
            # try/except in case of race condition.
            try:
                url = self.recent_google_images[room][-1]
            except:
                url = None

        # if still no URL, error.
        if not url:
            return "(areyoukiddingme) URL not specified and no Google image search history."

        # if there is no http:// prefix, add it.
        if not url.lower().startswith("http"):
            url = "http://" + url

        # swap https:// prefix with http://.
        if url.lower().startswith("https"):
            url = "http" + url.lstrip("https")

        try:
            requests.get(URL + url, timeout=5).raise_for_status()
            return URL + url
        except:
            return "(hipster) sorry. Couldn't mustachify that one. mustachify is spotty though, try again later."
