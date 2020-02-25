from dataclasses import dataclass
from typing import *

Pcr_date = NewType('Pcr_date', int)
Pcr_time = NewType('Pcr_time', int)
QQid = NewType('QQid', int)
Groupid = NewType('Groupid', int)


@dataclass
class BossStatus:
    cycle: int
    num: int
    health: int
    challenger: QQid
    info: str

    def __str__(self):
        summary = (
            f'现在{self.cycle}周目，{self.num}号boss\n'
            f'生命值{self.health}'
        )
        if self.challenger:
            summary += '\n' + f'{self.challenger}正在挑战boss'
        if self.info:
            summary = self.info + '\n' + summary
        return summary


@dataclass
class BossChallenge:
    date: Pcr_date
    time: Pcr_time
    cycle: int
    num: int
    health_ramain: int
    damage: int
    is_continue: bool
    team: Optional[List[int]]
    message: Optional[str]


ClanBattleReport = NewType(
    'ClanBattleReport',
    List[Dict[str, Any]]
)
