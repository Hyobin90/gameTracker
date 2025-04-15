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
    COMING_SOON = 'coming soon' # GTPS-010 Allow the user to define the sense of how soon
    # PREORDER_AVAILABLE = 'pre-order available' # TODO Find out if it's to be retrieved from PSN update
    PREORDERED = 'pre-oredered'
    RELEASED = 'released'
    PURCHASED = 'purchased'
    PLAYING = 'currently playing'
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
    def __init__(self, title:str, game_id:str, aliases: str, wikidata_code: str, is_DLC: int, parent_id: str,
                 genres: str, developers: str, publishers: str, release_id: str, release_date: datetime,
                 released: int, platforms: str, **kwargs):
        # Necessary data on the game
        self.title = title
        self.game_id = game_id
        self.aliases = aliases.split(', ')
        self.wikidata_code = wikidata_code
        self.is_dlc = True if is_DLC else False
        self.parent_id = parent_id
        self.genres = genres.split(', ')
        self.developers = developers.split(', ')
        self.publishers = publishers.split(', ')
        self.release_id = release_id
        self.release_date = release_date.strftime('%Y-%m-%d')
        self.released = True if released else False
        self.platforms = platforms.split(', ')
        # self.regions

        #self.my_score = 0

        # Data to be filled after playing
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

        # Attributes to be updated per user, stored in their DB, not stored in game_db
        # self.purchase_date = None # this is not stored in game_db
        # self.purchased = None
        # self.playing = None
        # self.played = None
        # self.status: Status = None


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
    

    def set_game_active(self) ->  None:
        """Set the game currently playing."""
        if self.purchased:
            self.playing = True
            self.played = True
            self.update_status()


    def set_game_inactive(self) -> None:
        """Set the game paused."""
        if self.purchased and self.playing:
            self.playing = False
            self.update_status()


    # TODO maybe not needed
    def _fill_metadata_from_wikidata(self, wikidata:Dict[str, str]):
        """Fills up the metadata from `Wikidata` """
        try:
            self.wikipedia_link = wikidata.get('wikipedia_link')
            self.wikidata_link = wikidata.get('wikidata_link')
            self.genres = wikidata.get('genres')
            self.developers = wikidata.get('developers')
            self.publishers = wikidata.get('publishers')
            self.release_date = datetime.strptime(wikidata.get('release_date')[:10], '%Y-%m-%d') if isinstance(wikidata.get('release_date'), str) else None
            self.released = self._is_released()
            self.platforms = wikidata.get('platforms') # TODO allow to select the platform
        except Exception as e:
            print(f'Error occurred while filling metadata | {e}')
            # TODO specify error types case by case
        #self.logo = wikidata.get('logo') # TODO handle the logo image


    def _is_released(self) -> bool:
        """Verifies whether a game has been released."""
        # TODO this should be called each time the game is requested
        current_date = datetime.today()
        released = None
        # In case the release date hasn't been announced yet.
        if not self.release_date:
            released = False
        elif self.release_date:
            if self.release_date <= current_date:
                released = True
            else:
                released = False
        self.update_status()
        return released


    def _calculate_days_till_release(self) -> int:
        """Verifies if the game will be released soon."""
        if not self.release_date:
            raise RuntimeError('Even no release date has been announced.')
        else:
            current_date = datetime.today()
            return (self.release_date - current_date).days
        


    def set_purchase(self) -> None:
        """Sets the purchase date and purchase related status."""
        # TODO this should be called by the client
        # TODO this can be called when the game is purchased before or after released.
        while True:
            purchase_date = input('Please put the date of purchase in the following format, yyyy-mm-dd.\nPlease enter 0, if you haven\'t purchased the game yet.\n')
            if purchase_date == '0':
                self.purchased = False
                break
            elif _validate_date_format(purchase_date):
                self.purchase_date = datetime.strptime(purchase_date, '%Y-%m-%d')
                self.purchased = True
                break
            else:
                print(f'Wrong date format: {purchase_date}')
                continue
        self.update_status()



    # TODO this should be called by the client
    def set_play_platform(self) -> None:
        """Sets the play platform."""
        # TODO this can be called each time the user wants to change the value.
        while True:
            play_platform = input('Please put the device you play this game on between PS4 and PS5.\n')
            if play_platform not in Platform:
                print(f'Wrong platform: {play_platform}')
                continue
            break
        self.play_platform = Platform(play_platform)

    # TODO this should be called by the client
    def set_expectation(self) -> None:
        """Sets the user expectation on the game."""
        # TODO this can be called each time the user wants to change the value.
        while True:
            try:
                expectation = int(input('Please put your expectation on this game from 0 to 3, the higher, the more hyped.\n'))
                if (expectation > 3) or (expectation < 0):
                    print(f'Invalid value for the expectation: {expectation}')
                    continue
                break
            except ValueError:
                print(f'Please enter a valid integer.')
                continue
        self.expectaion = Expectation(int(expectation)).value


    # TODO this should be called by the client
    def fill_post_playing_data(self):
        """Fills up certain data after playing"""
        pass
        # self.goals = {}
        # self.note = ''
        # self.my_score = 0


    # TODO this should be called by the client
    def fill_meta_score(self):
        """Retrieve critics score and user score from `Metacritic`"""
        pass
        # self.play_platform # it will be needed for `Metacritic`
        # self.meta_critics_score = 0
        # self.meta_user_score = 0


    # TODO this should be called by the client
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