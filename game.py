""" Defines `game` class"""
from enum import Enum
from typing import Dict, List


URL_METACRITIC = 'https://www.metacritic.com/game/'
URL_OPENCRITIC = 'https://opencritic.com/game/'

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

# TODO with PSN API, would it be possible to add an entry automatically each time a game is purchased?
class Game:
    """A class to hold metadata on a game"""
    def __init__(self, wikidata: Dict[str, str]):
        # attributes to be filled by user
        self.my_score = 0
        self.goals = {}
        #self.pro_enhanced: bool = False
        #self.note
        #self.released = released # TODO verify compared to the current date with the release date
        #self.purchase_date = purchase_date
        #self.play_platform = playing_platform
        # self.status = status
        # self.hyped_level = hyped_level

        # attributes to be filled automatically
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



        # self.metadata_sources: List[Dict]= [
        #     {
        #         'attribute': 'genre',
        #         'selector': '',
        #         'variable': self.genre
        #     },
        #     {
        #         'attribute': 'developer',
        #         'selector': '',
        #         'variable': self.developer
        #     },
        #     {
        #         'attribute': 'publisher',
        #         'selector': '',
        #         'variable': self.publisher
        #     },
        #     {
        #         'attribute': 'meta_critics_score',
        #         'selector': '',
        #         'variable': self.meta_critics_score
        #     },
        #     {
        #         'attribute': 'meta_user_score',
        #         'selector': '',
        #         'variable': self.meta_user_score
        #     },
        #     {
        #         'attribute': 'open_critics_score',
        #         'selector': '',
        #         'variable': self.open_critics_score
        #     },
        #     {
        #         'attribute': 'open_user_score',
        #         'selector': '',
        #         'variable': self.open_user_score
        #     }
        # ]


    def _parse_date(self) -> None:
        """Parses the date given as string into Date class"""
        pass


    def _extract_metadata(self, data_name: str, source_url: str) -> None:
        """Extract and store desired data by crawling the source URL."""
        pass

    