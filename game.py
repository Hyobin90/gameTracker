""" Defines `game` class"""
from bs4 import BeautifulSoup
import datetime
from enum import Enum
import requests
from typing import Any, Dict, List

URL_WIKIPEDIA = 'https://en.wikipedia.org/'
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
class game:
    """A class to hold metadata on a game"""
    def __init__(self, title: str, released: bool, purchase_date: str, playing_platform: str, status: str, hyped_level: str):
        self.title = self._verify_title(title)
        self.released = released # TODO verify compared to the current date with the release date
        self.purchase_date = purchase_date
        self.play_platform = playing_platform
        self.status = status
        self.hyped_level = hyped_level

        self.url_wikipedia = self._construct_url(self.title, URL_WIKIPEDIA)
        self.url_metacritic = self._construct_url(self.title, URL_METACRITIC)
        self.url_opencritic = self._construct_url(self.title, URL_OPENCRITIC)

        # attributes to be filled automatically
        # from `Wikipedia`
        self.genre = ''
        self.developer = ''
        self.publisher = ''
        self.release_date = ''

        # from `Metacritics`
        self.meta_critics_score = 0
        self.meta_user_score = 0
        # from `Opencritics`
        self.open_critics_score = 0
        self.open_user_score = 0

        # attributes to be filled by user
        self.my_score = 0
        self.goals = {}

        self.metadata_sources: List[Dict]= [
            {
                'attribute': 'genre',
                'selector': '',
                'url': f'{URL_WIKIPEDIA}',
                'variable': self.genre
            },
            {
                'attribute': 'developer',
                'selector': '',
                'url': '',
                'variable': self.developer
            },
            {
                'attribute': 'publisher',
                'selector': '',
                'url': '',
                'variable': self.publisher
            },
            {
                'attribute': 'meta_critics_score',
                'selector': '',
                'url': '',
                'variable': self.meta_critics_score
            },
            {
                'attribute': 'meta_user_score',
                'selector': '',
                'url': '',
                'variable': self.meta_user_score
            },
            {
                'attribute': 'open_critics_score',
                'selector': '',
                'url': '',
                'variable': self.open_critics_score
            },
            {
                'attribute': 'open_user_score',
                'selector': '',
                'url': '',
                'variable': self.open_user_score
            }
        ]

        self.fill_all_metadata()

    def _verify_title(self) -> str:
        """Verifies and corrects the given title on Wikipedia."""
        # Search for the game with the given title on Wikipedia.
        # Check if the game exists with the title
        # if it doesn't exist, raise an error
        # if the game exists but the title is not accurate
        # find and put the correct name into `self.title`
        # return complete_name
        pass

    def _construct_url(self, title: str, url: str) -> str:
        """Constructs the URL for the given website for the game"""
        #complete_url = f'{url}/'
        #return complete_url
        pass

    def _parse_date(self) -> None:
        """Parses the date given as string into Date class"""
        pass


    def _extract_metadata(self, data_name: str, source_url: str) -> None:
        """Extract and store desired data by crawling the source URL."""
        pass

    def _fill_all_metadata(self) -> None:
        """Fills all the metadata"""

        # for source in self.metadata_sources:
        # _extract_metadata
        pass
    