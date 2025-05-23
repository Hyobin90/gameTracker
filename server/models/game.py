""" Defines `game` class"""
from enum import Enum
from typing import Dict
from datetime import datetime
import re


class Platform(Enum):
    """Collections of platforms"""
    PS4 = 'PS4'
    PS5 = 'PS5'


class Status(Enum):
    """Collectons of current status of a game."""
    ANNOUNCED = 'announced'
    COMING = 'coming' 
    COMING_SOON = 'coming soon'
    # PREORDER_AVAILABLE = 'pre-order available' # TODO Find out if it's to be retrieved from PSN update
    PREORDERED = 'pre-oredered'
    RELEASED = 'released'
    PURCHASED = 'purchased'
    PLAYING = 'currently playing'
    PAUSED = 'paused'
    COMPLETED = 'completed as aimed'


class Expectation(Enum):
    """Collection of the level of being excited about the game."""
    MUST_PLAY = 4
    HYPED = 3
    LOOKING_FORWARD = 2
    INTERESTED = 1
    NOTICED = 0


class Goals(Enum):
    """Collections of frequently mentioned goals for the game."""
    ALL_TRPOHYIES = 'all_trophies'


class Game:
    """A class to hold metadata on a game"""
    def __init__(self, title:str, game_id:str, aliases: str, wikidata_code: str, is_DLC: int,
                 genres: str, developers: str, publishers: str,
                 release_id: str, release_date: str, released: bool,
                 platforms: str, purchase_date: str, purchased: bool, **kwargs):
        # Necessary data on the game
        self.title = title
        self.game_id = game_id
        self.aliases = aliases.split(', ')
        self.wikidata_code = wikidata_code
        self.is_dlc = True if is_DLC else False
        #self.parent_id = parent_id
        self.genres = genres.split(', ')
        self.developers = developers.split(', ')
        self.publishers = publishers.split(', ')
        self.release_id = release_id
        self.release_date = datetime.strptime(release_date, '%Y-%m-%d')
        self.released = True if released else self._is_released
        self.platforms = platforms.split(', ')

        # Attributes to be updated per user, stored in their DB, not stored in game_db
        self.status: Status = None
        self.purchase_date = datetime.strptime(purchase_date, '%Y-%m-%d')
        self.purchased = purchased
        # self.playing = None
        # self.played = None


        # Data to be filled after playing
        # self.my_score = 0
        # self.goals = {}
        # self.note = ''
        # self.logo = None

        ## Data from `PSN API`
        # self.pro_enhanced = pro_enhanced
        # ## Data from `Metacritics`
        # self.meta_critics_score = 0
        # self.meta_user_score = 0
        # ## Data from `Opencritics`
        # self.open_critics_score = 0
        # self.open_user_score = 0


    def update_status(self) -> None:
        """Centralizes updating the status of the game based on `released`, `purchased`, and `playing`"""
        try:
            if not self.release_date:
                self.status = Status.ANNOUNCED
                return

            days_till_release = self._calculate_days_till_release()
            if not self.released:
                if self.purchased:
                    self.status = Status.PREORDERED
                elif days_till_release > 180:
                    self.status = Status.COMING
                elif days_till_release <= 180:
                    self.status = Status.COMING_SOON
                return
            
            if self.released:
                if self.purchased and self.playing:
                    self.status = Status.PLAYING
                elif self.purchased and not self.playing and self.played:
                    self.status = Status.PAUSED
                elif self.purchased:
                    self.status = Status.PURCHASED
                else:
                    self.status = Status.RELEASED
        except Exception as e:
            print(f'Error occurred while updating Game status : {e}')
    

    def _set_game_active(self) ->  None:
        """Set the game currently playing."""
        if self.purchased:
            self.playing = True
            self.played = True
            self.update_status()


    def _set_game_inactive(self) -> None:
        """Set the game paused."""
        if self.purchased and self.playing:
            self.playing = False
            self.update_status()


    def _is_released(self) -> bool:
        """Verifies whether a game has been released."""
        current_date = datetime.today()
        released = None
        if not self.release_date:
            released = False
        elif self.release_date:
            if self.release_date <= current_date:
                released = True
            else:
                released = False
        return released


    def _calculate_days_till_release(self) -> int:
        """Verifies if the game will be released soon."""
        if not self.release_date:
            raise RuntimeError('Even no release date has been announced.')
        else:
            current_date = datetime.today()
            return (self.release_date - current_date).days


    # TODO this should be called by the client
    def fill_post_playing_data(self):
        """Fills up certain data after playing"""
        pass
        # self.goals = {}
        # self.note = ''
        # self.my_score = 0


    def fill_meta_score(self):
        """Retrieve critics score and user score from `Metacritic`"""
        pass
        # self.play_platform # it will be needed for `Metacritic`
        # self.meta_critics_score = 0
        # self.meta_user_score = 0


    def fill_open_score(self):
        """Retrieve critics score and user score from `Opencritic`"""
        pass
        # self.open_critics_score = 0
        # self.open_user_score = 0
                

def _validate_date_format(value):
    """Validate if `value` consolidates the desired date pattern."""
    date_pattern = r'^\d{4}-\d{2}-\d{2}$'
    if re.match(date_pattern, value):
        return True
    else:
        return False