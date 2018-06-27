import random

import telepot

from .base import BaseGame, BaseDispatcher
from .cards import *
from .klaverjas_ai import BasePlayer, AI

KLAVERJASSEN = 100

class Klaverjas(BaseGame):
    game_type = KLAVERJASSEN
    def __init__(self, bot, game_id, players,date, cmd):
        super().__init__(bot, game_id, players,date, cmd)
        self.real_players = []
        for user_id,user_name in players:
            p = RealPlayer(self, user_id,user_name, len(self.real_players))
            self.real_players.append(p)

        self.deck = None
        self.players = self.real_players.copy()
        for i in range(len(self.real_players),4):
            p = AI(i)
            self.players.append(p)

        self.callbacks_disposed = []

        self.initialize()
        
    def give_cards(self):
        self.deck = create_deck()
        if self.cmd: 
            r = random.Random()
            r.seed(self.cmd)
            r.shuffle(self.deck)
        else: random.shuffle(self.deck)
        for i in range(4):
            self.players[i].give_cards(Cards([self.deck[i*8+j] for j in range(8)]))

    def initialize(self):
        self.round = 1
        self.cards_this_round = Cards()
        self.cards_previous_round = Cards()
        self.glory = -1
        self.glory_previous_round = -1
        self.currentplayer = 0
        self.startingplayer= 0
        self.status_messages = []
        self.endroundtext = ""
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
        msg = "Team 1: {}, {}\n".format(self.p1.name, self.p3.name)
        msg += "Team 2: {}, {}\n".format(self.p2.name, self.p4.name)
        for p in self.real_players:
            p.send_message(msg+p.hand_string())

        if isinstance(self.players[0],RealPlayer):
            self.current_users = [self.players[0].user_id]
            self.message_pick_trump(self.players[0])
            #self.players[0].pick_trump()
            return
        self.trump = self.players[0].pick_trump()
        [self.players[i].set_trump(self.trump) for i in range(4)]
        self.progress_game()


    def _trump_set(self,ident, button_id, user):
        if ident in self.callbacks_disposed: return
        self.callbacks_disposed.append(ident)
        self.trump = button_id
        [self.players[i].set_trump(self.trump) for i in range(4)]
        self.disable_keyboard(ident)
        self.progress_game()
    def message_pick_trump(self, player):
        msg = player.hand_string() + "\nKies troef"
        self.send_keyboard_message(player.user_id, msg, [suit_to_unicode[i] for i in range(4)], self._trump_set)
        self.save_game_state()
    

    def _card_picked(self,ident, button_id, user):
        if ident in self.callbacks_disposed: return
        self.callbacks_disposed.append(ident)
        self.cards_this_round.append(self.playable_cards[button_id])
        p = self.players[self.currentplayer]
        p.cards.remove(self.playable_cards[button_id])
        if isinstance(p, RealPlayer):
            p.send_hand_message()
        self.disable_keyboard(ident)
        self.currentplayer = (self.currentplayer+1)%4
        if self.currentplayer == self.startingplayer:
            self.process_round(progress_game=True)
        else: self.progress_game()
    def message_play_card(self, player):
        self.playable_cards = player.legal_cards(self.cards_this_round)
        buttons = [card.pretty() for card in self.playable_cards]
        self.send_keyboard_message(player.user_id, "Kies een kaart", buttons, self._card_picked)
        self.save_game_state()

    def update_status_message(self):
        if self.cards_previous_round:
            msg = "Vorige ronde: \n"
            for i in range(4):
                p = self.players[self.cards_previous_round[i].owner]
                if p.index%2 == 0: msg += "*"
                msg += "{}: {}\n".format(p.name, self.cards_previous_round[i].pretty())
            winner = highest_card(self.cards_previous_round,self.trump).owner
            #glory = glory_calculation(self.cards_previous_round, self.trump)
            if self.glory_previous_round > 0: 
                msg += "Roem! {!s} punten\n".format(self.glory_previous_round)
            msg += "{} heeft gewonnen\n \n".format(self.players[winner].name)
        else: msg = ""
        msg += "Ronde {!s}\n".format(self.round)
        count = len(self.cards_this_round)
        for i in range(count):
            p = self.players[(self.startingplayer+i)%4]
            if p.index%2 == 0: msg += "*"
            msg += "{}: {}\n".format(p.name, self.cards_this_round[i].pretty())
        if count != 4:
            i = count
            p = self.players[(self.startingplayer+i)%4]
            if p.index%2 == 0: msg += "*"
            msg += "{}: Bezig met kiezen\n".format(p.name)
            for i in range(count+1, 4):
                p = self.players[(self.startingplayer+i)%4]
                if p.index%2 == 0: msg += "*"
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



    def _accept_glory(self,ident, button_id, user):
        if ident in self.callbacks_disposed: return
        self.callbacks_disposed.append(ident)
        if button_id == 1:
            self.glory == 0
        else:
            self.glory = glory_calculation(self.cards_this_round, self.trump)
        self.disable_keyboard(ident)
        self.process_round(progress_game=True)
    def message_accept_glory(self, player, glory_amount):
        buttons = ["ja", "nee"]
        self.send_keyboard_message(player.user_id, "{!s} roem. Kloppen?".format(glory_amount), buttons, self._accept_glory)
        self.save_game_state()

    def process_round(self, progress_game=False):
        cards = self.cards_this_round
        h = highest_card(cards,self.trump)
        winner = h.owner 
        points = card_points(cards, self.trump)
        
        msg = "{} heeft gewonnen met een {}".format(self.players[winner].name, h.pretty())
        self.endroundtext = msg

        if self.glory == -1:
            glory = glory_calculation(cards, self.trump)
            if glory == 0 or not isinstance(self.players[winner], RealPlayer):
                self.glory = glory
            else:
                self.update_status_message()
                self.message_accept_glory(self.players[winner], glory)
                return
        if self.glory>0:
            msg += "Roem! {!s} punten\n".format(self.glory)
        
        if winner == 0 or winner == 2:
            self.points1 += points + self.glory
            if self.round == 8: self.points1 += 10
        else:
            self.points2 += points + self.glory
            if self.round == 8: self.points2 += 10
        for p in self.players:
            p.show_trick(cards, self.round)

        self.endroundtext = msg
        self.update_status_message()

        self.startingplayer = winner
        self.currentplayer = winner
        self.cards_previous_round = self.cards_this_round
        self.cards_this_round = Cards()
        self.glory_previous_round = self.glory
        self.glory = -1

        if self.round == 8: #end of game
            msg = "Potje is afgelopen. \nTeam 1: {!s} punten\nTeam 2: {!s} punten\n".format(self.points1,self.points2)
            if self.points1 < self.points2:
                msg += "Team 1 is nat"
            self.send_user_message(msg)
            self.is_active = False
            self.save_game_state()
        
        self.round += 1

        if progress_game:
            self.progress_game()
        

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
                self.process_round(progress_game=True)
                return
            


