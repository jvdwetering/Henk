if __package__ is None or __package__ == '':
    from cards import *
else:
    from .cards import *

import random
import itertools

class BasePlayer(object):
    def __init__(self, index):
        self.index = index
        self.name = ["Henk", "Ingrid", "Klaas", "Bert"][index]
        self.silent = False
        self.printer = pp
        self.reset()

    def reset(self):
        self.partner = None # Index of player on your team
        self.cards = Cards() # Current cards in your hand
        self.discarded = Cards() # Cards you have thrown out of your hand
        self.points1 = 0 # Points of the attacking team
        self.points2 = 0 # Points of the defending team
        self.trump = None # The suite of Trump
        self.is_playing = False # Whether we are the 'attacking' team.
        #We want to record what the possible cards are for every player
        self.unknown_cards = [create_deck(), create_deck(), create_deck()]
        #unknown_cards[0] is the player next, [1] is our mate, and [2] is the player before us
        index = self.index
        self.unknown_cards[0].owner = (1 + index) % 4
        self.unknown_cards[1].owner = (2 + index) % 4
        self.unknown_cards[2].owner = (3 + index) % 4
        for i,d in enumerate(self.unknown_cards):
            j = (index+i+1)%4
            d.owner = j
            for c in d: c.owner = j
        self.unknown_colours = [list(range(4))]*3 # The possible colours every player might have
        self.mystery_cards = create_deck() # The cards still in play that we don't have
        self.prefered_colors = {} # Dictionary containing information about which colors are desirable to play
        self.signed_colors = {} # The colors we have given information of to our mate
        self.flag_partner_started_with_trump = False
        
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
        '''returns whether card is the highest one of that colour'''
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
        for color in range(4): #we go trough every colour and assign a value to them
            cards = self.cards.filter_color(color)
            values = cards.values()
            val = 0
            l = len(cards)
            if l == 0: val = -50
            if l == 1: val = -10
            if l == 2: val = 10
            if l == 3: val = 20
            if l == 4: val = 30
            if l > 4: val = 60
            if JACK in values:
                val += 25
                if NINE in values: val += 25
            elif NINE in values: val += 14
            else: val -= 10
            if ACE in values: val += 8
            if TEN in values: val += 5
            if KING in values:
                if QUEEN in values: val += 7
                else: val += 3
            elif QUEEN in values:
                val += 1
            for color2 in range(4):
                if color2 == color: continue
                bijkaarten = self.cards.filter_color(color2).values()
                if ACE in bijkaarten:
                    if TEN in bijkaarten: val += 20
                    else: val += 10
                elif TEN in bijkaarten:
                    val += 5

            #self.pp("Trumpvalue: {}: {!s}".format(colornames[color],val))
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

    # TODO: Still contains a bug with trumps
    def show_trick(self,cards, round):
        '''Here we analyze the played cards, and try to conclude some information
        on the hands of the players'''
        color = cards[0].color
        p = cards[0].owner
        glory = glory_calculation(cards,self.trump)
        h = highest_card(cards, self.trump)
        points = card_points(cards)
        if self.player_is_playing(h.owner):
            self.points1 += points + glory
        else: self.points2 += points + glory

        self.remove_known_cards(cards)

        def remove_all_in_color(index, color, exceptions=[]):
            if index == self.index: return
            d = self.index_to_deck(index)
            for cc in  [a for a in d if (a.color == color and a.value not in exceptions)]:
                d.remove(cc)
            if not exceptions or not any(c in d.filter_color(color).values() for c in exceptions):
                i = (index-1-self.index)%4
                if color in self.unknown_colours[i]: self.unknown_colours[i].remove(color)
        
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
                    elif cards[0].value != JACK and p == self.partner:
                        self.pp("Mate started with non-high trump, so he probably wants it back")
                        self.flag_partner_started_with_trump = True
                    # if cards[0].value == KING:
                    #     if Card(QUEEN, self.trump) in d:
                    #         self.player_has_card(p, Card(QUEEN, self.trump))

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
                        
                    
        if self.index in (cards[0].owner,cards[1].owner) and highest_card(cards).owner == self.index: #we are playing and have won
            m = cards[2] if (cards[0].owner == self.index) else cards[3] # the card of your mate
            if m.color != color and m.color != self.trump: #mate didn't confess color and didn't trump
                if m.color in self.prefered_colors and abs(self.prefered_colors[m.color])>1: pass
                else:
                    if m.value in (SEVEN, EIGHT, NINE, ACE): #mate is signing
                        self.prefered_colors[m.color] = 2
                        self.pp("Mate signed card color")
                        if round < 6 and m.value == ACE:
                            if Card(TEN, m.color) in self.unknown_cards[1]:
                                self.unknown_cards[1].remove(Card(TEN,m.color))
                    elif m.value in (QUEEN, KING, TEN): #mate is de-signing the color
                        self.pp("Mate signed off card color")
                        self.prefered_colors[m.color] = -2
                        if round < 6 and m.value == TEN:
                            if Card(ACE, m.color) in self.unknown_cards[1]:
                                self.unknown_cards[1].remove(Card(ACE,m.color))
        if h.owner not in (self.index, self.partner) and h.owner in (cards[0].owner,cards[1].owner): # opponent won this round early
            m = cards[2] if (cards[0].owner == h.owner) else cards[3] # the card of its mate
            if m.color not in (color, self.trump): #mate didn't confess color and didn't trump
                if m.color not in self.prefered_colors: 
                    if m.value in (SEVEN, EIGHT, NINE, ACE): #mate is signing
                        self.prefered_colors[m.color] = -1
                        self.pp("Opponent signed card color")
                        if round < 6 and m.value == ACE:
                            if Card(TEN, m.color) in self.index_to_deck(m.owner):
                                self.index_to_deck(m.owner).remove(Card(TEN,m.color))
                    elif m.value in (QUEEN, KING, TEN): #mate is de-signing the color
                        self.pp("Opponent signed off card color")
                        self.prefered_colors[m.color] = 1
                        if round < 6 and m.value == TEN:
                            if Card(ACE, m.color) in self.index_to_deck(m.owner):
                                self.index_to_deck(m.owner).remove(Card(ACE,m.color))
                    
        if color == self.trump: #trump asked
            highest = cards[0]
            for c in cards[1:]:
                if c.color == self.trump:
                    if c > highest:
                        highest = c
                    else: #didn't overtrump, remove those possibilities
                        if c.owner == self.index: continue
                        d = self.index_to_deck(c.owner)
                        rem = [a for a in d if (a.color == self.trump and a > highest)]
                        if rem == d.filter_color(self.trump):
                            remove_all_in_color(c.owner, self.trump)
                        else:
                            for cc in rem:
                                d.remove(cc)
                else: #couldn't confess color
                    if c.owner == self.index: continue
                    remove_all_in_color(c.owner, self.trump)
        else: #not a trump asked
            highest = cards[0]
            for c in cards[1:]:
                if c.color in (highest.color, self.trump) and c>highest: highest = c
                if c.color != color: #couldn't confess color
                    if c.owner == self.index: continue
                    remove_all_in_color(c.owner, color)
                    if highest.owner != self.index_to_mate(c.owner):
                        if c.color != self.trump: #he didn't trump in
                            if highest.color != self.trump:
                                remove_all_in_color(c.owner, self.trump)
                            else:
                                d = self.index_to_deck(c.owner)
                                rem = [a for a in d if (a.color == self.trump and a > highest)]
                                if rem == d.filter_color(self.trump):
                                    remove_all_in_color(c.owner, self.trump)
                                else:
                                    for cc in rem:
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
            t = Card(TEN, color)
            if a in self.mystery_cards: #we haven't seen the ACE yet
                if a not in cards and cards[0].value!=TEN: #it is not played in this round
                    if self.trump not in Cards(cards).colors(): #not trumped in anywhere
                        pass
                        # self.pp("No Ace played in this round. How weird")
                        # if cards[0].owner != self.index:
                        #     d = self.index_to_deck(cards[0].owner)
                        #     if a in d: d.remove(a)
                        # if cards[2].owner != self.index:
                        #     d = self.index_to_deck(cards[2].owner)
                        #     if a in d: d.remove(a)
            for i in range(0,3):
                if cards[i] == a: #ACE has been played
                    
                    if i == 0 and cards[1] == t: remove_all_in_color(cards[1].owner, color)
                    j = 3 if i == 0 else i+1
                    if cards[j] == t and highest_card(cards,self.trump) == a: # check all the possibilities for why he would have trown a 10
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

        for i, c in enumerate(cards[1:]):
            if c.owner == self.index: continue
            if c.color != color and c.value in (TEN, ACE) and c != highest and self.index_to_mate(c.owner) != highest.owner:
                mate = (c.owner+1-self.index)%4
                if i == 2 or (mate!=3 and color not in self.unknown_colours[mate]) or (color not in self.cards.colors()):
                    self.pp("Person threw away valuable card to opponent, must not have lower cards to play")
                    for col in range(4):
                        if col == self.trump: continue
                        remove_all_in_color(c.owner, col, [TEN, ACE])
        
        # If the possible cards of a player exactly match how many cards they should have,
        # we remove those possibilities from other players
        for d in self.unknown_cards:
            if len(d) == len(self.cards):
                for c in d:
                    self.player_has_card(d.owner, c)

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

    def will_win_this_round(self, cards_played):
        """Returns whether we are absolutely certain to win this round,
        regardless of what we will play."""
        if not cards_played: return False
        h = highest_card(cards_played)
        if h.owner != self.partner: return False
        if len(cards_played) == 3: return True #Only us left to play
        color = cards_played[0].color
        is_trumped = h.color == self.trump
        notyetplayed = list(range(4))
        notyetplayed.remove(self.index)
        for c in cards_played: notyetplayed.remove(c.owner)
        # Since we are assuming that our partner is currently winning
        # And we are not last to play, there is exactly one other player that
        # needs to play a card
        p = notyetplayed[0]
        d = self.index_to_deck(p) # Possible cards in hand of the player
        if is_trumped: #winning card is trump
            if d.higher_then(h): return False # Person could overtrump
            else: return True
        if d.filter_color(self.trump): return False # Person could trump in
        if d.higher_then(h): return False
        return True



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
            cols = [c for c, val in self.prefered_colors.items() if val > 1]
            if not cols:
                cols = [c for c, val in self.prefered_colors.items() if val > 0]
            if not cols and len(self.prefered_colors) == 2: # two negative suggestions
                cols = [i for i in range(4) if i != self.trump and i not in self.prefered_colors]
            for color in cols:
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
            if self.unknown_cards[0].get_trumps():
                colors = list(range(4))
                for color in self.unknown_cards[0].colors(): colors.remove(color)
                for color in colors:
                    poss = sorted([c for c in non_trumps.filter_color(color) if c.value not in (TEN,ACE)])
                    if poss: 
                        self.pp("We try to draw out a trump from the opponent player")
                        return poss[0]
            self.pp("Can't play a signed color, and no TEN to free. Play something low and safe")
            filt = [c for c in non_trumps if not self.glory_possibility(c) and (c.color not in self.prefered_colors or self.prefered_colors[c.color]>0)]
            if not filt: #there is always a glory chance
                filt = [c for c in non_trumps if c.color not in self.prefered_colors or self.prefered_colors[c.color]>0]
                if not filt: filt = non_trumps
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
        self.pp("We play a high card")
        if high_cards.filter_value(TEN):
            return random.choice(high_cards.filter_value(TEN))
        if high_cards.filter_value(ACE):
            return random.choice(high_cards.filter_value(ACE))
        return random.choice(high_cards)

    def sign_mate(self):
        '''Pick a card to trow away at your mate (like he is going to win)'''
        self.pp("We pick a card to give to our mate")
        played_cards = self.played_cards
        for color in range(4):
            if color == self.trump: continue
            filt = self.cards.filter_color(color)
            if len(filt) == 1 and filt.has(TEN) and not self.is_high(Card(TEN,color)) and self.will_win_this_round(played_cards):
                self.pp("We play our naked 10 to our mate who is guaranteed to win this round.")
                if color not in self.signed_colors: self.signed_colors[color] = -1
                return filt.has(TEN)
        
        val = 0
        col = -1
        colors = list(range(4))
        colors.remove(self.trump)
        for c in self.signed_colors: colors.remove(c)

        for color in colors:
            filt = self.cards.filter_color(color)
            if filt.has(TEN):
                if len(filt) == 1:
                    if self.is_high(Card(TEN,color)):
                        if val < 1 and self.will_win_this_round(played_cards):
                            val = 0
                            col = color
                else:
                    if filt.has(ACE):
                        if len(filt) > 3: #We have A 10 x x
                            if self.will_win_this_round(played_cards):
                                val = 5
                                col = color
                        elif len(filt) == 3: #We have A 10 x
                            if filt.has(SEVEN) or filt.has(EIGHT) or filt.has(NINE):
                                if val < 4:
                                    val = 4
                                    col = color
                                else: #We have A 10 K/Q/J
                                    if self.will_win_this_round(played_cards):
                                        if val < 3:
                                            val = 3
                                            col = color
                            
                    else: #we have a card below the Ten
                        if self.will_win_this_round(played_cards):
                            if val < 1:
                                val = 1
                                col = color
            elif filt.has(ACE): # ACE but no TEN
                if filt.has(SEVEN) or filt.has(EIGHT) or filt.has(NINE):
                    if val < 3:
                        val = 3
                        col = color

        if val == 5:
            self.pp("We have the ace, a ten and two other of a color.")
            self.pp("We know we will win, so I can safely throw the Ace")
            self.signed_colors[col] = 2
            return self.cards.filter_color(col).has(ACE)
            
        elif val == 3 or val == 4:
            if val == 4: self.pp("We have the ace, a ten, and a small one of a color. Play the small one")
            elif val == 3: self.pp("Signal ACE, by playing small card")
            self.signed_colors[col] = 1
            if self.cards.filter_color(col).has(NINE):
                return self.cards.filter_color(col).has(NINE)
            elif self.cards.filter_color(col).has(EIGHT):
                return self.cards.filter_color(col).has(EIGHT)
            else:
                return self.cards.filter_color(col).has(SEVEN)
                
        elif val == 3:
            self.signed_colors[col] = 2
            self.pp("We have the ATK.")
            self.pp("We know we will win. I can safely play the ace") 
            return self.cards.filter_color(col).has(ACE)
            
        elif val > 0:
            self.signed_colors[col] = -2
            self.pp("We have a Ten.")
            self.pp("We know we will win. I can safely play the Ten")
            return self.cards.filter_color(col).has(TEN)
                
        self.pp("We can't signal on a color")
        for color in colors:
            filt = self.cards.filter_color(color)
            if len(filt) == 1 and len(self.mystery_cards.filter_color(color))>5 and filt[0].value in (JACK, QUEEN, KING):
                self.pp("Give glory sensitive solo card")
                self.signed_colors[color]=-1
                return filt[0]

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
        if aces and lowest.value in (SEVEN, EIGHT, NINE):
            self.signed_colors[lowest.color] = 1
            self.pp("We trow a low card to sign we have a Ace")
            return lowest

        self.pp("We can't signal an Ace. Play some points")
        for king in self.cards.filter_value(KING):
            if not king.is_trump and not self.is_high(king):
                return king
        for queen in self.cards.filter_value(QUEEN):
            if not queen.is_trump and not self.is_high(queen):
                return queen
        for jack in self.cards.filter_value(JACK):
            if not jack.is_trump and not self.is_high(jack):
                return jack
        self.pp("No points to trow away, trow away crap")
        return self.trow_away_card()
        
            
    def trow_away_card(self):
        '''Trow away a card, if you can't confess a card.'''
        #TODO: Watch out for making glory
        self.pp("We want to trow away a card")
        colors = self.cards.colors()
        if self.trump in colors: colors.remove(self.trump)
        if len(colors) == 1:
            self.pp("Trow away the lowest card we have of the only possible color")
            poss = sorted(self.cards.filter_color(colors[0]))
            c, glory = self.maxmin_glory(self.played_cards, deck=poss, maximize=False,color=colors[0])
            return c
        if len(colors) == 0:
            raise NotImplementedError("We only have trumps, shouldn't call this function")
        poss = Cards()
        for color in colors:
            filt = self.cards.filter_color(color)
            if len(filt) == 1 and filt[0].value not in (ACE, TEN, SEVEN) and len(self.mystery_cards.filter_color(color))>=6:
                self.pp("Trow away single glory sensitive card")
                return filt[0]
            # if len(filt) >= 4:
            #     self.pp("We trow away the lowest card of the color we have the most of")
            #     poss = sorted(filt)[:1] # look at lowest two cards
            #     c, glory = self.maxmin_glory(self.played_cards, deck=poss, maximize=False,color=color)
            #     return c
            if filt.has(TEN) and not self.is_high(filt.has(TEN)): continue
            filt = filt.filter(lambda c: c.value not in (TEN, ACE))
            poss.extend(filt)
        if poss:
            self.pp("Trowing away a low card in a colour that doesn't have a low TEN")
            c, glory = self.maxmin_glory(self.played_cards, deck=poss, maximize=False)
            return c
        self.pp("We have a Ten in every playable color. Play a card in one of them")
        poss = sorted(self.cards.filter(self.is_not_trump))[:2]
        c, glory = self.maxmin_glory(self.played_cards, deck=poss, maximize=False)
        return c
            

    def play_card(self, rnum, played_cards):
        '''This function is called by the game class. It should return
        the card that the AI is playing this round.'''
        played_cards = Cards(played_cards)
        self.played_cards = played_cards
        self.round = rnum
        legal = self.legal_cards(played_cards)
        if len(legal) == 1:
            self.pp("Only one legal card to play")
            return self.play_this_card(legal[0])
        if self.round >= 6 or (self.round == 5 and len(played_cards)>1):
            c = self.do_minmax()
            if c: return self.play_this_card(c)
        trumps = self.cards.get_trumps().sorted()
        high_trumps = trumps.filter(self.is_high)
        non_trumps = self.cards.filter(self.is_not_trump).sorted()
        if not played_cards:
            self.pp("We are playing this round")
            filt = Cards([c for c in high_trumps if self.glory_possibility(c)])
            if filt:
                self.pp("We have high trumps with a chance of glory")
                if KING in filt.values(): #king is high and there is glory possibility
                    return self.play_this_card(filt.has(KING))
                if NINE in filt.values():
                    return self.play_this_card(filt.has(NINE))
                return self.play_this_card(filt.sorted()[0])

            n = len(self.unknown_cards[0].get_trumps())
            m = len(self.unknown_cards[2].get_trumps())
            mate_trumps = len(self.unknown_cards[1].get_trumps())
            totaltrumps = len(self.mystery_cards.get_trumps())
            if n!=0 and m!=0 and totaltrumps>1 and trumps and not mate_trumps : #we want to trade 2 for 1
                if len(trumps)>1 or not trumps.has(NINE): # More than one trump, or otherwise we have something lower than the nine
                    
                    if high_trumps: 
                        self.pp("Mate doesn't have trump, so we try to draw out 2 trumps of the opponent")
                        return self.play_this_card(high_trumps[0])
                    options = [c for c in trumps if not self.glory_possibility(c) and c.value not in (ACE, TEN, NINE)]
                    if options: 
                        self.pp("Mate doesn't have trump, so we try to draw out 2 trumps of the opponent")
                        return self.play_this_card(sorted(options)[0])
                    #else: return self.play_this_card(sorted(trumps)[0])
                    
            if self.is_playing:
                self.pp("We are playing this game")
                if n + m != 0:
                    if high_trumps and (len(trumps)>1 or not mate_trumps):
                        self.pp("The other team might still have trumps")
                        return self.play_this_card(high_trumps[0])
                    if len(trumps) > 1:
                        filt = [c for c in trumps if not self.glory_possibility(c) and c.value!=NINE]
                        if filt:
                            self.pp("Don't have high trump, play low one with no chance of glory")
                            return self.play_this_card(sorted(filt)[0])
                        self.pp("Don't have high trump, play lowest trump and hope for the best")
                        return self.play_this_card(sorted(trumps)[0])
                    if trumps and self.flag_partner_started_with_trump:
                        self.flag_partner_started_with_trump = False
                        self.pp("Mate started out with non-JACK trump, play trump back to him")
                        poss = [c for c in trumps if self.glory_possibility(c)]
                        if poss: return self.play_this_card(poss[0])
                        else: return self.play_this_card(sorted(trumps)[0])
                    if trumps:
                        self.pp("No good trump play, playing non-trump")
                    else: self.pp("We have no trumps")
                    return self.play_this_card(self.pick_non_trump())
                self.pp("Other team doesn't have trumps, so play non trump")
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
            #if len(possibilities) == 1: #only 1 possible card to play, possibility taken care of in the beginning
            #    self.pp("Only one possible card to play")
            #    return self.play_this_card(possibilities[0])
            if not possibilities:
                self.pp("Can't confess color")
                if trumps:
                    opponent_trumps = max((len(self.unknown_cards[0].get_trumps()),
                                           len(self.unknown_cards[2].get_trumps())))
                    if opponent_trumps < len(high_trumps):
                        high_non_trumps = non_trumps.filter(self.is_high)
                        if (non_trumps == high_non_trumps or
                            (not self.will_win_this_round(played_cards) and high_non_trumps and len(high_trumps)>1)):
                            if non_trumps == high_non_trumps: self.pp("We pretrump because we only have high cards left")
                            else: self.pp("We pretrump because we might lose this round, and we still have some high cards")
                            options = [c for c in high_trumps if not self.glory_possibility(c)]
                            if options: return self.play_this_card(options[0])
                            if len(high_trumps) > 1:
                                if Card(KING, self.trump) in high_trumps:
                                    high_trumps.remove(Card(KING,self.trump))
                            return self.play_this_card(high_trumps[0])
                    if winning:
                        self.pp("Our mate is winning, don't trump in")
                        if non_trumps:
                            if self.is_high(highest) or self.will_win_this_round(played_cards):
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
                        if len(played_cards) == 3: high_cards = filt
                        if high_cards and self.is_playing:
                            self.pp("We play a high trump, maximizing glory possibility")
                            c, glory = self.maxmin_glory(played_cards, deck=high_cards)
                            return self.play_this_card(c)
                        if JACK in filt.values():
                            filt.remove(Card(JACK, self.trump))
                        self.pp("We play a card that minimizes glory")
                        c, glory = self.maxmin_glory(played_cards, deck=filt, maximize=False)
                        return self.play_this_card(c)

                    if winning and self.is_high(highest):
                        if NINE not in trumps.values() or ACE in trumps.values(): 
                            c, glory = self.maxmin_glory(played_cards)
                        else:
                            c, glory = self.maxmin_glory(played_cards, deck=[a for a in trumps if a.value!=NINE])
                        return self.play_this_card(c)
                    if ACE not in trumps.values():
                        c, glory = self.maxmin_glory(played_cards,
                                                     deck=[a for a in trumps if a.value!=NINE], maximize=False)
                    else:
                        c, glory = self.maxmin_glory(played_cards,
                                                     deck=trumps, maximize=False)
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
                            self.pp("we can win with a card")
                            c, glory = self.maxmin_glory(played_cards, deck=filt)
                            if glory:
                                self.pp("And we can make glory! do it")
                                return self.play_this_card(c)
                            return self.play_this_card(filt.sorted()[0])
                        else:
                            self.pp("we can't win, play a low card")
                            #TODO: make exceptions
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
                        
                        if len(played_cards) == 1:
                            if possibilities.has(TEN): possibilities.remove(Card(TEN, played_cards[0].color))
                        if len(played_cards) == 2 and possibilities.has(TEN):
                            no_glory = Cards([c for c in possibilities if not glory_calculation(played_cards+[c],self.trump)])
                            if no_glory.has(TEN):
                                if len(no_glory) == 1:
                                    self.pp("Only way to dodge glory is trowing away our TEN")
                                    return self.play_this_card(no_glory.has(TEN))
                                no_glory.remove(Card(TEN, played_cards[0].color))
                            if no_glory:
                                possibilities = no_glory
                            else: # Glory any case, let the optimizer decide
                                pass
                        self.pp("we can't win, play a low card")
                        c, glory = self.maxmin_glory(played_cards, maximize=False, deck=possibilities)
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


    def do_minmax(self, amount=None):
        self.pp("Minmaxing")
        options = {c:list() for c in self.legal_cards(self.played_cards)}
        self.remove_known_cards(self.played_cards)
        if self.round < 6:
            maxcount = 100//len(options) if not amount else amount
        else:
            maxcount = 200//len(options) if not amount else amount
        distributions = []
        count = 0 
        for i,d in enumerate(self.generate_all_distributions(self.round, self.played_cards)):
            distributions.append(d)
            count += 1
            if count>500: break
        if count == 0:
            self.pp("No valid distributions")
            return None
        #if count>500:
        if count>maxcount:
            self.pp("Too many distributions, picking randomly")
            distributions = [self.generate_distribution(self.round,self.played_cards) for i in range(maxcount)]
        # elif count>maxcount:
        #     self.pp("{!s} distributions, taking a subset".format(count))
        #     skipvalue = (count-1)//maxcount + 1
        #     distributions = [d for i,d in enumerate(distributions) if i%skipvalue == 0]
        else:
            self.pp("Evaluating {!s} possibilities".format(count))
        
        players = []
        p = DummyPlayer(self.index, self.is_playing, self.trump, Cards(self.cards))
        players.append(p)
        for i in range(3):
            index = (self.index+i+1)%4
            p = DummyPlayer(index, self.player_is_playing(index), self.trump, Cards())
            players.append(p)
        players.sort(key=lambda p: p.index)
        for hands in distributions:
            for i,hand in enumerate(hands):
                players[(self.index+i+1)%4].cards = Cards(hand)
            m = MinMaxer(players, self.trump, self.points1, self.points2, 
                         self.index, self.round, Cards(self.played_cards))
            for c in options:
                m2 = m.copy()
                m2.progress_game(c)
                points1, points2 = m2.do_minmax()
                points = points1 - points2 if self.is_playing else points2 - points1
                options[c].append(points)

        scores = {}
        best_score = -500
        for c,l in options.items():
            avg = sum(l)/len(l)
            self.pp("Minmax: {} has average score of {:.2f}".format(c.pretty(),avg))
            if avg > best_score:
                best_score = avg
            scores[c] = avg
        filt = Cards([c for c, score in scores.items() if score>best_score-1.0])
        if len(filt) == 1: return filt[0]
        filt2 = filt.filter(lambda c: not self.is_high(c))
        if filt2: return filt2[0]
        return filt.sorted()[0]


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

    def maxmin_glory(self, cards, maximize = True, deck=None, color=None):
        baseglory = glory_calculation(cards, self.trump)
        c, glory = self.maxmin_glory_prime(cards, maximize, deck,color)
        if glory-baseglory != 0:
            self.pp("Glory calculation: {0:.1f}".format(glory-baseglory))
        return (c, glory)
    def maxmin_glory_prime(self, cards_played, maximize = True, deck=None, color=None):
        '''Returns the card in deck that maximizes glory, and gives the expected glory.
        If maximize is False then it minimizes glory.'''
        cards = cards_played
        mult = 1
        if maximize == False: mult = -1
        if not color:
            if not cards:
                color = deck[0].color
            else: color = cards[0].color
        if deck==None:
            poss = self.cards.filter_color(color)
        else:
            poss = deck

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
            for c in poss:
                other = self.unknown_cards[0].filter_color(c.color) # the cards of the next player
                if not other: other = self.unknown_cards[0].filter_color(cards[0].color)
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
            other2 = self.unknown_cards[1].filter_color(cards[0].color)
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
        if len(cards) == 0:
            raise Exception("Shouldn't call this function when played_cards is empty")



