import random
import string
from collections import OrderedDict

import telepot

from .base import BaseGame, BaseDispatcher
from .cards import *
from .klaverjas_ai import BasePlayer, AI

KLAVERJASSEN = 100
KLAVERJASSEN_DISPATCH = 101
KLAVERJASSEN_CHALLENGE = 102

#seed for potje met roem op eerste slag: ulonrloyfp

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
        self.save_game_state()
        
    def give_cards(self):
        self.deck = create_deck()
        if self.cmd: self.seed = self.cmd
        else:
            self.seed = ''.join(random.choice(string.ascii_lowercase) for _ in range(10))
        r = random.Random()
        r.seed(self.seed)
        r.shuffle(self.deck)
        for i in range(4):
            self.players[i].give_cards(Cards([self.deck[i*8+j] for j in range(8)]))

    def initialize(self):
        self.round = 1
        self.cards_this_round = Cards()
        self.cards_previous_round = Cards()
        self.round_lists = []
        self.glory_lists = []
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
        self.pointsglory1 = 0
        self.pointsglory2 = 0

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
        return "Troef gekozen"
    def message_pick_trump(self, player):
        msg = player.hand_string() + "\nKies troef"
        self.send_keyboard_message(player.user_id, msg, ["  {}  ".format(suit_to_unicode[i]) for i in range(4)], self._trump_set)
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
        return "Kaart gekozen"

    def message_play_card(self, player):
        legal = Cards(player.legal_cards(self.cards_this_round))
        self.playable_cards = legal.get_trumps().sorted(reverse=True)
        suits = list(range(4))
        suits.remove(self.trump)
        for col in suits:
            self.playable_cards.extend(legal.filter_color(col).sorted(reverse=True))
        buttons = [card.pretty() for card in self.playable_cards]
        self.send_keyboard_message(player.user_id, "Kies een kaart", buttons, self._card_picked)
        self.save_game_state()

    def update_status_message(self):
        if self.cards_previous_round:
            msg = "Vorige ronde: \n"
            msg += "{} is begonnen\n".format(self.players[self.cards_previous_round[0].owner].name)
            index_to_card = {}
            for c in self.cards_previous_round:
                index_to_card[c.owner] = c.pretty()
            msg += "```\n{}\n".format(self.p3.name.rjust(12))
            msg += index_to_card[self.p3.index].rjust(10) + "\n"
            msg += self.p2.name.ljust(12) + self.p4.name.rjust(10) + "    \n"
            msg += index_to_card[self.p2.index].center(4).ljust(12)
            msg += index_to_card[self.p4.index].center(len(self.p4.name)-1).rjust(6)
            msg += "\n" + self.p1.name.rjust(12) + "\n"
            msg += index_to_card[self.p1.index].rjust(10) + "\n"
            msg += "\n```"
            # for i in range(4):
            #     p = self.players[self.cards_previous_round[i].owner]
            #     if p.index%2 == 0: msg += "*"
            #     msg += "{}: {}\n".format(p.name, self.cards_previous_round[i].pretty())
            #     if p.index%2 == 0: msg += "*"
            winner = highest_card(self.cards_previous_round,self.trump).owner
            #glory = glory_calculation(self.cards_previous_round, self.trump)
            if self.glory_previous_round > 0: 
                msg += "Roem! {!s} punten\n".format(self.glory_previous_round)
            msg += "{} heeft gewonnen\n \n".format(self.players[winner].name)
        else: msg = ""
        msg += "Ronde {!s}\n".format(self.round)
        
        count = len(self.cards_this_round)
        index_to_card = {}
        for c in self.cards_this_round:
            index_to_card[c.owner] = c.pretty()
        if count != 4:
            index_to_card[self.currentplayer] = "  ..."
        msg += "```\n{}\n".format(self.p3.name.rjust(12))
        if self.p3.index in index_to_card:
            msg += index_to_card[self.p3.index].rjust(10) + "\n"
        else:
            msg += "\n"
        msg += self.p2.name.ljust(12) + self.p4.name.rjust(10) + "       \n"
        if self.p2.index in index_to_card:
            msg += index_to_card[self.p2.index].center(4).ljust(12)
        else: msg += " "*13
        if self.p4.index in index_to_card:
            msg += index_to_card[self.p4.index].center(len(self.p4.name)-1).rjust(6)
        else: msg += " "*12
        msg += "\n" + self.p1.name.rjust(12) + "\n"
        if self.p1.index in index_to_card:
            msg += index_to_card[self.p1.index].rjust(10) + "\n"
        msg += "\n```"
        if count == 4:
            msg += self.endroundtext
            if self.glory == -1: msg += " "

        
        # for i in range(count):
        #     p = self.players[(self.startingplayer+i)%4]
        #     if p.index%2 == 0: msg += "*"
        #     msg += "{}: {}\n".format(p.name, self.cards_this_round[i].pretty())
        # if count != 4:
        #     i = count
        #     p = self.players[(self.startingplayer+i)%4]
        #     if p.index%2 == 0: msg += "*"
        #     msg += "{}: Bezig met kiezen\n".format(p.name)
        #     for i in range(count+1, 4):
        #         p = self.players[(self.startingplayer+i)%4]
        #         if p.index%2 == 0: msg += "*"
        #         msg += "{}: \n".format(self.players[(self.startingplayer+i)%4].name)
        # else:
        #     msg += "\n" + self.endroundtext
        #     if self.glory == -1: msg += " "

        if not self.status_messages:
            for p in self.real_players:
                sent = self.bot.telebot.sendMessage(p.user_id, msg, parse_mode="Markdown")
                ident = telepot.message_identifier(sent)
                self.status_messages.append(ident)
        else:
            for ident in self.status_messages:
                editor = telepot.helper.Editor(self.bot.telebot, ident)
                try:
                    editor.editMessageText(msg, parse_mode="Markdown")
                except telepot.exception.TelegramError:
                    pass


    def _accept_glory(self,ident, button_id, user):
        if ident in self.callbacks_disposed: return
        self.callbacks_disposed.append(ident)
        if button_id == 1:
            self.glory = 0
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
            msg += "\nRoem! {!s} punten\n".format(self.glory)
        
        if winner == 0 or winner == 2:
            self.points1 += points + self.glory
            self.pointsglory1 += self.glory
            if self.round == 8: self.points1 += 10
        else:
            self.points2 += points + self.glory
            self.pointsglory2 += self.glory
            if self.round == 8: self.points2 += 10
        for p in self.players:
            p.show_trick(cards, self.round)

        self.endroundtext = msg
        self.update_status_message()

        self.startingplayer = winner
        self.currentplayer = winner
        self.round_lists.append(self.cards_this_round)
        self.glory_lists.append(self.glory)
        self.cards_previous_round = self.cards_this_round
        self.cards_this_round = Cards()
        self.glory_previous_round = self.glory
        self.glory = -1


        if self.round == 8: #end of game
            if self.points1 == 0: 
                self.points2 += 100
                self.pointsglory2 += 100
            if self.points2 == 0: 
                self.points1 += 100
                self.pointsglory1 += 100

            # msg = "Potje is afgelopen. \nTeam 1: {!s} punten\nTeam 2: {!s} punten\n".format(self.points1,self.points2)
            # if self.points1 <= self.points2:
            #     msg += "Team 1 is nat\n"
            # if self.points1 == 0 or self.points2 == 0:
            #     msg += "Pit!\n"
            msg = self.game_end_message()
            self.send_user_message(msg, parse_mode="Markdown")
            #for i in self.player_names: self.bot.telebot.sendMessage(i, msg, parse_mode="Markdown")
            self.game_ended()
            self.save_game_state()
            return
        
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
    
    def game_end_message(self):
        msg = "Klaverjas potje met seed {}\n".format(self.seed)
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

        for k,cards in enumerate(self.round_lists):
            #msg += "Ronde {!s}:\n".format(k+1)
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
            #msg += "{} wint de slag met een {}".format(self.players[h.owner].name, h.pretty()) + "\n"
            if self.glory_lists[k]:
                msg += "{!s} roem geklopt".format(self.glory_lists[k]) + "\n"
            msg += "\n"
        msg = "\n".join(s.strip() for s in msg.splitlines())
        return msg

    def summarize(self):
        msg = "{} ".format(suit_to_unicode[self.trump])
        if self.pointsglory1: msg += "({!s}) {!s} - ".format(self.pointsglory1, self.points1)
        else: msg += "{!s} - ".format(self.points1)
        if self.pointsglory2: msg += "{!s} ({!s})".format(self.points2,self.pointsglory2)
        else: msg += "{!s}".format(self.points2)
        return msg


