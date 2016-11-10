##Game Description & Instruction:
Hangman is a simple word-guessing game. Everytime you start a game, there is a 'word'.
'word' is a random implemented word and you play game by guessing the word a letter
by letter. There's 6 chances to guess the word, but if you nominate letter 
which is in the 'word', the chances are not decreased. Everytime you missed letter, 
hangman picture is drawing little by little, and after 6 chances are gone, hangman 
picture is complete and the game is over. your guess is sent to the `make_move` endpoint.
Many different Hangman games can be played by many different Users at any
given time. Each game can be retrieved or played by using the path parameter
`urlsafe_game_key`.

##Score Keeping
Score of this game is remaining chances. for example, the 6 chances are given at the
first place, and if you missed one letter, your scrore is 5. and you are fail to 
guess the word, than your score is 0.  


##Files Included:
 - api.py: Contains endpoints and game playing logic.
 - app.yaml: App configuration.
 - cron.yaml: Cronjob configuration.
 - main.py: Handler for taskqueue handler.
 - models.py: Entity and message definitions including helper methods.
 - utils.py: Helper function for retrieving ndb.Models by urlsafe Key string.

##Endpoints Included:
 - **create_user**
    - Path: 'user'
    - Method: POST
    - Parameters: user_name, email (optional)
    - Returns: Message confirming creation of the User.
    - Description: Creates a new User. user_name provided must be unique. 
    If the user_name exist, there would be an ConflictException error.
    
 - **new_game**
    - Path: 'game'
    - Method: POST
    - Parameters: user_name, urlsafe_game_key
    - Returns: GameForm with initial game state.
    - Description: Creates a new Game. Input parameter is user_name and it
    should exist alrealdy or raise an error. take queue also functions to udate
    average moves remaining for active games.
     
 - **get_game**
    - Path: 'game/{urlsafe_game_key}'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: GameForm with current game state.
    - Description: Returns the current state of a game.
    
 - **make_move**
    - Path: 'game/{urlsafe_game_key}'
    - Method: PUT
    - Parameters: urlsafe_game_key, guess
    - Returns: GameForm with new game state.
    - Description: Accepts a 'guess' and returns the updated state of the game.
    If this causes a game to end, a corresponding Score entity will be created.
    
 - **get_scores**
    - Path: 'scores'
    - Method: GET
    - Parameters: None
    - Returns: ScoreForms.
    - Description: Returns all Scores in the database (unordered).
    
 - **get_user_scores**
    - Path: 'scores/user/{user_name}'
    - Method: GET
    - Parameters: user_name
    - Returns: ScoreForms. 
    - Description: Returns all Scores recorded by the provided player (unordered).
    Will raise a NotFoundException if the User does not exist.
    
 - **get_average_attemps_remaining**
    - Path: 'games/average_attemps'
    - Method: GET
    - Parameters: None
    - Returns: StringMessage
    - Description: Gets the average number of attempts remaining for all games
    from a previously cached memcache key.

 - **get_user_games**
    - Path: 'games/active'
    - Method: GET
    - Parameters: None
    - Returns: UserGamesForms
    - Description: Get the active games grouped by users

 - **cancel_game**
    - Path: 'games/cancel'
    - Method: DELETE
    - Parameters: urlsafe_game_key
    - Returns: StringMessage
    - Description: input the urlsafe_game_key and cancel the active game. 
    you can't cancel or delete game which is over.

 - **get_high_scores**
    - Path: 'games/high_scores'
    - Method: GET
    - Parameters: number_of_results
    - Returns: ScoreForms
    - Description: Get a leaderboard of games which score is in descending
    order. and the score means remining chances

 - **get_user_rankings**
    - Path: 'games/rankings'
    - Method: GET
    - Parameters: None
    - Returns: RankingForms
    - Description: get win/loss ratio of each user and save it to users. and get
    rankings which user have the high win/loss ratio. 


 - **get_game_history**
    - Path: 'games/history'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: HistroyForm
    - Description: input urlsafe_game_key and get the history of the game.
    History includes guessed letter, cracked_letter.
    
##Cron job:
 - **SendReminderEmail**
    - get email of users, if exist, and filtering which game is not over,
    and send email to users to alert that the incompleted game.

##Forms Included:
 - **GameForm**
    - Representation of a Game's state (urlsafe_key, attempts_remaining,
    game_over flag, message, user_name, cracked_word, secret_word,
    guessed_letter, missed_letter, hangmanpic).
 - **NewGameForm**
    - Used to create a new game (user_name)
 - **MakeMoveForm**
    - Inbound make move form (guess).
 - **ScoreForm**
    - Representation of a completed game's Score (user_name, date, won flag,
    points).
 - **ScoreForms**
    - Multiple ScoreForm container. (items)
 - **GameForms**
    - Multiple GameForm container. (items)
 - **StringMessage**
    - General purpose String container.
 - **UserGamesForm**
    - Representation of games with username. (user_games)
 - **UserGamesForms**
    - Multiple UserGamesForm container. (items)
 - **RankingForm**
    - Representation of user with win/loss ratio. (user_name, ratio)
 - **RankingForms**
    - Multiple RankingForm container. (items)
 - **HistoryForm**
    - Representation of hitory of game chosen by key. (moves)