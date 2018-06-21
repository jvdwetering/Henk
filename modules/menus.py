import urllib.request
import datetime
from html import unescape

from .base import Module

refterurl = "http://www.ru.nl/facilitairbedrijf/horeca/de-refter/weekmenu-refter/menu-soep-deze-week/"
gerechturl = "http://www.ru.nl/facilitairbedrijf/horeca/het-gerecht-grotiusgebouw/menu-{0}/"

maanden = ["januari", "februari", "maart", "april", "mei", "juni",
           "juli", "augustus", "oktober", "november", "december"]
dagen = ["Maandag", "Dinsdag", "Woensdag", "Donderdag", "Vrijdag"]

def get_refter_menu():
    with urllib.request.urlopen(refterurl) as response:
        html = response.read().decode('utf-8')
        try:
            data = html[html.find('<p><strong>'):]
            days = []
            for i in range(5):
               r = data.find("</ul>")
               days.append(data[:r])
               data = data[r+len("</ul>"):]
            day = datetime.datetime.today().weekday() #0 if Monday, 6 if Sunday
            if day>4: #it is weekend
                day=0 #show Monday
            menu = days[day].strip()
            options = []
            for line in menu.splitlines():
                s = line.strip()
                if not s.startswith("<li>"): continue
                pre = len('<li><span class="li-content">')
                post = len("</span>")
                options.append(unescape(s[pre:-post]))
            date = menu[len("<p><strong>"):menu.find("</strong>")]

            return date+"\n"+"\n".join(options)
        except KeyError:
            return "Meh, er ging iets fout :("


def get_gerecht_menu():
    t = datetime.datetime.today()
    m = t - datetime.timedelta(days = t.weekday()) # gets the monday of this week
    f = t + datetime.timedelta(days = 4-t.weekday()) #friday
    if m.month == f.month:
        s = "%d-%d-%s" % (m.day, f.day, maanden[t.month-1])
    else:
        s = "%d-%s-%d-%s" % (m.day, maanden[m.month-1], f.day, maanden[f.month-1])

    url = gerechturl.format(s)
    with urllib.request.urlopen(url) as response:
        html = response.read().decode('utf-8')
        try:
            data = html[html.find('<div class="iprox-rich-content iprox-content">'):]
            lines = []
            for l in data[:data.find('</div>')].splitlines()[1:-1]:
                f = l.replace('<p>','').replace('<strong>','').replace('</p>','').replace('</strong>','')
                f = unescape(f.replace('<sup>','').replace('</sup>',' ').replace('<em>',' ').replace('</em>',' ').replace('\xa0',' ').strip())
                lines.append(f)
            #return lines
            text = "\n".join(lines)
            days = []
            if t.weekday()>4: #it is weekend
                return text
            s = "%s %d %s" % (dagen[t.weekday()], t.day, maanden[t.month-1])
            if t.weekday==4: #it is friday
                return text[text.find(s):]
            morgen = m = t + datetime.timedelta(days = 1)
            s2= "%s %d %s" % (dagen[morgen.weekday()], morgen.day, maanden[morgen.month-1])
            return text[text.find(s):text.find(s2)]
        except KeyError:
            return "Meh, er ging iets fout :("

def get_todays_menu():
    refter = get_refter_menu()
    gerecht = get_gerecht_menu()

    output = ""
    if not refter:
        output += "Geen idee wat de Refter heeft\n\n"
    else:
        output += "Refter:\n" + refter + "\n\n"
    if not gerecht:
        output += "Geen idee wat het Gerecht heeft\n\n"
    else:
        output += "Gerecht:\n" + gerecht

    return output


class Menu(Module):
    def register_commands(self,bot):
        bot.add_slash_command("refter", self.get_menu)

        bot.add_command_category("refter", self.get_menu)

    def get_menu(self, bot, msg):
        return get_todays_menu()

menu = Menu()