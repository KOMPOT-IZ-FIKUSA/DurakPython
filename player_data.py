from dataclasses import dataclass


@dataclass
class GlobalPlayerData:
   id_: int
   name: str
   pw: int
   score: int
   avatar_link: str
