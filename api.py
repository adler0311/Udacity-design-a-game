# -*- coding: utf-8 -*-`
"""api.py - Create and configure the Game API exposing the resources.
This can also contain game logic. For more complex games it would be wise to
move game logic to another file. Ideally the API will be simple, concerned
primarily with communication to/from the API's users."""


import logging
import endpoints
from protorpc import remote, messages
from google.appengine.api import memcache
from google.appengine.api import taskqueue
from utils import get_by_urlsafe

from models import (
  User,
  Game,
  Score,
)

from models import (
  StringMessage,
  NewGameForm,
  GameForm,
  MakeMoveForm,
  ScoreForms,
  GameForms,
  RankingForm,
  RankingForms,
  HistoryForm,
  UserGamesForms
)

GET_URLSAFE_GAME_KEY_REQUEST = endpoints.ResourceContainer(
  urlsafe_game_key=messages.StringField(1))
NEW_GAME_REQUEST = endpoints.ResourceContainer(NewGameForm,
        urlsafe_game_key=messages.StringField(1))
MAKE_MOVE_REQUEST = endpoints.ResourceContainer(
    MakeMoveForm,
    urlsafe_game_key=messages.StringField(1),)
USER_REQUEST = endpoints.ResourceContainer(user_name=messages.StringField(1),
                                           email=messages.StringField(2))
GET_HIGH_SCORES_REQUEST = endpoints.ResourceContainer(
    number_of_results=messages.IntegerField(1))

MEMCACHE_MOVES_REMAINING = 'MOVES_REMAINING'

