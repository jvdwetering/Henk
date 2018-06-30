from cards import *
from klaverjas_ai import AI
import random

def test_trump_choice(seed):
    deck = create_deck()
    r = random.Random()
    if seed:
        r.seed(seed)
    r.shuffle(deck)
    ai = AI(0)
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
    import cards
    cards.PRINT = False
    t = time.time()
    for i in range(100):
        g = Game()
        g.should_pause = False
        g.initialize()
        g.play_game()

    delta = time.time() - t

    print("Took %.2f seconds" % delta)
    cards.PRINT = True



class Game(object):
    def __init__(self):
        self.should_pause = True
        self.players = []
        self.deck = None
        self.pindex = {}
        for i in range(4):
            p = AI(i)
            self.pindex[p] = i
            self.players.append(p)

    def give_cards(self):
        self.deck = create_deck()
        random.shuffle(self.deck)
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
        pp("Player 1 hand:\n%s" % self.players[0].hand_string())
        
    def do_round(self):
        cards = Cards()
        for i in range(4):
            cards.append(self.players[(self.currentplayer+i)%4].play_card(self.round, cards))
            pp("Player %d: %s" % ((self.currentplayer+i)%4+1, str(cards[-1])))
        h = highest_card(cards,self.trump)
        winner = h.owner
        points = card_points(cards, self.trump)
        glory = glory_calculation(cards, self.trump)
        pp("Points: %d" % points)
        if glory > 0:
            pp("Glory! %d points" % glory)
        n = winner
        pp("Player %d wins this round with a %s" % (n+1, str(h)))
        if n == 0 or n == 2:
            self.points1 += points + glory
            if self.round == 8: self.points1 += 10
        else:
            self.points2 += points + glory
            if self.round == 8: self.points2 += 10
        for p in self.players:
            p.show_trick(cards, self.round)
        self.currentplayer = n
        self.round += 1

    def play_game(self):
        self.trump = self.players[0].pick_trump()
        pp("Player 1 has chosen trump %s" % colornames[self.trump])
        [self.players[i].set_trump(self.trump) for i in range(4)]
        
        for i in range(8):
            self.do_round()
            if self.should_pause:
                s = input(">> ")
                if s=="q":
                    break
            

        pp("Score: \nTeam 1: %d points\nTeam 2: %d points" % (self.points1, self.points2))
        
        if self.points1 < self.points2:
            pp("Wet")
            self.points2 += self.points1
            self.points1 = 0

