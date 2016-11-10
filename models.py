"""models.py - This file contains the class definitions for the Datastore
entities used by the Game. Because these classes are also regular Python
classes they can include methods (such as 'to_form' and 'new_game')."""

import random
from datetime import date
from protorpc import messages
from google.appengine.ext import ndb
from board import board
from words import words

class User(ndb.Model):
    """User profile"""
    name = ndb.StringProperty(required=True)
    email =ndb.StringProperty()
    wons = ndb.IntegerProperty(required=True, default=0)
    losts = ndb.IntegerProperty(required=True, default=0)
    ratio = ndb.ComputedProperty(lambda self: float(0) if self.wons ==0 and\
             self.losts==0 else float(self.wons)/(self.wons+self.losts) )
    user_games = ndb.TextProperty(required=True, default="")   

    def to_usergamesform(self):
        form = UserGamesForm()
        form.user_games = self.user_games
        return form

    def to_rankingform(self):
        form = RankingForm()
        form.user_name=self.name
        form.ratio = self.ratio
        return form

class Game(ndb.Model):
    """Game object"""
    secret_word = ndb.StringProperty(required=True)
    cracked_word = ndb.StringProperty(required=True)
    guessed_letters = ndb.StringProperty(repeated=True)
    missed_letters = ndb.StringProperty(repeated=True)
    attempts_allowed = ndb.IntegerProperty(required=True, default=6)
    attempts_remaining = ndb.IntegerProperty(required=True, default=6)
    game_over = ndb.BooleanProperty(required=True, default=False)
    user = ndb.KeyProperty(required=True, kind='User')
    moves = ndb.StringProperty(repeated=True)

    @classmethod # here, save to the ndb model
    def new_game(cls, user):
        """Creates and returns a new game"""
        word = words[random.randint(0,len(words)-1)]
        game = Game(user=user, game_over=False, secret_word=word,cracked_word=len(word)*"_")
        game.put()
        return game

    def to_form(self, message=''): # make a form for response
        """Returns a GameForm representation of the Game"""
        form = GameForm()
        form.urlsafe_key = self.key.urlsafe()
        form.user_name = self.user.get().name
        form.attempts_remaining = self.attempts_remaining
        form.game_over = self.game_over
        form.cracked_word = self.cracked_word
        form.secret_word = self.secret_word
        form.guessed_letters = self.guessed_letters
        form.missed_letters = self.missed_letters
        form.message = message
        form.hangingpic = board[len(self.missed_letters)]
        return form

    def end_game(self, won=False):
        """Ends the game - if won is True, the player won. - if won is False,
        the player lost."""
        self.game_over = True
        self.put()
        # Add the game to the score 'board'
        score = Score(user=self.user, date=date.today(), won=won,
                      points=self.attempts_remaining)
        score.put()


    def to_historyform(self):
        form = HistoryForm()
        form.moves = self.moves
        return form


class Score(ndb.Model):
    """Score object"""
    user = ndb.KeyProperty(required=True, kind='User')
    date = ndb.DateProperty(required=True)
    won = ndb.BooleanProperty(required=True)
    points = ndb.IntegerProperty(required=True)


    def to_form(self):
        return ScoreForm(user_name=self.user.get().name, won=self.won,
                         date=str(self.date), points=self.points)


class GameForm(messages.Message):
    """GameForm for outbound game state information"""
    urlsafe_key = messages.StringField(1, required=True) # game key
    attempts_remaining = messages.IntegerField(2, required=True)
    game_over = messages.BooleanField(3, required=True)
    message = messages.StringField(4, required=True)
    user_name = messages.StringField(5, required=True)
    cracked_word = messages.StringField(6, required=True)
    secret_word = messages.StringField(7, required=True)
    guessed_letters = messages.StringField(8, repeated=True)
    missed_letters = messages.StringField(9, repeated=True)
    hangingpic = messages.StringField(10, required=True)


class NewGameForm(messages.Message): # request
    """Used to create a new game"""
    user_name = messages.StringField(1, required=True)


class MakeMoveForm(messages.Message):
    """Used to make a move in an existing game"""
    guess = messages.StringField(1, required=True)


class ScoreForm(messages.Message):
    """ScoreForm for outbound Score information"""
    user_name = messages.StringField(1, required=True)
    date = messages.StringField(2, required=True)
    won = messages.BooleanField(3, required=True)
    points = messages.IntegerField(4, required=True)


class ScoreForms(messages.Message):
    """Return multiple ScoreForms"""
    items = messages.MessageField(ScoreForm, 1, repeated=True)

class GameForms(messages.Message):
    """Return multiple GameForms"""
    items = messages.MessageField(GameForm, 1, repeated=True)    

class StringMessage(messages.Message):
    """StringMessage-- outbound (single) string message"""
    message = messages.StringField(1, required=True)

class UserGamesForm(messages.Message):
    user_games = messages.StringField(1, required=True)

class UserGamesForms(messages.Message):
    items = messages.MessageField(UserGamesForm, 1, repeated=True)

class RankingForm(messages.Message):
    """return rankingForm"""
    user_name = messages.StringField(1, required=True)
    ratio = messages.FloatField(4, required=True)

class RankingForms(messages.Message):
    """Return multiple rankingForm"""
    items = messages.MessageField(RankingForm, 1, repeated=True)

class HistoryForm(messages.Message):
    """return historyform"""
    moves = messages.StringField(1, repeated=True)