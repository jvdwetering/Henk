from .admin import admin
from .menus import menu
from .weather import weather
from .wiki import wiki
from .learning import learning
from .poll import poll
from .entertainment import entertainment
from .calc import calc
from .markup import markup
from .games import games

modules = [admin, weather, wiki, calc, learning,
           entertainment,markup, games]
# I've removed menu from modules list, as this probably is no longer up to date.
# I've removed poll from the list as this feature is superceded by the Telegram feature.