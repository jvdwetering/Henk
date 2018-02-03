import urllib.request
import datetime
from html import unescape

url = "http://www.ru.nl/facilitairbedrijf/horeca/de-refter/weekmenu-refter/menu-soep-deze-week/"

def get_todays_menu():
    with urllib.request.urlopen(url) as response:
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
            menu = days[day]
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