@endpoints.api(name='hangman', version='v1')
class HangmanApi(remote.Service):
    """Game API"""
    @endpoints.method(request_message=USER_REQUEST,
                      response_message=StringMessage,
                      path='user',
                      name='create_user',
                      http_method='POST')
    def create_user(self, request):
        """Create a User. Requires a unique username"""
        if User.query(User.name == request.user_name).get():
            raise endpoints.ConflictException(
                    'A User with that name already exists!')
        user = User(name=request.user_name, email=request.email)
        user.put()
        return StringMessage(message='User {} created!'.format(
                request.user_name))

    @endpoints.method(request_message=NEW_GAME_REQUEST,
                      response_message=GameForm,
                      path='game',
                      name='new_game',
                      http_method='POST')
    def new_game(self, request):
        """Creates new game"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        game = Game.new_game(user.key)

        # Use a task queue to update the average attempts remaining.
        # This operation is not needed to complete the creation of a new game
        # so it is performed out of sequence.
        taskqueue.add(url='/tasks/cache_average_attempts')
        return game.to_form('Good luck playing Hangman!')

    @endpoints.method(request_message=GET_URLSAFE_GAME_KEY_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='get_game',
                      http_method='GET')
    def get_game(self, request):
        """Return the current game state."""
        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            return game.to_form('Time to make a move!')
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(request_message=MAKE_MOVE_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='make_move',
                      http_method='PUT')
    def make_move(self, request):
        """Makes a move. Returns a game state with message"""

        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game.game_over:
          raise endpoints.ForbiddenException('Illegal action: Game is already over.')

        # Guessing the letter 
        if request.guess.isalpha() and not "":
          letter = request.guess

          if len(letter) != len(game.secret_word) and len(letter) != 1:
            msg = ("Wrong. you failed to guess whole word or just guess letter one by one.")
            game.attempts_remaining -= 1
          else:
            if letter == game.secret_word:
              msg = ('Wow. You just guessed entire word. You Win!')
              game.moves.append("(guess: %s, result: %s)" % (request.guess, msg))
              game.cracked_word = game.secret_word
              game.end_game(True)
              return game.to_form(msg)
            else:
              if letter in game.secret_word and letter not in game.guessed_letters:
                game.guessed_letters.append(letter)
                msg = ('Correct! Still ')

              elif letter not in game.secret_word and letter not in game.missed_letters:
                game.missed_letters.append(letter)
                msg = ('That\'s too bad! Incorrect!')
                game.attempts_remaining -= 1

              elif letter in game.guessed_letters or letter in game.missed_letters:
                msg = ('You\'ve already tried this letter!')
                game.attempts_remaining -= 1

              game.cracked_word = ""
              for letter in game.secret_word:
                if letter not in game.guessed_letters:
                  game.cracked_word+='_'
                else:
                  game.cracked_word+=letter
              
              if '_' not in game.cracked_word:
                msg = ('You Win! You correct the word!')
                game.moves.append("(guess: %s, result: %s)" % (request.guess, msg))
                game.end_game(True)
                return game.to_form(msg)
              
        else:
          game.to_form('You have to put alphanumeric letter!')

        if game.attempts_remaining < 1:
          msg = (msg + ' Game over!')
          game.moves.append("(guess: %s, result: %s)" % (request.guess, msg))
          game.end_game(False)
          return game.to_form(msg)
        else:
          game.moves.append("(guess: %s, result: %s)" % (request.guess, game.cracked_word))
          game.put()
          return game.to_form(msg + ' %sremains' %(game.attempts_remaining))



    @endpoints.method(response_message=ScoreForms,
                      path='scores',
                      name='get_scores',
                      http_method='GET')
    def get_scores(self, request):
        """Return all scores"""
        return ScoreForms(items=[score.to_form() for score in Score.query()])

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=ScoreForms,
                      path='scores/user/{user_name}',
                      name='get_user_scores',
                      http_method='GET')
    def get_user_scores(self, request):
        """Returns all of an individual User's scores"""
        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                    'A User with that name does not exist!')
        scores = Score.query(Score.user == user.key)
        return ScoreForms(items=[score.to_form() for score in scores])

    @endpoints.method(response_message=StringMessage,
                      path='games/average_attempts',
                      name='get_average_attempts_remaining',
                      http_method='GET')
    def get_average_attempts(self, request):
        """Get the cached average moves remaining"""
        return StringMessage(message=memcache.get(MEMCACHE_MOVES_REMAINING) or '')

    @staticmethod
    def _cache_average_attempts():
        """Populates memcache with the average moves remaining of Games"""
        games = Game.query(Game.game_over == False).fetch()
        if games:
            count = len(games)
            total_attempts_remaining = sum([game.attempts_remaining
                                        for game in games])
            average = float(total_attempts_remaining)/count
            memcache.set(MEMCACHE_MOVES_REMAINING,
                         'The average moves remaining is {:.2f}'.format(average))

    @endpoints.method(response_message=UserGamesForms,
                      path='games/active',
                      name='get_user_active_games',
                      http_method='GET')
    def get_user_games(self, request):
      """Get all the User's active game"""
      users = User.query()
      for user in users:
        games = Game.query(Game.game_over == False)
        games = games.filter(Game.user == user.key)
        active_games = []
        for game in games:
          active_games.append(game.to_form())

        user.user_games = "%s : %s" % (user.name, active_games)
        user.put()

      return UserGamesForms(items=[user.to_usergamesform() for user in User.query()])



    @endpoints.method(request_message=GET_URLSAFE_GAME_KEY_REQUEST,
                      response_message=StringMessage,
                      path='games/cancel',
                      name='cancel_game',
                      http_method='DELETE')
    def cancel_game(self, request):
      game = get_by_urlsafe(request.urlsafe_game_key, Game)
      if game.game_over == True:
        msg=("You can't cancel this game!")
      else:
        game.key.delete()
        msg=("You just canceled this game!")

      return StringMessage(message=msg)


    @endpoints.method(request_message=GET_HIGH_SCORES_REQUEST,
                      response_message=ScoreForms,
                      path='games/high_scores',
                      name='get_high_scores',
                      http_method='GET')
    def get_high_scores(self, request):      
      return ScoreForms(items=[score.to_form() for score in Score.query().order(-Score.points).fetch(request.number_of_results)])


    @endpoints.method(
                      response_message=RankingForms,
                      path='games/rankings',
                      name='get_user_rankings',
                      http_method='GET')
    def get_user_rankings(self, request):
      # get ratio and save to each user. 
      users = User.query()
      for user in users:
        scores = Score.query(Score.user == user.key).fetch()
        if scores:
          for score in scores:
            if score.won == True:
              user.wons += 1
            else:
              user.losts += 1
        user.put()

      return RankingForms(items = [user.to_rankingform() for user in User.query()])

    @endpoints.method(request_message=GET_URLSAFE_GAME_KEY_REQUEST,
                      response_message=HistoryForm,
                      path='games/history',
                      name='get_game_history')
    def get_game_history(self, request):
      game = get_by_urlsafe(request.urlsafe_game_key, Game)

      return game.to_historyform()

api = endpoints.api_server([HangmanApi])
