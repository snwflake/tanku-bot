from enum import Enum


class Slot1(Enum):
    FreeXP = "MILITARY_MANEUVERS"
    CrewXP = "ADDITIONAL_BRIEFING"


class Slot2(Enum):
    Disabled = None
    Credits = "BATTLE_PAYMENTS"
    TankXP = "TACTICAL_TRAINING"
