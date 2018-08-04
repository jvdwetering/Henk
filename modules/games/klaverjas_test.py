from cards import *
from klaverjas_ai import AI as BaseAI, BasePlayer
from klaverjas_ai2 import AI as AI0
#from klaverjas_ai_old import AI as AI0
#from klaverjas_ai3 import AI as AI1
#from klaverjas_ai4 import AI as AI2
import random

#seed = "uihgwrkftd"  # AI gooit aas weg aan de tegenstander

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

def time_test(ai=BaseAI):
    #import cards
    #cards.PRINT = False
    t = time.time()
    for i in range(100):
        g = Game(silent=2, players=[ai]*4)
        g.should_pause = False
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
        g = Game(silent=2, seed=r.randint(10000000,20000000), players = players, cancelpoints=False)
        g.play_game()
        tpoints1 += g.points1
        tpoints2 += g.points2
        if g.points1 <= g.points2:
            tnat += 1
        if i%(ngames//10) == 0:
            print(i, end='. ')
    print("\nTotal games played:", ngames)
    print("Average score: {!s} vs {!s}".format(tpoints1/ngames, tpoints2/ngames))
    print("Percentage gehaald: ", (1-tnat/ngames)*100)
    tpointsd = tpoints1-tpoints2
    return (tpoints1, tpoints2, tnat, tpointsd)
    
def performance_compare(ai_class1, ai_class2, ai_class3):
    game1 = performance_test(ai_class1, ai_class3)
    game2 = performance_test(ai_class3, ai_class1)
    game3 = performance_test(ai_class2, ai_class3)
    if ai_class2 is ai_class3:
        game4 = game3
    else: game4 = performance_test(ai_class3, ai_class2)
    print("Aanvallend heeft AI 1", game1[2], "keer nat en", game1[3], "punten verschil.")
    print("Verdedigend heeft AI 1 de ander", game2[2], "keer nat gespeeld en", game2[3], "punten verschil gemaakt.")
    print("Aanvallend heeft AI 2", game3[2], "keer nat en", game3[3], "punten verschil.")
    print("Verdedigend heeft AI 2 de ander", game4[2], "keer nat gespeeld en", game4[3], "punten verschil gemaakt.\n")
    
    if game1[2]>game3[2]:
        print("Aanvallend is AI 2", game1[2]-game3[2],"keer minder vaak nat gegaan")
    elif game1[2]<game3[2]:
        print("Aanvallend is AI 1", game3[2]-game1[2],"keer minder vaak nat gegaan")
    elif game1[2]==game3[2]:
        print("Aanvallend zijn AI 1 en AI 2 even vaak nat gegaan")
        
    if game1[3]>game3[3]:
        print("Aanvallend heeft AI 1", game1[3]-game3[3],"meer puntenverschil weten te behalen")
    elif game1[3]<game3[3]:
        print("Aanvallend heeft AI 2", game3[3]-game1[3],"meer puntenverschil weten te behalen")
    elif game1[3]==game3[3]:
        print("Aanvallend hebben AI 1 en AI 2 exact hetzelfde puntenverschil behaald. Wonderlijk.")
        
    if game2[2]>game4[2]:
        print("Verdedigend heeft AI 2 de ander", game2[2]-game4[2],"keer minder vaak nat gespeeld")
    elif game2[2]<game4[2]:
        print("Verdedigend heeft AI 1 de ander", game4[2]-game2[2],"keer minder vaak nat gespeeld")
    elif game2[2]==game4[2]:
        print("Verdedigend hebben AI 1 en AI 2 de ander even vaak nat gespeeld")
        
    if game2[3]>game4[3]:
        print("Verdedigend heeft AI 1 ", game2[3]-game4[3],"meer puntenverschil weten te behalen")
    elif game2[3]<game4[3]:
        print("Verdedigend heeft AI 2 ", game4[3]-game2[3],"meer puntenverschil weten te behalen")
    elif game2[3]==game4[3]:
        print("Verdedigend hebben AI 1 en AI 2 exact hetzelfde puntenverschil behaald. Magistraal.")
    
def find_divergent_game(ai_class1, ai_class2):
    '''Looks for a game where the first class did at least 20 points worse than the second class'''
    players1 = [ai_class1, ai_class2, ai_class1, ai_class2]
    players2 = [ai_class2, ai_class1, ai_class2, ai_class1]
    n = 0
    while True:
        n += 1
        if n%100 == 0:
            print(n, end='. ')
        seed = random.randint(1000000,2000000)
        random.seed(seed)
        g1 = Game(silent=2, seed=seed, players=players1, cancelpoints=False)
        g1.play_game()
        random.seed(seed)
        g2 = Game(silent=2, seed=seed, players=players2, cancelpoints=False)
        g2.play_game()
        s1 = g1.points1 - g1.points2
        s2 = g2.points1 - g2.points2
        if s1 < s2-30:
            print("\nseed: ", seed)
            #return g1,g2 
            game_diff(g1,g2)
            return g1,g2
                    
def game_diff(g1, g2):
    '''Gives the first divergence point of two given games'''
    msg = "{} ({!s}) {!s} | {!s} ({!s})    vs  {} ({!s}) {!s} | {!s} ({!s})\n".format(
            suit_to_unicode[g1.trump], g1.pointsglory1, g1.points1, g1.points2, g1.pointsglory2,
            suit_to_unicode[g2.trump], g2.pointsglory1, g2.points1, g2.points2, g2.pointsglory2)
    for i in range(len(g1.round_lists)):
        if g1.round_lists[i] == g2.round_lists[i]: continue
        else: break
    
    for rnd in range(i):
        msg += g1.pretty_round(rnd)

    msg += "\nDifference here\nGame 1:\n"
    msg += g1.pretty_round(i)
    msg += g1.chatter[i]
    msg += "\n\nGame 2:\n"
    msg += g2.pretty_round(i)
    msg += g2.chatter[i]
    print(msg)
    


class Game(object):
    def __init__(self, silent=0, seed=None,players=[], cancelpoints=True):
        self.should_pause = True if silent < 2 else False
        self.silent = silent
        self.cancelpoints = cancelpoints # whether points should be added to other team in case of wet
        self.chatter = []
        if not seed: self.seed = random.randint(10000000,20000000)
        else: self.seed = seed
        self.players = []
        self.deck = None
        self.pindex = {}
        if not players: players = [BaseAI]*4
        for i, ai_class in enumerate(players):
            p = ai_class(i)
            p.printer = self.ai_chatter
            if silent == 2 or silent == 1 and i!=0:
                p.silent = False # True
            self.pindex[p] = i
            self.players.append(p)
        self.initialize()

    def ai_chatter(self, msg):
        if self.round > len(self.chatter):
            self.chatter.append(msg)
        else:
            self.chatter[self.round-1] += "\n"+msg
        if self.silent < 2: print(msg)

    def give_cards(self):
        r = random.Random()
        r.seed(self.seed)
        self.deck = create_deck()
        r.shuffle(self.deck)
        for i in range(4):
            self.players[i].give_cards(Cards([self.deck[i*8+j] for j in range(8)]))

    def initialize(self):
        self.round = 1
        self.round_lists = []
        self.glory_lists = []
        self.p1, self.p2, self.p3, self.p4 = self.players
        self.p1.set_partner(self.p3.index)
        self.p3.set_partner(self.p1.index)
        self.p2.set_partner(self.p4.index)
        self.p4.set_partner(self.p2.index)
        self.p1.is_playing = True
        self.p3.is_playing = True
        self.points1 = 0
        self.points2 = 0
        self.pointsglory1 = 0
        self.pointsglory2 = 0
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
            self.pointsglory1 += glory
            self.points1 += points + glory
            if self.round == 8: self.points1 += 10
        else:
            self.pointsglory2 += glory
            self.points2 += points + glory
            if self.round == 8: self.points2 += 10
        for p in self.players:
            p.show_trick(cards, self.round)
        self.round_lists.append(cards)
        self.glory_lists.append(glory)
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
            self.pointsglory1 += 100
            self.points1 += 100

        if self.points1 < self.points2:
            if self.silent < 2: pp("Wet")
            if self.cancelpoints:
                self.points2 += self.points1
                self.points1 = 0

    def pretty_round(self, rnd):
        msg = ""
        k = rnd
        cards = self.round_lists[rnd]
        for i,c in enumerate(cards):
            c.played_index = i
        cardsorted = Cards(sorted(cards,key=lambda c: self.players[c.owner].index))
        for p,c in [(self.players[c.owner],c) for c in cardsorted]:
            if c.played_index == 0:
                msg += "{}".format(("*["+p.name+"]*").center(11))
            else:
                msg += "{}".format(p.name.center(11))
        msg += "\n"
        h = highest_card(cards,self.trump)
        for c in cardsorted:
            if c == h: msg += "{}".format(("*["+c.pretty()+"]*").center(10))
            else: msg += "{}".format(c.pretty().center(10))
        msg += "\n"
        if self.glory_lists[k]:
            msg += "{!s} roem geklopt".format(self.glory_lists[k]) + "\n"
        msg += "\n"
        return msg
    
    def game_string(self):
        msg = "Klaverjas potje met seed {!s}\n".format(self.seed)
        msg += "Team 1: *{}*, *{}*\n".format(self.p1.name, self.p3.name)
        msg += "Team 2: {}, {}\n".format(self.p2.name, self.p4.name)
        msg += "Troef is {}\n".format(suit_to_unicode[self.trump])
        if self.pointsglory1: msg += "{!s} (+ {!s} roem)".format(self.points1-self.pointsglory1,self.pointsglory1)
        else: msg += "{!s}".format(self.points1)
        msg += " vs "
        if self.pointsglory2: msg += "{!s} (+ {!s} roem)".format(self.points2-self.pointsglory2,self.pointsglory2)
        else: msg += "{!s}".format(self.points2)
        
        if self.points1 == 0 or self.points2 == 0: msg += ". Pit!\n\n"
        elif self.points1 <= self.points2: msg += ". Nat!\n\n"
        else: msg += "\n\n"

        for rnd in range(len(self.round_lists)):
            msg += self.pretty_round(rnd)
        msg = "\n".join(s.strip() for s in msg.splitlines())
        return msg

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
    #seed = 17419590
    seed = 1004
    g = Game(seed=seed, players=[AI0]*4)
    g.play_game()
#if __name__ == '__main__':
#    g1, g2 = find_divergent_game(NewAI, BaseAI)
#    print(game_diff(g1,g2))
