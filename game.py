""" Defines `game` class"""
import datetime
from enum import Enum
import requests


class Platform(Enum):
    """Collections of platforms"""
    PS5 = 'PlayStation5'
    PS5_PRO = 'PlayStation5 Pro'

class Status(Enum):
    """Collectons of current status of playing a game"""
    ANNOUNCED = 'announced'
    COMMING = 'comming' 
    COMMING_SOON = 'comming soon' # TODO let the user define how soon
    RELEASED = 'released'
    PLAYING = 'playing'
    PAUSED = 'paused'
    COMPLETED = 'completed as aimed'
    # TODO Find logics to describe completed but still playing including playing through multiple time
    # TODO in the client, the options for the status should be provided as a drop-down list

class game:
    """A class to hold meta data on a game"""
    def __init__(self, title: str, released: bool, purchase_date: str, playing_platform: str, status: str, hyped_level: str):
        self.title = title
        self.purchase_date = purchase_date
        self.play_platform = playing_platform
        self.status = status
        self.hyped_level = hyped_level

        # attributes to be filled automatically
        self.genre = ''
        self.developer = ''
        self.publisher = ''
        self.meta_critics_score = 0
        self.meta_user_score = 0
        self.open_critics_score = 0
        self.open_user_score = 0

        # attributes to be filled by user
        self.my_score = 0
        self.goals = {}

        self._verify_title()
        self._retrieve_genere()

    def _verify_title(self) -> None:
        """Verifies and corrects the given title on Wikipedia."""
        # Search for the game with the given title on Wikipedia.
        # Check if the game exists with the title
        # if it doesn't exist, raise an error
        # if the game exists but the title is not accurate
        # find and put the correct name into `self.title`
        pass


    def _parse_date(self) -> None:
        """Parses the date given as string into Date class"""
        pass


    def _retrieve_genere(self) -> None:
        """Fill out the genre of the game via Wikipedia"""
        pass

    