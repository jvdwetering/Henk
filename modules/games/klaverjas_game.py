import random

import telepot

from .base import BaseGame
from .cards import *
from .klaverjas_ai import BasePlayer, AI

KLAVERJASSEN = 100

class Klaverjas(BaseGame):
    game_type = KLAVERJASSEN
    def __init__(self, bot, game_id, players,date):
        super().__init__(bot, game_id, players,date)
        self.real_players = []
        for user_id,user_name in players:
            p = RealPlayer(self, user_id,user_name, len(self.real_players))
            self.real_players.append(p)

        self.deck = None
        self.players = self.real_players.copy()
        for i in range(len(self.real_players),4):
            p = AI(i)
            self.players.append(p)

        self.initialize()
        
    def give_cards(self):
        self.deck = create_deck()
        random.shuffle(self.deck)
        for i in range(4):
            self.players[i].give_cards(Cards([self.deck[i*8+j] for j in range(8)]))

    def initialize(self):
        self.round = 1
        self.cards_this_round = Cards()
        self.cards_previous_round = Cards()
        self.currentplayer = 0
        self.startingplayer= 0
        self.status_messages = []
        self.p1, self.p2, self.p3, self.p4 = self.players
        self.p1.set_partner(self.p3.index)
        self.p3.set_partner(self.p1.index)
        self.p2.set_partner(self.p4.index)
        self.p4.set_partner(self.p2.index)
        self.p1.is_playing = True
        self.p3.is_playing = True
        self.points1 = 0
        self.points2 = 0

        self.give_cards()
        if isinstance(self.players[0],RealPlayer):
            self.current_users = [self.players[0].user_id]
            self.message_pick_trump(self.players[0])
            #self.players[0].pick_trump()
            return
        self.trump = self.players[0].pick_trump()
        [self.players[i].set_trump(self.trump) for i in range(4)]
        self.progress_game()


    def _trump_set(self,ident, button_id):
        self.trump = button_id
        [self.players[i].set_trump(self.trump) for i in range(4)]
        self.disable_keyboard(ident)
        self.progress_game()
    def message_pick_trump(self, player):
        msg = player.hand_string() + "\nKies troef"
        self.send_keyboard_message(player.user_id, msg, [suit_to_unicode[i] for i in range(4)], self._trump_set)
        self.save_game_state()
    

    def _card_picked(self,ident, button_id):
        self.cards_this_round.append(self.playable_cards[button_id])
        p = self.players[self.currentplayer]
        p.cards.remove(self.playable_cards[button_id])
        if isinstance(p, RealPlayer):
            p.send_hand_message()
        self.disable_keyboard(ident)
        self.currentplayer = (self.currentplayer+1)%4
        if self.currentplayer == self.startingplayer:
            self.process_round()
        self.progress_game()
    def message_play_card(self, player):
        self.playable_cards = player.legal_cards(self.cards_this_round)
        buttons = [card.pretty() for card in self.playable_cards]
        self.send_keyboard_message(player.user_id, "Kies een kaart", buttons, self._card_picked)
        self.save_game_state()

    def update_status_message(self):
        if self.cards_previous_round:
            msg = "Vorige ronde: \n"
            for i in range(4):
                msg += "{}: {}\n".format(self.players[self.cards_previous_round[i].owner].name,
                                         self.cards_previous_round[i].pretty())
            winner = highest_card(self.cards_previous_round,self.trump).owner
            msg += "{} had gewonnen\n \n".format(self.players[winner].name)
        else: msg = ""
        msg += "Ronde {!s}\n".format(self.round)
        count = len(self.cards_this_round)
        for i in range(count):
            msg += "{}: {}\n".format(self.players[(self.startingplayer+i)%4].name, self.cards_this_round[i].pretty())
        if count != 4:
            i = count
            msg += "{}: Bezig met kiezen\n".format(self.players[(self.startingplayer+i)%4].name)
            for i in range(count+1, 4):
                msg += "{}: \n".format(self.players[(self.startingplayer+i)%4].name)
        else:
            msg += "\n" + self.endroundtext

        if not self.status_messages:
            for p in self.real_players:
                sent = self.bot.telebot.sendMessage(p.user_id, msg)
                ident = telepot.message_identifier(sent)
                self.status_messages.append(ident)
        else:
            for ident in self.status_messages:
                editor = telepot.helper.Editor(self.bot.telebot, ident)
                editor.editMessageText(msg)

    def process_round(self):
        cards = self.cards_this_round
        h = highest_card(cards,self.trump)
        winner = h.owner  #need to correct because index starts at 1
        points = card_points(cards, self.trump)
        glory = glory_calculation(cards, self.trump)
        msg = "" #"Ronde {!s}:\n".format(self.round)
        if glory > 0:
            msg += "Roem! {!s} punten\n".format(glory)
        msg += "{} heeft gewonnen met een {}".format(self.players[winner].name, h.pretty())
        #self.send_user_message(msg)
        if winner == 0 or winner == 2:
            self.points1 += points + glory
            if self.round == 8: self.points1 += 10
        else:
            self.points2 += points + glory
            if self.round == 8: self.points2 += 10
        for p in self.players:
            p.show_trick(cards, self.round)

        self.endroundtext = msg
        self.update_status_message()

        self.startingplayer = winner
        self.currentplayer = winner
        self.cards_previous_round = self.cards_this_round
        self.cards_this_round = Cards()
        #self.status_messages = []

        if self.round == 8: #end of game
            msg = "Potje is afgelopen. \nTeam 1: {!s} punten\nTeam 2: {!s} punten\n".format(self.points1,self.points2)
            if self.points1 < self.points2:
                msg += "Team 1 is nat"
            self.send_user_message(msg)
            self.is_active = False
            self.save_game_state()
        
        self.round += 1
        

    def progress_game(self):
        '''When the cards have been dealt and trump has been chosen, tries to progress the game
        until it hits a point where user input is required.'''
        while self.round<=8:
            if isinstance(self.players[self.currentplayer],RealPlayer):
                self.update_status_message()
                self.message_play_card(self.players[self.currentplayer])
                return

            self.cards_this_round.append(self.players[self.currentplayer].play_card(self.round, self.cards_this_round.copy()))
            self.currentplayer = (self.currentplayer+1)%4
            if self.currentplayer == self.startingplayer:
                self.process_round()
            




class RealPlayer(BasePlayer):
    def __init__(self, game, user_id, name, index):
        super().__init__(index)
        self.game = game
        self.user_id = user_id
        self.name = name
        self.hand_message_id = None

    def send_message(self, msg):
        self.game.send_user_message(msg, self.user_id)

    def hand_string(self):
        s= ""
        for color in range(4):
            s += suit_to_unicode[color] + " " + ", ".join([short_valuenames[v] for v in self.cards.filter_color(color).values()]) + "\n"
        return s.strip()

    def set_partner(self, i):
        pass

    def give_cards(self, cards):
        super().give_cards(cards)
        #self.send_message(self.hand_string())

    def send_hand_message(self):
        msg = "Troef is " + suit_to_unicode[self.trump] + "\n" + self.hand_string()
        if not self.hand_message_id:
            sent = self.game.bot.telebot.sendMessage(self.user_id, msg)
            self.hand_message_id = telepot.message_identifier(sent)
        else:
            editor = telepot.helper.Editor(self.game.bot.telebot, self.hand_message_id)
            editor.editMessageText(msg)
    
    def set_trump(self, trump):
        super().set_trump(trump)
        self.send_hand_message()