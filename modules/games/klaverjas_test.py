from cards import *
from klaverjas_ai import AI as BaseAI, BasePlayer
from klaverjas_ai2 import AI as NewAI
import random

seed = "uihgwrkftd"  # AI gooit aas weg aan de tegenstander

def test_trump_choice(seed):
    deck = create_deck()
    r = random.Random()
    if seed:
        r.seed(seed)
    r.shuffle(deck)
    ai = BaseAI(0)
    ai.set_partner(ai)
    cards = Cards(sorted(deck[:8],key=lambda c:c.color))
    ai.give_cards(cards)
    colors = [[],[],[],[]]
    for c in cards:
        colors[c.color].append(c)
    for i in range(4):
        print(colornames[i]+": " + ", ".join([valuenames[c.value] for c in colors[i]]))
    trump = ai.pick_trump()
    print("Chosen " + colornames[trump])

import time

#from game import Game

def time_test():
    #import cards
    #cards.PRINT = False
    t = time.time()
    for i in range(100):
        g = Game(silent = 2)
        g.should_pause = False
        g.initialize()
        g.play_game()

    delta = time.time() - t

    print("Took %.2f seconds" % delta)
    #cards.PRINT = True


def performance_test(ai_class1, ai_class2=BaseAI, ngames=1000):
    seed = 500
    r = random.Random()
    r.seed(seed)
    random.seed(seed)
    players = [ai_class1, ai_class2, ai_class1, ai_class2]
    tpoints1 = 0
    tpoints2 = 0
    tnat = 0
    for i in range(ngames):
        g = Game(silent=2, seed=r.randint(10000000,20000000), players = players)
        g.play_game()
        tpoints1 += g.points1
        tpoints2 += g.points2
        if g.points1 <= g.points2:
            tnat += 1
        if i%100 == 0:
            print(i, end='. ')
    print("\nTotal games played:", ngames)
    print("Average score: {!s} vs {!s}".format(tpoints1/ngames, tpoints2/ngames))
    print("Percentage gehaald: ", (1-tnat/ngames)*100)
    return tpoints1, tpoints2, tnat
    



class Game(object):
    def __init__(self, silent=0, seed=None,players=[]):
        self.should_pause = True if silent < 2 else False
        self.silent = silent
        if not seed: self.seed = random.randint(10000000,20000000)
        else: self.seed = seed
        self.players = []
        self.deck = None
        self.pindex = {}
        if not players: players = [BaseAI]*4
        for i, ai_class in enumerate(players):
            p = ai_class(i)
            if silent == 2 or silent == 1 and i!=0:
                p.silent = True
            self.pindex[p] = i
            self.players.append(p)
        self.initialize()

    def give_cards(self):
        r = random.Random()
        r.seed(self.seed)
        self.deck = create_deck()
        r.shuffle(self.deck)
        for i in range(4):
            self.players[i].give_cards(Cards([self.deck[i*8+j] for j in range(8)]))

    def initialize(self):
        self.round = 1
        self.p1, self.p2, self.p3, self.p4 = self.players
        self.p1.set_partner(self.p3.index)
        self.p3.set_partner(self.p1.index)
        self.p2.set_partner(self.p4.index)
        self.p4.set_partner(self.p2.index)
        self.p1.is_playing = True
        self.p3.is_playing = True
        self.points1 = 0
        self.points2 = 0
        self.currentplayer = 0

        self.give_cards()
        if self.silent < 2: pp("Player 1 hand:\n%s" % self.players[0].hand_string())
        
    def do_round(self):
        cards = Cards()
        for i in range(4):
            p = self.players[(self.currentplayer+i)%4]
            cards.append(p.play_card(self.round, cards))
            if self.silent < 2: pp("{}: {}".format(p.name, cards[-1].pretty()))
        h = highest_card(cards,self.trump)
        winner = h.owner
        points = card_points(cards, self.trump)
        glory = glory_calculation(cards, self.trump)
        if self.silent < 2: pp("Points: %d" % points)
        if glory > 0:
            if self.silent < 2: pp("Glory! %d points" % glory)
        n = winner
        if self.silent < 2: pp("Player %d wins this round with a %s" % (n+1, str(h)))
        if n == 0 or n == 2:
            self.points1 += points + glory
            if self.round == 8: self.points1 += 10
        else:
            self.points2 += points + glory
            if self.round == 8: self.points2 += 10
        for p in self.players:
            p.show_trick(cards, self.round)
        self.round += 1
        self.currentplayer = n
##        if self.round == 7:
##            pp(str(len(list(self.p1.generate_all_distributions(self.round, [])))))
##        if self.silent < 2:
##            pp("Unkown deck sizes: {!s}, {!s}, {!s}".format(*[len(d) for d in self.p1.unknown_cards]))
##            if self.round>3:
##                poss = 0
##                for _ in self.p1.generate_all_distributions(self.round, []):
##                    poss += 1
##                    if poss >= 10000:
##                        break
##                if poss == 10000: pp("Possible distributions: > 10000")
##                else: pp("Possible distributions: {!s}".format(poss))
        
        

    def play_game(self):
        self.trump = self.players[0].pick_trump()
        if self.silent < 2: pp("Player 1 has chosen trump %s" % colornames[self.trump])
        [self.players[i].set_trump(self.trump) for i in range(4)]
        
        for i in range(8):
            self.do_round()
            if self.should_pause:
                s = input(">> ")
                if s=="q":
                    break
            

        if self.silent < 2:
            pp("Score: \nTeam 1: %d points\nTeam 2: %d points" % (self.points1, self.points2))
        
        if self.points2 == 0: 
            if self.silent < 2: pp("Pit!")
            self.points1 += 100

        if self.points1 < self.points2:
            if self.silent < 2: pp("Wet")
            self.points2 += self.points1
            self.points1 = 0

class RealPlayer(BasePlayer):
    def __init__(self, index):
        super().__init__(index)
        self.name = "Speler"

    def pick_trump(self):
        print("%s pick a trump color: [H]earts, [D]iamonds, [C]lubs, [S]pades")
        r = input("H/D/C/S: ").strip()
        if r.upper().startswith('H'): return HEARTS
        if r.upper().startswith('D'): return DIAMONDS
        if r.upper().startswith('R'): return DIAMONDS
        if r.upper().startswith('C'): return CLUBS
        if r.upper().startswith('K'): return CLUBS
        if r.upper().startswith('S'): return SPADES
        print("AHHH moeilijk")
        raise Exception

    def play_card(self, *args):
        print("%s play a card" % self.name)
        card = raw_input_card("Cardname: ")
        card.owner = self.index
        print(card)
        return card


def raw_input_card(s):
    while True:
        r = input(s).upper().strip()
        c = r[0]
        if c == 'H': color = HEARTS
        elif c == 'D' or c == 'R': color = DIAMONDS
        elif c == 'C' or c == 'K': color = CLUBS
        elif c == 'S': color = SPADES
        else:
            print("ERRAWR")
            print("Try again")
            continue
        v = r[1:]
        if v == 'J' or v == 'B': value = JACK
        elif v == 'Q' or v == 'V': value = QUEEN
        elif v == 'K': value = KING
        elif v == 'A': value = ACE
        elif v == '7': value = SEVEN
        elif v == '8': value = EIGHT
        elif v == '9': value = NINE
        elif v == '10': value = TEN
        else:
            print("ERRAWR")
            print("Try again")
            continue
        card = Card(value, color)
        return card

if __name__ == '__main__':
    g = Game(seed=seed, players=[BaseAI,BaseAI,BaseAI,BaseAI])
    g.play_game()
