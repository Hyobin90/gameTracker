""" Defines `game` class"""
from enum import Enum
from typing import Dict
from datetime import datetime


URL_METACRITIC = 'https://www.metacritic.com/game/'
URL_OPENCRITIC = 'https://opencritic.com/game/'

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
    def __init__(self, personal_data: Dict[str, str], wikidata: Dict[str, str]):
        # attributes to be filled by user
        ## filled up initally
        self.purchase_date = datetime.strptime(personal_data['purchase_date'], '%Y-%m-%d')
        self.play_platform = Platform(personal_data['play_platform'])
        self.expectaion = Expectation(int(personal_data['expectation'])).value
        
        # TODO maybe with NoSQL implemented
        # self.goals = {}
        # self.note = ''
        # self.my_score = 0

        # attributes to be filled automatically
        ## updated automatically
        # self.released = released # TODO verify compared to the current date with the release date
        # self.status = status
        
        ## from `WikiData`
        self.wikipedia_link = wikidata['wikipedia_link']
        self.wikidata_link = wikidata['wikidata_link']
        self.genres = wikidata['genres']
        self.developers = wikidata['developers']
        self.publishers = wikidata['publishers']
        self.release_date = wikidata['release_date'] # 
        self.platforms = wikidata['platforms'] # TODO allow to select the platform
        self.title = wikidata['title']

        ## from `Metacritics`
        self.meta_critics_score = 0
        self.meta_user_score = 0
        ## from `Opencritics`
        self.open_critics_score = 0
        self.open_user_score = 0

        # from `PSN API`?
        #self.pro_enhanced: bool = False
