import random

PRINT = True
stoplevel = 0
def pp(s, stoplvl=0):
    if not PRINT: return
    if stoplvl >= stoplevel:
        print(s)

def cmp(a,b):
    if a>b: return 1
    if a<b: return -1
    else: return 0

CLUBS = 0
SPADES = 1
DIAMONDS = 2
HEARTS = 3
CLUB = CLUBS
SPAD = SPADES
DIAM = DIAMONDS
HEART = HEARTS

FAKE = 10

SEVEN = 0
EIGHT = 1
NINE = 2
JACK = 3
QUEEN = 4
KING = 5
TEN = 6
ACE = 7

valuenames = {SEVEN: "SEVEN", EIGHT: "EIGHT", NINE: "NINE", TEN: "TEN",
              JACK: "JACK", QUEEN: "QUEEN", KING: "KING", ACE: "ACE"}
colornames = {CLUBS: "CLUBS", SPADES: "SPADES", DIAMONDS: "DIAMONDS", HEARTS: "HEARTS"}
suit_to_unicode = {
    CLUBS: u"\u2663",
    SPADES: u"\u2660",
    DIAMONDS: u"\u2666",
    #HEARTS: u"\u2665" #This one looks black on iOS
    HEARTS: u"\u2764"
}
short_valuenames = {SEVEN: "7", EIGHT: "8", NINE: "9", TEN: "10",
                    JACK: "J", QUEEN: "Q", KING: "K", ACE: "A"}

point_value = {
    SEVEN: 0,
    EIGHT: 0,
    NINE: 0,
    TEN: 10,
    JACK: 2,
    QUEEN: 3,
    KING: 4,
    ACE: 11
}
point_valueT = { #trump card values
    SEVEN: 0,
    EIGHT: 0,
    NINE: 14,
    TEN: 10,
    JACK: 20,
    QUEEN: 3,
    KING: 4,
    ACE: 11
}

TOTALPOINTS = 162

glory_order = [SEVEN,EIGHT,NINE,TEN,JACK,QUEEN,KING,ACE]
trump_order = [SEVEN,EIGHT,QUEEN,KING,TEN,ACE,NINE,JACK]
normal_order= [SEVEN,EIGHT,NINE,JACK,QUEEN,KING,TEN,ACE]

class Card(object):
    def __init__(self,value,color):
        self.value = value
        self.color = color
        self.index = self.color*8+self.value
        self.owner = None
        self.is_trump = False
        self.point_value = 0

    def __str__(self):
        return "Card({}, {})".format(valuenames[self.value],colornames[self.color])

    def __repr__(self):
        return str(self)

    def pretty(self):
        return suit_to_unicode[self.color]+short_valuenames[self.value]

    def __gt__(self,other):
        if self.is_trump:
            if not other.is_trump: return True
            return trump_order.index(self.value) > trump_order.index(other.value)
        if other.is_trump: return False
        return normal_order.index(self.value) > normal_order.index(other.value)

    def __le__(self,other):
        if self.is_trump == other.is_trump and self.value == other.value:
            return False
        return not (self > other)

    def __eq__(self, other):
        return (self.color == other.color and self.value == other.value)

def fake_card():
    return Card(FAKE, FAKE)

def index_to_card(index):
    color, value = divmod(index, 8)
    return Card(value, color)

def create_deck():
    return Cards([index_to_card(i) for i in range(32)])

def random_cards(amount):
    l = list(range(32))
    random.shuffle(l)
    return Cards([index_to_card(i) for i in l[:amount]])

def highest_card(cards, trump=None):
    if trump:
        for c in cards:
            c.is_trump = (c.color == trump)

    color = cards[0].color

    l = []
    cards = sorted(cards)
    for c in cards:
        if c.color == color or c.is_trump:
            l.append(c)

    return l[-1]

class Cards(list):
    """
    A overload of a list to add additional functions to deal with cards
    """

    def filter(self, func):
        return Cards(filter(func, self))

    def sorted(self):
        self.sort()
        return self

    def filter_color(self, color):
        '''Creates a new Cards object with only cards with that color'''
        return Cards([a for a in self if a.color == color])

    def filter_value(self, value):
        '''Creates a new Cards object with only cards with that value'''
        return Cards([a for a in self if a.value == value])

    def higher_then(self, c):
        '''Creates a new Cards object with only cards higher then the one given
            and of the correct color'''
        return Cards([a for a in self if a>c and a.color==c.color])

    def has(self, c):
        '''c is either a Card object or a number.
        Returns wether we have that card or a card of that value (if it is a number)'''
        if isinstance(c, Card):
            a = [b for b in self if b == c]
        else:
            a = [b for b in self if b.value == c]
        if a: return a[0]
        else: return False

    def values(self):
        return list(set([c.value for c in self]))

    def colors(self):
        return list(set([c.color for c in self]))

    def get_trumps(self):
        '''Returns a new Cards object with only trumps'''
        return Cards([a for a in self if a.is_trump])

    def pretty(self):
        s= ""
        for color in range(4):
            vals = ", ".join([short_valuenames[v] for v in self.cards.filter_color(color).values()])
            s += "{} {}\n".format(suit_to_unicode[color], vals)
        return s.strip()

def card_points(cards, trump=None):
    val = 0
    for c in cards:
        if c.is_trump or c.color == trump:
            val += point_valueT[c.value]
        else: val += point_value[c.value]
    return val

def glory_calculation(cards, trump):
    glory = 0
    for color in range(4):
        values = Cards(cards).filter_color(color).values()
        if color == trump and QUEEN in values and KING in values: #"stuk"
            glory += 20
        if len(values) < 3: continue #only glory with at least 3 cards
        order = sorted([glory_order.index(i) for i in values])
        if len(values) == 3:
            if (order[2] == order[0] + 2) and (order[1] == order[0] + 1):
                glory += 20
            return glory
        #len(values) = 4
        if (order[3] == order[0] + 3) and (order[2] == order[0] + 2) and (order[1] == order[0] + 1):
            glory += 50
            return glory
        if (order[2] == order[0] + 2) and (order[1] == order[0] + 1):
            glory += 20
            return glory
        if (order[3] == order[1] + 2) and (order[2] == order[1] + 1):
            glory += 20
            return glory
    return glory
    
