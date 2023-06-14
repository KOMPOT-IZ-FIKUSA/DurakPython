from dataclasses import dataclass


@dataclass
class GameProperties:
    redirect: bool
    secondary_attack_sides_only: bool
    shapers: bool
    draw: bool
    fast: bool
    players_count: int
    lowest_card_rank: int
    bet: int
    self_position: int

