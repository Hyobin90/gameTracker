""" Defines `game` class"""
from enum import Enum
from typing import Dict
from datetime import datetime


class Platform(Enum):
    """Collections of platforms"""
    PS4 = 'PS4'
    PS5 = 'PS5'


class Status(Enum):
    """Collectons of current status of a game."""
    ANNOUNCED = 'announced'
    COMMING = 'comming' 
    COMMING_SOON = 'comming soon' # GTPS-010 Allow the user to define the sense of how soon
    RELEASED = 'released'
    PURCHASE = 'purchased'
    PLAYING = 'playing'
    PAUSED = 'paused'
    COMPLETED = 'completed as aimed'


class Expectation(Enum):
    """Collection of the level of being excited about the game."""
    VERY_HIGH = 3
    HIGH = 2
    INTERESTED = 1
    NOTICING = 0


class Goals(Enum):
    """Collections of frequently mentioned goals for the game."""
    ALL_TRPOHYIES = 'all_trophies'


class Game:
    """A class to hold metadata on a game"""
    def __init__(self, title:str, purchase_date:str, play_platform:str, expectation:int, use_wikidata:bool, wikidata =Dict[str, str]):
        # Necessary data on the game
        self.title = title
        self.purchase_date = datetime.strptime(purchase_date, '%Y-%m-%d')
        self.play_platform = Platform(play_platform)
        self.expectaion = Expectation(int(expectation)).value
        self.use_wikidata = use_wikidata

        # Data from `Wikidata`
        self.wikipedia_link = ''
        self.wikidata_link = ''
        self.genres = ''
        self.developers = ''
        self.publishers = ''
        self.release_date = None
        self.platforms = ''
        self.title = ''
        self.logo = None

        # Data to be filled after playing # TODO maybe with NoSQL implemented
        self.goals = {}
        self.note = ''
        self.my_score = 0

        ## Data from `Metacritics`
        self.meta_critics_score = 0
        self.meta_user_score = 0
        ## Data from `Opencritics`
        self.open_critics_score = 0
        self.open_user_score = 0

        # Data from `PSN API`
        self.pro_enhanced: bool = False

        # Attributes to be updated automatically
        # self.released = released # TODO verify compared to the current date with the release date
        # self.status = status

        if use_wikidata:
            self.fill_metadata_from_wikidata(wikidata)

    def fill_metadata_from_wikidata(self, wikidata:Dict[str, str]):
        """Fills up the metadata from `Wikidata` """
        self.wikipedia_link = wikidata.get('wikipedia_link')
        self.wikidata_link = wikidata.get('wikidata_link')
        self.genres = wikidata.get('genres')
        self.developers = wikidata.get('developers')
        self.publishers = wikidata.get('publishers')
        self.release_date = datetime.strptime(wikidata.get('release_date')[:10], '%Y-%m-%d') #TODO error handling is required
        self.platforms = wikidata.get('platforms') # TODO allow to select the platform
        #self.logo = wikidata.get('logo') # TODO handle the logo image

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