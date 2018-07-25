if __package__ is None or __package__ == '':
    from cards import JACK, NINE, ACE, TEN, QUEEN, KING, EIGHT, SEVEN
    from cards import (create_deck, highest_card, colornames, valuenames,
                        pp, Card, Cards, glory_calculation, fake_card, cmp)
else:
    from .cards import JACK, NINE, ACE, TEN, QUEEN, KING, EIGHT, SEVEN
    from .cards import create_deck, highest_card, colornames, valuenames
    from .cards import pp, Card, Cards, glory_calculation, fake_card, cmp

import random
import itertools

class BasePlayer(object):
    def __init__(self, index):
        self.index = index
        self.name = ["Henk", "Ingrid", "Klaas", "Bert"][index]
        self.silent = False
        self.reset()

    def reset(self):
        self.partner = None
        self.cards = Cards()
        self.discarded = Cards()
        self.trump = None
        self.is_playing = False
        #We wan't to record what the possible cards are for every player
        self.unknown_cards = [create_deck(), create_deck(), create_deck()]
        #possible_cards[0] is the player next, [1] is our mate, and [2] is the player before us
        index = self.index
        self.unknown_cards[0].owner = (1 + index) % 4
        self.unknown_cards[1].owner = (2 + index) % 4
        self.unknown_cards[2].owner = (3 + index) % 4
        self.mystery_cards = create_deck()
        self.mate_prefered_colors = []
        
    def pp(self, s, index=-1):
    	if self.silent: return
    	if index == -1:
    		self.printer("{}: {}".format(self.name, s))
    	else:
    		if self.index == index:
    			self.printer("{}: {}".format(self.name,s))

    def hand_string(self):
        colors = [[],[],[],[]]
        for c in self.cards:
            colors[c.color].append(c)
        s = ""
        for i in range(4):
            s += colornames[i]+": " + ", ".join([valuenames[c.value] for c in colors[i]]) + "\n"
        return s

    def set_partner(self, index):
        self.partner = index

    def set_trump(self,trump):
        self.trump = trump
        for c in self.cards.filter_color(trump):
            c.is_trump = True
        for deck in self.unknown_cards:
            for card in deck.filter_color(trump):
                card.is_trump = True
        for c in self.mystery_cards.filter_color(trump):
            c.is_trump = True

    def give_cards(self,cards):
        self.cards = cards
        self.cards.sort()
        for c in self.cards:
            c.owner = self.index
            for deck in self.unknown_cards:
                deck.remove(c)
            self.mystery_cards.remove(c)


    def index_to_deck(self, index):
        for d in self.unknown_cards:
            if d.owner == index:
                return d
        raise NotImplementedError("Wrong index given")

    def index_to_mate(self, index):
        if index == 0: return 2
        if index == 1: return 3
        if index == 2: return 0
        if index == 3: return 1
    
    def player_is_playing(self, index): #returns wether the player index is on the 'playing' team
        if self.is_playing and (index == self.index or index == self.partner):
            return True
        if not self.is_playing and (index != self.index and index != self.partner):
            return True
        return False

    def is_high(self, card):
        '''returns wether card is the highest one of that color'''
        for d in self.unknown_cards:
            if card.owner == d.owner: continue
            filt = d.higher_then(card)
            if filt:
                return False
        return True

    def show_trick(self,cards, round):
        pass

    def legal_cards(self, played_cards):
        if not played_cards: return self.cards #first to play, everything is legal
        played_cards = Cards(played_cards)
        color = played_cards[0].color
        played_trumps = played_cards.filter_color(self.trump)
        highest = highest_card(played_cards)
        if highest.owner == None:
            raise KeyError("Played card doesn't have owner")
        winning = (highest.owner == self.partner)
        cards = self.cards.filter_color(color)
        if cards: #we can confess colour
            if color != self.trump: return cards #no trumps so no restrictions
            #must not undertrump
            higher = [t for t in cards if t>highest]
            if higher: return higher # We must overtrump
            return cards
        trumps = self.cards.get_trumps()
        if not trumps: return self.cards # Don't have any trumps so everything is legal
        if not played_trumps and not winning: return trumps # We aren't winning and we have trumps, so we must play one of those
        higher = [t for t in trumps if t>highest]
        if higher and not winning: return higher # We must overtrump
        c = self.cards.filter(lambda c: c.color!=self.trump) #Any card except trumps
        c.extend(higher)
        if c: return c
        return self.cards #we can't overtrump, but we only have trumps so we need to play them.