class DummyPlayer(object):
    def __init__(self, index, is_playing, trump, cards):
        self.index = index
        self.partner = (index+2)%4
        self.is_playing = is_playing
        self.trump = trump
        self.cards = cards

    def copy(self):
        return DummyPlayer(self.index, self.is_playing, self.trump, Cards(self.cards))

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



class MinMaxer(object):
    def __init__(self, players, trump, points1, points2, currentplayer, round, played_cards):
        self.players = players
        self.round = round
        self.played_cards = played_cards
        self.currentplayer = currentplayer
        self.trump = trump
        self.points1 = points1
        self.points2 = points2

    def copy(self):
        players = [p.copy() for p in self.players]
        return MinMaxer(players, self.trump, self.points1, self.points2, 
                        self.currentplayer, self.round, Cards(self.played_cards))

    def progress_game(self,c):
        self.players[self.currentplayer].cards.remove(c)
        self.played_cards.append(c)
        if len(self.played_cards) != 4:
            self.currentplayer = (self.currentplayer + 1)%4
            return
        cards = self.played_cards
        h = highest_card(cards,self.trump)
        winner = h.owner 
        points = card_points(cards, self.trump)
        glory = glory_calculation(cards, self.trump)
        if self.players[winner].is_playing: 
            self.points1 += points + glory
            if self.round == 8: self.points1 += 10
        else: 
            self.points2 += points + glory
            if self.round == 8: self.points2 += 10
        
        if self.round == 8:
            if self.points1 == 0:
                self.points2 += 100
            if self.points2 == 0:
                self.points1 += 100
            if self.points1 < self.points2: #Nat
                self.points2 += self.points1
                self.points1 = 0


        self.currentplayer = winner
        self.round += 1
        self.played_cards = Cards()

    def do_minmax(self):
        while True:
            p = self.players[self.currentplayer]
            options = p.legal_cards(self.played_cards)
            #print(self.round, self.currentplayer, options, [len(p.cards) for p in self.players])
            if len(options) == 1:
                self.progress_game(options[0])
            else:
                break
            if self.round > 8:
                return self.points1, self.points2

        #best_card = None
        best_score = -500
        p1, p2 = 0, 0
        for c in options:
            m = self.copy()
            #print("Going deeper")
            #print(self.round, self.currentplayer, [len(p.cards) for p in m.players])
            m.progress_game(c)
            points1, points2 = m.do_minmax()
            if p.is_playing: points = points1 - points2
            else: points = points2 - points1
            if points > best_score:
                best_score = points
                #best_card = c
                p1 = points1
                p2 = points2

        return p1, p2