class KlaverjasDispatcher(BaseDispatcher):
    welcome = "Klaverjassen! Wie doet er mee?"
    buttons = ["join/unjoin", "start"]
    maxplayers = 4
    def __init__(self, bot, game_id, msg):
        super().__init__(bot, game_id, msg)
        self.players = [(self.sender_id,self.sender_name)]

    def message_init(self):
        txt = self.welcome+"\n*" + self.sender_name
        self.ident = self.send_keyboard_message(self.chat_id, txt, self.buttons, self.callback)

    def callback(self, ident, button_id, s):
        sender, sendername = s
        if not self.is_active: return
        if button_id == 0: #join/unjoin
            if self.players.count((sender,sendername)):
                self.players.remove((sender,sendername))
            else:
                if len(self.players) == self.maxplayers:
                    return "Het spel zit al vol"
                self.players.append((sender,sendername))
            self.update_message()
        elif button_id == 1: #start game
            if not self.players:
                return "Er moet wel iemand meedoen"
            if sender != self.sender_id:
                return "Alleen {} kan dit potje beginnen".format(self.sender_name)
            index = len(self.bot.dataManager.games)
            self.is_active = False
            g = Klaverjas(self.bot,index,self.players,self.date, self.cmd)
            self.bot.games[index] = g
            editor = telepot.helper.Editor(self.bot.telebot, self.ident)
            editor.editMessageReplyMarkup()

    def update_message(self):
        msg = self.welcome +"\n" +"\n".join("* "+n for i,n in self.players)
        editor = telepot.helper.Editor(self.bot.telebot, self.ident)
        editor.editMessageText(msg, reply_markup=self.get_keyboard(self.buttons,index=0))


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