class AI(BasePlayer):
    def pick_trump(self):
        maxval = 0
        picked = 0
        for color in range(4): #we go trough every color and assign a value to them
            cards = self.cards.filter_color(color)
            values = cards.values()
            val = 0
            l = len(cards)
            if l == 1: val = -10
            if l == 2: val = 10
            if l == 3: val = 20
            if l == 4: val = 40
            if l > 4: val = 70
            if JACK in values:
                val += 30
                if NINE in values: val += 20
            else:
                if NINE in values: val += 12
            if ACE in values: val += 7
            if TEN in values: val += 5
            if KING in values and QUEEN in values: val += 7
            if val>maxval:
                maxval = val
                picked = color
        return picked

    def is_trump(self, card):
        return (card.color == self.trump)
    def is_not_trump(self, card):
        return (card.color != self.trump)
    def check_color(self, color):
        def is_color(card):
            return card.color == color
        return is_color
    def has_trump(self,val):
        return bool(self.cards.get_trumps().has(val))


    def show_trick(self,cards, round):
        '''Here we analyze the played cards, and try to conclude some information
        on the hands of the players'''
        color = cards[0].color
        p = cards[0].owner
        glory = glory_calculation(cards,self.trump)

        def remove_all_in_color(index, color, exceptions=[]):
            if index == self.index: return
            d = self.index_to_deck(index)
            for cc in  [a for a in d if (a.color == color and a.value not in exceptions)]:
                d.remove(cc)
        
        if p != self.index: #we did not start this round
            d = self.index_to_deck(p)
            if round == 1:
                if color != self.trump: #starting player didn't play a trump
                    if Card(JACK, self.trump) in d:
                        d.remove(Card(JACK, self.trump))
                else:
                    if cards[0].value == NINE:
                        if Card(JACK, self.trump) in d:
                            self.player_has_card(p, Card(JACK, self.trump))
                    if cards[0].value == KING:
                        if Card(QUEEN, self.trump) in d:
                            self.player_has_card(p, Card(QUEEN, self.trump))

            #if not self.player_is_playing(p): #player starting didn't play
            if cards[0].value == TEN and color != self.trump:
                if Card(ACE, color) in d:
                    self.player_has_card(p, Card(ACE, color))

        if color == self.trump and cards[0].value == JACK:
            for i in [1,3]:
                if cards[i] == Card(NINE, self.trump) and glory < 25:
                    remove_all_in_color(cards[i].owner, self.trump)
                if cards[i] == Card(QUEEN, self.trump):
                    if glory:
                        remove_all_in_color(cards[i].owner, self.trump, [NINE])
                        
                    
        if p == self.index and highest_card(cards).owner == self.index: #we are playing and have won
            m = cards[2] # the card of your mate
            if m.color != color and m.color != self.trump: #mate didn't confess color and didn't trump
                if m.value in (SEVEN, EIGHT, NINE, ACE): #mate is signing
                    if m.color not in self.mate_prefered_colors:
                        self.mate_prefered_colors.append(m.color)
                        self.pp("Mate signed card color")
                elif m.value in (QUEEN, KING, TEN): #mate is de-signing the color
                    if m.color not in self.mate_prefered_colors: #if it was already signed, ignore this
                        if len(self.mate_prefered_colors) == 0:
                            self.mate_prefered_colors = list(range(4))
                            self.mate_prefered_colors.remove(self.trump)
                            self.mate_prefered_colors.remove(m.color)
                    
        if color == self.trump: #trump asked
            highest = cards[0]
            for (i,c) in enumerate(cards[1:]):
                if c.color == self.trump:
                    if c > highest:
                        highest = c
                    else: #didn't overtrump, remove those possibilities
                        if c.owner == self.index: continue
                        d = self.index_to_deck(c.owner)
                        for cc in [a for a in d if (a.color == self.trump and a > c)]:
                            d.remove(cc)
                else: #couldn't confess color
                    if c.owner == self.index: continue
                    remove_all_in_color(c.owner, self.trump)
        else: #not a trump asked
            highest = cards[0]
            for (i, c) in enumerate(cards[1:]):
                if c.color == color:
                    if c > highest: highest = c
                else: #couldn't confess color
                    if c.owner == self.index: continue
                    d = self.index_to_deck(c.owner)
                    for cc in [a for a in d if (a.color == color)]:
                        d.remove(cc)
                    if highest.owner != self.index_to_mate(c.owner):
                        if c.color != self.trump: #he didn't trump in
                            if highest.color != self.trump:
                                for cc in [a for a in d if (a.color == self.trump)]:
                                    d.remove(cc)
                            else:
                                for cc in [a for a in d if (a.color == self.trump and a > highest)]:
                                    d.remove(cc)
        
        highest = highest_card(cards)
        if highest.owner != cards[3].owner: #last person didn't win the round
            if highest.owner != cards[1].owner: #his mate also didn't
                if cards[3].color == color: #he confessed color
                    if glory > 20: #at least 40 glory, it would always have been better to prevent it
                        remove_all_in_color(cards[3].owner, color)
                    if glory == 20 and color != self.trump: #he might have chosen not to play the TEN
                        remove_all_in_color(cards[3].owner, color, [TEN])

        if color != self.trump:
            a = Card(ACE, color)
            if Card(ACE, color) in self.mystery_cards: #we haven't seen the ACE yet
                if a not in cards and cards[0].value!=TEN: #it is not played in this round
                    if self.trump not in Cards(cards).colors(): #not trumped in anywhere
                        self.pp("No Ace played in this round. How weird")
                        if cards[0].owner != self.index:
                            d = self.index_to_deck(cards[0].owner)
                            if a in d: d.remove(a)
                        if cards[2].owner != self.index:
                            d = self.index_to_deck(cards[2].owner)
                            if a in d: d.remove(a)
            if cards[0] == a: #ACE has been played
                t = Card(TEN, color)
                if cards[1] == t: remove_all_in_color(cards[1].owner, color)
                if cards[3] == t: #last person played a TEN
                    values = Cards(cards).filter_color(color).values()
                    if QUEEN in values:
                        if KING in values: remove_all_in_color(cards[3].owner, color, [JACK])
                        else: remove_all_in_color(cards[3].owner, color, [KING])
                    elif KING in values: remove_all_in_color(cards[3].owner, color, [QUEEN])
                    elif SEVEN in values and EIGHT in values:
                        remove_all_in_color(cards[3].owner, color, [NINE])
                    elif SEVEN in values and NINE in values:
                        remove_all_in_color(cards[3].owner, color, [EIGHT])
                    else:
                        remove_all_in_color(cards[3].owner, color)
            
                                    
        self.remove_known_cards(cards)

    def remove_known_cards(self, cards):
        for deck in self.unknown_cards:
            for c in cards:
                if c in deck:
                    deck.remove(c)
        for c in cards:
            if c in self.mystery_cards:
                self.mystery_cards.remove(c)
        
    def player_has_card(self, player, card):
        for d in self.unknown_cards:
            if d.owner == player: continue
            if card in d:
                d.remove(card)

    def play_this_card(self, card): #helper function to remove it from lists
        self.cards.remove(card)
        self.discarded.append(card)
        card.owner = self.index
        return card

    def pick_non_trump(self):
        '''Pick a non-trump card to start a round with'''
        non_trumps = self.cards.filter(self.is_not_trump).sorted()
        if not non_trumps:
            self.pp("We only have trumps left")
            high_cards = Cards([c for c in self.cards if self.is_high(c)])
            filt = [c for c in high_cards if self.glory_possibility(c)]
            if filt:
                return filt[0]
            if len(high_cards) >= len(self.mystery_cards.get_trumps()):
                return high_cards[0]
            elif len(high_cards) > 1:
                return high_cards[0]
            else:
                m = len(self.unknown_cards[0].get_trumps())
                n = len(self.unknown_cards[2].get_trumps())
                if m <= 1 and n <= 1:
                    if high_cards:
                        return high_cards[0] #the other team only have a maximum of 1 trump each
                    return self.cards[0]
                else: #they might have more then 1 trump
                    if self.round >= 6: #don't risk it, play the lower 1
                        return sorted(self.cards)[0]
                    else:
                        if high_cards:
                            return high_cards[0]
                        return self.cards[0]
        high_cards = Cards([c for c in non_trumps if self.is_high(c)])
        if not high_cards:
            self.pp("We don't have a high card")
            if self.mate_prefered_colors:
                for color in self.mate_prefered_colors:
                    poss = non_trumps.filter_color(color)
                    if not poss: continue
                    self.pp("We play the signed color")
                    return poss[0]
            tens = Cards(non_trumps).filter_value(TEN)
            for color in tens.colors():
                poss = Cards(non_trumps).filter_color(color)
                if len(poss) > 1:
                    self.pp("We will try to free our TEN")
                    return poss[0]
            self.pp("Can't play a signed color, and no TEN to free. Play something low and safe")
            filt = [c for c in non_trumps if not self.glory_possibility(c)]
            if not filt: #there is always a glory chance
                filt = non_trumps
            lowest = Cards(filt).filter_value(list(sorted(Cards(filt).values()))[0])
            if not lowest:
                return self.cards.get_trumps()[0]
            return random.choice(lowest)

        poss = Cards([c for c in high_cards if self.glory_possibility(c)])
        if poss:
            self.pp("We have a high card with a chance for glory")
            if poss.filter_value(TEN):
                return random.choice(poss.filter_value(TEN))
            if poss.filter_value(ACE):
                return random.choice(poss.filter_value(ACE))
            return random.choice(poss)
        if high_cards.filter_value(TEN):
            return random.choice(high_cards.filter_value(TEN))
        if high_cards.filter_value(ACE):
            return random.choice(high_cards.filter_value(ACE))
        return random.choice(high_cards)

    def sign_mate(self):
        '''Pick a card to trow away at your mate (like he is going to win)'''
        self.pp("We pick a card to give to our mate")
        val = 0
        col = -1
        for color in range(4):
            if color == self.trump: continue
            filt = self.cards.filter_color(color)
            if filt.has(TEN):
                if len(filt) == 1:
                    if self.is_high(Card(TEN,color)):
                        if val < 1:
                            val = 1
                            col = color
                    else:
                        self.pp("We play a naked Ten")
                        return filt.has(TEN)
                else:
                    if filt.has(ACE):
                        val = 3
                        col = color
                    else: #we have a card below the Ten
                        if val < 2:
                            val = 2
                            col = color
        if val == 3:
            self.pp("We have the ace and a ten of a color. Play the Ace")
            return self.cards.filter_color(col).has(ACE)
        elif val > 0:
            self.pp("We have a Ten. Play it")
            return self.cards.filter_color(col).has(TEN)
        self.pp("We don't have a Ten.")

        aces = self.cards.filter_value(ACE)
        if aces: lowest = aces[0]
        for color in aces.colors():
            if color == self.trump: continue
            filt = self.cards.filter_color(color)
            if len(filt) == 1: #we only have the ace
                continue
            else:
                filt.sort()
                if filt[0] < lowest:
                    lowest = filt[0]
        if aces and lowest != aces[0]:
            self.pp("We trow a low card to sign we have a Ace")
            return lowest

        self.pp("We can't signal an Ace. Play some points")
        for king in self.cards.filter_value(KING):
            if not king.is_trump:
                return king
        for queen in self.cards.filter_value(QUEEN):
            if not queen.is_trump:
                return queen
        for jack in self.cards.filter_value(JACK):
            if not jack.is_trump:
                return jack
        self.pp("No points to trow away, trow away crap")
        return self.trow_away_card()
        
            
    def trow_away_card(self):
        '''Trow away a card, if you can't confess a card'''
        self.pp("We want to trow away a card")
        colors = self.cards.colors()
        if self.trump in colors:
            colors.remove(self.trump)
        if len(colors) == 1:
            self.pp("Trow away the lowest card we have of the only possible color")
            return sorted(self.cards.filter_color(colors[0]))[0]
        if len(colors) == 0:
            raise NotImplementedError("We only have trumps, shouldn't call this function")
        for color in colors:
            filt = self.cards.filter_color(color)
            if len(filt) >= 4:
                self.pp("We trow away the lowest card of the color we have the most of")
                return sorted(filt)[0]
            if not filt.has(TEN):
                self.pp("We don't have a Ten in this color, so it's safe to trow a card away there")
                return sorted(filt)[0]
        self.pp("We have a Ten in every playable color. Play a card in one of them")
        return sorted(self.cards.filter_color(colors[0]))[0]
            

    def play_card(self, rnum, played_cards):
        played_cards = Cards(played_cards)
        self.round = rnum
        legal = self.legal_cards(played_cards)
        if len(legal) == 1:
            self.pp("Only one legal card to play")
            return self.play_this_card(legal[0])
        trumps = self.cards.get_trumps().sorted()
        non_trumps = self.cards.filter(self.is_not_trump).sorted()
        if not played_cards:
            self.pp("We are playing this round")
            if self.is_playing:
                self.pp("We are playing this game")
                high_trumps = trumps.filter(self.is_high)
                filt = Cards([c for c in high_trumps if self.glory_possibility(c)])
                if filt:
                    self.pp("We have trumps with a chance of glory")
                    if KING in filt.values(): #king is high and there is glory possibility
                        return self.play_this_card(filt.has(KING))
                    if NINE in filt.values():
                        return self.play_this_card(filt.has(NINE))
                    return self.play_this_card(filt.sorted()[0])
                

                n = len(self.unknown_cards[0].get_trumps())
                m = len(self.unknown_cards[2].get_trumps())
                if n + m != 0:
                    self.pp("The other team might still have trumps")
                    if high_trumps:
                        return self.play_this_card(high_trumps[0])
                    if len(trumps) > 1:
                        filt = [c for c in trumps if not self.glory_possibility(c) and c.value!=NINE]
                        if filt:
                            return self.play_this_card(sorted(filt)[0])
                        return self.play_this_card(sorted(trumps)[0])
                    return self.play_this_card(self.pick_non_trump())
                return self.play_this_card(self.pick_non_trump())
            #We are not playing this game
            return self.play_this_card(self.pick_non_trump())
                             
        else: #someone else already played
            highest = highest_card(played_cards)
            winning = (highest.owner == self.partner)
            color = played_cards[0].color
            
            if color != self.trump and highest.value == TEN and played_cards[0].value == TEN: #a person came out with a 10, so he has the ace
                self.player_has_card(played_cards[0].owner, Card(ACE, color))
            if color == self.trump and highest.value == NINE and played_cards[0].value == NINE:
                self.player_has_card(played_cards[0].owner, Card(JACK, color))
            
            possibilities = self.cards.filter_color(color)
            played_trumps = played_cards.get_trumps()
            if len(possibilities) == 1: #only 1 possible card to play
                self.pp("Only one possible card to play")
                return self.play_this_card(possibilities[0])
            if len(possibilities) == 0:
                self.pp("Can't confess color")
                if trumps:
                    if winning:
                        self.pp("Our mate is winning, don't trump in")
                        if non_trumps:
                            if self.is_high(highest):
                                return self.play_this_card(self.sign_mate())
                            else:
                                return self.play_this_card(self.trow_away_card())
                        else:
                            return self.play_this_card(trumps[-1])
                    if len(trumps) == 1:
                        self.pp("We have exactly one trump")
                        c = trumps[0]
                        if not played_trumps:
                            self.pp("We have to trump in")
                            return self.play_this_card(c)
                        else:
                            h = highest_card(played_trumps)
                            if c>h:
                                self.pp("We can defeat the highest played trump, so do it")
                                return self.play_this_card(c)
                            else:
                                if non_trumps:
                                    self.pp("We can't over trump, so play another card")
                                    return self.play_this_card(self.trow_away_card())
                                else:
                                    return self.play_this_card(c)
                    else:
                        self.pp("We have more then one trump")
                        if played_trumps:
                            h = played_trumps.sorted()[-1]
                            filt = trumps.higher_then(h)
                            if filt:
                                self.pp("We can over trump, do it with the lowest one")
                                return self.play_this_card(filt[0])
                            else:
                                self.pp("We can't over trump")
                                poss = self.cards.filter(self.is_not_trump)
                                if poss:
                                    return self.play_this_card(self.trow_away_card())
                                else:
                                    return self.play_this_card(trumps[0])
                        else:
                            return self.play_this_card(trumps[0]) # we play our lowest trump
                else:
                    self.pp("We have no trump and we can't confess color")
                    if winning and self.is_high(highest):
                        return self.play_this_card(self.sign_mate())
                    else:
                        return self.play_this_card(self.trow_away_card())
            else:
                self.pp("We have more than 1 card of the right color")
                if color == self.trump:
                    filt = trumps.higher_then(highest)
                    if filt:
                        self.pp("We have to overtrump")
                        if len(filt) == 1:
                            return self.play_this_card(filt[0])
                        high_cards = filt.filter(self.is_high)
                        if high_cards:
                            c, glory = self.maxmin_glory(played_cards, deck=high_cards)
                            return self.play_this_card(c)
                        c, glory = self.maxmin_glory(played_cards, deck=filt, maximize=False)
                        return self.play_this_card(c)
                    if winning and self.is_high(highest):
                        c, glory = self.maxmin_glory(played_cards)
                        return self.play_this_card(c)
                    c, glory = self.maxmin_glory(played_cards,
                                                 deck=[a for a in trumps if a.value!=NINE], maximize=False)
                    return self.play_this_card(c)
                if len(played_cards) == 3: #we are the last one to play a card
                    if winning:
                        self.pp("We are currently winning the round, and are last in line")
                        c, glory = self.maxmin_glory(played_cards)
                        if glory:
                            self.pp("We can make glory! Do it")
                            return self.play_this_card(c)
                        self.remove_known_cards(played_cards)
                        possibilities.sort()
                        c = possibilities[-1]
                        if c.value == TEN and highest.value != ACE:
                            return self.play_this_card(c)
                        if self.is_high(c): #we have the highest in hand
                            return self.play_this_card(possibilities[-2])
                         #we play our highest card
                        return self.play_this_card(c)
                    else:
                        self.pp("we are not winning this round, try to still win")
                        filt = Cards([c for c in possibilities if c>highest])
                        if filt:
                            self.pp("we can win with a card.")
                            c, glory = self.maxmin_glory(played_cards, deck=filt)
                            if glory:
                                self.pp("And we can make glory! do it")
                                return self.play_this_card(c)
                            return self.play_this_card(filt.sorted()[0])
                        else:
                            self.pp("we can't win, play a low card")
                            c, glory = self.maxmin_glory(played_cards, maximize = False)
                            return self.play_this_card(c)
                else: #we are not the last one to play in this round
                    if winning:
                        if self.is_high(highest) or (highest.color == self.trump and color != self.trump):
                            self.pp("We are currently winning with the highest card")
                            c, glory = self.maxmin_glory(played_cards)
                            if glory:
                                self.pp("There is a possibility for glory, try it")
                                return self.play_this_card(c)
                            poss = possibilities.sorted()
                            if self.is_high(poss[-1]):
                                return self.play_this_card(poss[-2])
                            return self.play_this_card(poss[-1])
                        filt = Cards([c for c in possibilities if c>highest]).sorted()
                        if filt and self.is_high(filt[-1]):
                            f = [c for c in filt if self.is_high(c)]
                            c, glory = self.maxmin_glory(played_cards, deck=f)
                            if glory:
                                self.pp("Possibility for glory with high card, do it")
                                return self.play_this_card(c)
                            return self.play_this_card(f[-1])
                        self.pp("We are currently winning, but there is a higher card in play, duck")
                        c, glory = self.maxmin_glory(played_cards, maximize=False)
                        return self.play_this_card(c)
                    filt = Cards([c for c in possibilities if self.is_high(c)]).sorted()
                    if filt and filt[0] > highest: #this last check is because it might be trumped in
                        self.pp("We have a high card, maximize glory and points!")
                        c, glory = self.maxmin_glory(played_cards, deck=filt)
                        if glory:
                            return self.play_this_card(c)
                        return self.play_this_card(filt[-1])
                    else:
                        #TODO: Do a check for not wasting a TEN or ACE
                        self.pp("we can't win, play a low card")
                        c, glory = self.maxmin_glory(played_cards, maximize=False)
                        return self.play_this_card(c)

        raise NotImplementedError("Ahhhh, shouldn't get here!")

    def generate_all_distributions(self, rnum, played_cards):
        cardsleft = [9-rnum]*3
        for c in played_cards:
            cardsleft[(c.owner - self.index -1)%4] -= 1

        for c1 in itertools.combinations(self.unknown_cards[0], cardsleft[0]):
            r2 = self.unknown_cards[1].copy()
            for c in c1:
                if c in r2: r2.remove(c)
            if len(r2) < cardsleft[1]: continue
            for c2 in itertools.combinations(r2, cardsleft[1]):
                r3 = self.unknown_cards[2].copy()
                for c in c1+c2:
                    if c in r3: r3.remove(c)
                if len(r3) < cardsleft[2]: continue
                for c3 in itertools.combinations(r3, cardsleft[2]):
                    yield [c1,c2,c3]

    def generate_distribution(self, rnum, played_cards):
        cardsleft = [9-rnum]*3
        for c in played_cards:
            cardsleft[(c.owner - self.index -1)%4] -= 1

        while True:
            c1 = random.sample(self.unknown_cards[0], cardsleft[0])
            r2 = self.unknown_cards[1].copy()
            for c in c1:
                if c in r2: r2.remove(c)
            if len(r2) < cardsleft[1]: continue
            c2 = random.sample(r2, cardsleft[1])
            r3 = self.unknown_cards[2].copy()
            for c in c1+c2:
                if c in r3: r3.remove(c)
            if len(r3) < cardsleft[2]: continue
            c3 = random.sample(r3, cardsleft[2])
            return [c1,c2,c3]


    def glory_possibility(self, card):
        '''Returns wether there is still a chance this card can produce glory'''
        color = card.color
        d1 = self.unknown_cards[0].filter_color(color)
        d2 = self.unknown_cards[1].filter_color(color)
        d3 = self.unknown_cards[2].filter_color(color)
        if not d1: d1 = [fake_card()]
        if not d2: d2 = [fake_card()]
        if not d3: d3 = [fake_card()]
        for a in d1:
            for b in d2:
                for c in d3:
                    if glory_calculation([a,b,c], self.trump): continue #disregard glory caused by other cards
                    g = glory_calculation([card, a, b, c], self.trump)
                    if g: return True
        return False

    def maxmin_glory(self, cards, maximize = True, deck=None):
        c, glory = self.maxmin_glory_prime(cards, maximize, deck)
        if glory != 0:
            self.pp("Glory calculation: {0:.1f}".format(glory))
        return (c, glory)
    def maxmin_glory_prime(self, cards, maximize = True, deck=None):
        '''Returns the card that maximizes glory, and gives the expected glory.
        If maximize is False then it minimizes glory'''
        mult = 1
        if maximize == False: mult = -1
        if not cards:
            color = deck[0].color
        else: color = cards[0].color
        if deck==None:
            poss = self.cards.filter_color(color)
        else:
            poss = Cards(deck).filter_color(color)

        glory = 0
        if not maximize: glory = 120
        best = poss[0]
        if len(cards) == 3:
            for c in poss:
                g = glory_calculation(cards + [c], self.trump)
                if mult*cmp(g,glory) == 1:
                    glory = g
                    best = c
                elif g == glory and c < best:
                    best = c
            return (best, glory)
        if len(cards) == 2:
            other = self.unknown_cards[0].filter_color(cards[0].color) # the cards of the next player
            for c in poss:
                if not other:
                    g = glory_calculation(cards + [c], self.trump)
                    if mult*cmp(g,glory) == 1:
                        glory = g
                        best = c
                    elif g == glory and c < best:
                        best = c
                else:
                    g = 0
                    for b in other:
                        g += glory_calculation(cards + [c,b], self.trump)
                    g = float(g)/len(other) # average glory
                    if mult*cmp(g,glory) == 1:
                        glory = g
                        best = c
                    elif g == glory and c < best:
                        best = c
            return (best, glory)
        if len(cards) == 1:
            other1 = self.unknown_cards[0].filter_color(cards[0].color)
            other2 = self.unknown_cards[0].filter_color(cards[0].color)
            if not other1:
                other1 = other2
                other2 = []
            if not other1 and not other2: #only possibility is stuk
                if maximize:
                    for c in poss:
                        g = glory_calculation(cards + [c], self.trump)
                        if g > glory: return (c, glory)
                else:
                    for c in poss:
                        g = glory_calculation(cards + [c], self.trump)
                        if g == 0: return (c,0)
                return (poss[0], 0)
            if not other2:
                for c in poss:
                    g = 0
                    for b in other1:
                        g += glory_calculation(cards + [c,b], self.trump)
                    g = float(g)/len(other1)
                    if mult*cmp(g,glory) == 1:
                        glory = g
                        best = c
                    elif g == glory and c < best:
                        best = c
                return (best, glory)
            for c in poss:
                g = 0
                for b in other1:
                    for a in other2:
                        g += glory_calculation(cards + [c,b,a], self.trump)
                g = float(g)/(len(other1)*len(other2))
                if mult*cmp(g,glory) == 1:
                    glory = g
                    best = c
                elif g == glory and c < best:
                    best = c
            return (best, glory)

