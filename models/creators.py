from dataclasses import dataclass, field

from typing import List, Dict, Tuple


@dataclass
class Person:
    name: str
    name_eng: List[str] = field(default_factory=list)


def person_list_to_str(lst: List[Person]) -> List[str]:
    return [p.name for p in lst]


Staff = Tuple[str, List[Person]]

role_mapping = {
    "PLACEHOLDER": "词曲",
    "Composer": "作曲",
    "Lyricist": "作词",
    "Arranger": "编曲",
    "Arrange": "编曲",
    "VoiceManipulator": "调教",
    "Mixer": "混音",
    "Mastering": "母带处理",
    "Instrumentalist": "乐器演奏",
    "Illustrator": "曲绘",
    "Animator": "PV制作",
    "Animators": "PV制作",
    "Publisher": "出版社",
    "Vocalist": "演唱",
}


def role_transform(role: str) -> str:
    return role_mapping.get(role, role)


def role_priority(role: str) -> int:
    for index, value in enumerate(role_mapping.values()):
        if role == value:
            return index
    return len(role_mapping) // 2


@dataclass
class Creators:
    producers: List[Person]
    vocalists: List[Person]
    staffs: Dict[str, List[Person]]

    def producers_str(self) -> List[str]:
        return person_list_to_str(self.producers)

    def vocalists_str(self) -> List[str]:
        return person_list_to_str(self.vocalists)

    def staff_list(self) -> List[Staff]:
        return [(role, self.staffs[role]) for role in self.staffs]