class KlaverjasDispatcher(BaseDispatcher):
    game_type = KLAVERJASSEN_DISPATCH
    welcome = "Klaverjassen! Wie doet er mee?"
    buttons = ["join/unjoin", "start"]
    maxplayers = 4
    def __init__(self, bot, game_id, msg):
        super().__init__(bot, game_id, msg)
        self.players = [(self.sender_id,self.sender_name)]
        self.started = False
        self.save_game_state()

    def message_init(self):
        txt = self.welcome+"\n*" + self.sender_name
        self.ident = self.send_keyboard_message(self.chat_id, txt, self.buttons, self.callback)

    def callback(self, ident, button_id, s):
        sender, sendername = s
        if self.started: return "Potje is al begonnen"
        if button_id == 0: #join/unjoin
            if self.players.count((sender,sendername)):
                self.players.remove((sender,sendername))
                self.update_message()
                return "Unjoined"
            else:
                if len(self.players) == self.maxplayers:
                    return "Het spel zit al vol"
                self.players.append((sender,sendername))
                self.update_message()
                return "Joined"

        elif button_id == 1: #start game
            if not self.players:
                return "Er moet wel iemand meedoen"
            if sender != self.sender_id:
                return "Alleen {} kan dit potje beginnen".format(self.sender_name)
            index = len(self.bot.dataManager.games)
            self.started = True
            g = Klaverjas(self.bot,index,self.players,self.date, self.cmd)
            g.final_callback = self.game_end
            self.bot.games[index] = g
            editor = telepot.helper.Editor(self.bot.telebot, self.ident)
            editor.editMessageReplyMarkup()
            return "Spel gestart"

    def update_message(self):
        msg = self.welcome +"\n" +"\n".join("* "+n for i,n in self.players)
        editor = telepot.helper.Editor(self.bot.telebot, self.ident)
        editor.editMessageText(msg, reply_markup=self.get_keyboard(self.buttons,index=0))
        self.save_game_state()

    def game_end(self, g):
        msg = g.game_end_message()
        editor = telepot.helper.Editor(self.bot.telebot, self.ident)
        editor.editMessageText(msg,parse_mode="Markdown")


