from dataclasses import dataclass
from typing import List, Union, Dict

from card_index import Index
from game_properties import GameProperties


@dataclass
class Attack:
    player_id: int
    card: Index


@dataclass
class Defence:
    player_id: int
    card_attack: Index
    card_defence: Index


@dataclass
class Redirect:
    redirecting_player: int  # primary victim
    card: Index


@dataclass
class TakeFromDeckOrder:
    players_ids: List[int]


@dataclass
class Hand:
    cards: List[Index]


@dataclass
class GameStart:
    pass


@dataclass
class SetModes:
    modes: dict


@dataclass
class SetTrumpCard:
    trump: Index


@dataclass
class SetTrumpSuit:
    trump: int


@dataclass
class SwapPlayers:
    player_id1: int
    player_id2: int


@dataclass
class EndTurn:
    taking_player_id: int


@dataclass
class AttackCanceled:
    card: Index


@dataclass
class RedirectCanceled:
    card: Index


@dataclass
class DefenceCanceled:
    card_attack: Index
    card_defence: Index


@dataclass
class ShaperBack:
    cards_to_players: Dict[Index, int]


class GameReset:
    pass


@dataclass
class SetGameProperties:
    properties: GameProperties