class KlaverjasChallenge(BaseDispatcher):
    game_type = KLAVERJASSEN_CHALLENGE
    welcome = "Klaverjas Challenge. Deelnemers:"
    buttons = ["start", "unveil", "unveil all"]

    def __init__(self, bot, game_id, msg):
        super().__init__(bot, game_id, msg)
        self.players = OrderedDict({1:"Henk",self.sender_id: self.sender_name})
        self.seed = ''.join(random.choice(string.ascii_lowercase) for _ in range(10))
        self.games = {}
        self.unveiled = False
        self.loaded = True
        self.save_game_state()
        for d in [[],[(self.sender_id,self.sender_name)]]:
            index = len(self.bot.dataManager.games)
            g = Klaverjas(self.bot,index,d,self.date, self.seed)
            self.bot.games[index] = g
            g.final_callback = self.game_end
            if d: self.games[d[0][0]] = g
            else: self.games[1] = g
        self.update_message()
        self.save_game_state()

    def __getstate__(self):
        state = super().__getstate__()
        state['games'] = {pid: g.game_id for pid,g in self.games.items()}
        state['loaded'] = False
        return state

    def load(self):
        for pid in self.games:
            if isinstance(self.games[pid], Klaverjas): continue
            g = self.bot.dataManager.load_game(self.games[pid])
            g.setstate(self.bot)
            self.games[pid] = g
        self.loaded = True

    def callback(self, ident, button_id, s):
        if not hasattr(self, "loaded") or not self.loaded: self.load()
        sender, sendername = s
        if button_id == 0:
            if sender in self.players:
                if self.games[sender].is_active:
                    return "Je bent al bezig met een potje"
                return "Je hebt je kans gehad, sorry"
            index = len(self.bot.dataManager.games)
            g = Klaverjas(self.bot,index,[(sender, sendername)],self.date, self.seed)
            self.bot.games[index] = g
            g.final_callback = self.game_end
            self.games[sender] = g
            self.players[sender] = sendername
            self.update_message()
            return "Potje gestart"
        elif button_id == 1:
            if self.unveiled: return "Al unveiled"
            if sender not in self.games: return "Je mag alleen kijken als je een potje gedaan hebt"
            if self.games[sender].is_active: return "Maak eerst je potje af"
            msg = self.generate_unveil_message()
            self.send_user_message(msg, sender)
            return "Zie Henk"
        elif button_id == 2:
            if self.unveiled: return "Al unveiled"
            if sender != self.sender_id:
                return "Alleen {} mag dit doen".format(self.sender_name)
            self.unveiled = True
            self.buttons = ["start"]
            self.update_message()
            return "Unveiled"

    def generate_unveil_message(self):
        if not self.loaded: self.load()
        l = []
        for sid, name in self.players.items():
            g = self.games[sid]
            if not g.is_active:
                l.append("*{}: {}".format(name, g.summarize()))
        msg = "\n".join(l)
        if not msg: return "Nog niemand is klaar met spelen"
        return msg

    def update_message(self):
        if not hasattr(self, "loaded") or not self.loaded: self.load()
        msg = self.welcome +"\n" 
        for sender_id, name in self.players.items():
            g = self.games[sender_id]
            if g.is_active:
                msg += "*{}: Bezig met spelen\n".format(name)
            else:
                if self.unveiled:
                    msg += "*{}: {}\n".format(name, g.summarize())
                else:
                    msg += "{}: Klaar (score verborgen)\n".format(name)
        editor = telepot.helper.Editor(self.bot.telebot, self.ident)
        editor.editMessageText(msg, reply_markup=self.get_keyboard(self.buttons,index=0))
        self.save_game_state()

    def game_end(self, g):
        self.update_message()
        if not self.unveiled:
            try:
                pid = list(g.player_names.keys())[0]
                msg = self.generate_unveil_message()
                self.send_user_message(msg, pid)
            except IndexError: pass # Henk finished its game

    def message_init(self):
        txt = "{}\n*Henk: Bezig met spelen\n*{}: Bezig met spelen".format(self.welcome, self.sender_name)
        self.ident = self.send_keyboard_message(self.chat_id, txt, self.buttons, self.callback)



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
