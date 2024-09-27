import logging
import re
import traceback
from collections import namedtuple
from dataclasses import dataclass, field
from enum import Enum

from exceptions import SigurModelMismatch


@dataclass
class SigurResponse:
    """Common class for OIF responses"""

    raw_line: str
    regex: str
    model: type
    data: namedtuple = field(init=False)

    def __post_init__(self):
        self.parse()

    def parse(self) -> namedtuple:
        try:
            m = re.search(self.regex, self.raw_line)
            if not m:
                raise SigurModelMismatch(self.__class__, self.raw_line)
            self.data = self.model(**m.groupdict())
        except (TypeError, AttributeError):
            raise SigurModelMismatch(self.__class__, self.raw_line)
        except Exception:
            logging.error(traceback.format_exc())
            raise


@dataclass
class SigurExceptionModel(SigurResponse):
    """
    `SigurExceptionModel.data`:
        `id`: Exception number
        `text`: Exception description
    """

    regex: str = "ERROR (?P<id>(.*?)) (?P<text>(.*?))"
    model: type = namedtuple("ERROR", "id, text")


@dataclass
class ObjectInfoEmp(SigurResponse):
    """
    `ObjectInfoEmp.data`:
        `id`: Object ID
        `name`: Employee's full name
        `position`: Employee's position
        `tabnumber`: Employee's table number
    """

    prefix: str = "EMP"
    regex: str = (
        f'{prefix} ID (?P<id>(.*?)) NAME "(?P<name>(.*))" '
        'POSITION "(?P<position>(.*))" TABNUMBER "(?P<tabnumber>(.*?))"'
    )
    model: type = namedtuple("OBJECTINFO", "id, name, position, tabnumber")

    def __str__(self) -> str:
        return (
            "Сотрудник:\r\n\t"
            f"ID: {self.data.id}\r\n\t"
            f"Имя: {self.data.name}\r\n\t"
            f"Должность: {self.data.position}\r\n\t"
            f"Табельный номер: {self.data.tabnumber}"
        )


@dataclass
class ObjectInfoGuest(SigurResponse):
    """
    `ObjectInfoGuest.data`:
        `id`: Object ID
        `name`: Guest's full name
        `tabnumber`: Guest's table number
    """

    prefix: str = "GUESTBADGE"
    # regex MUST start with 'GUESTBADGE ID' despite the 'GUEST ID' in the documentation
    regex: str = (
        f'{prefix} ID (?P<id>(.*?)) NAME "(?P<name>(.*))" '
        'TABNUMBER "(?P<tabnumber>(.*?))"'
    )
    model: type = namedtuple("OBJECTINFO", "id, name, tabnumber")

    def __str__(self) -> str:
        return (
            "Гость:\r\n\t"
            f"ID: {self.data.id}\r\n\t"
            f"Имя: {self.data.name}\r\n\t"
            f"Табельный номер: {self.data.tabnumber}"
        )


@dataclass
class ObjectInfoCar(SigurResponse):
    """
    `ObjectInfoCar.data`:
        `id`: Object ID
        `car_number`: Car number
        `car_model`: Car model
        `tabnumber`: Car table number
    """

    prefix: str = "CAR"
    # regex MUST have two spaces before 'MODEL' despite the documentation
    regex: str = (
        f'{prefix} ID (?P<id>(.*?)) NUMBER "(?P<car_number>(.*))"  '
        'MODEL "(?P<car_model>(.*?))" TABNUMBER "(?P<tabnumber>(.*?))"'
    )
    model: type = namedtuple("OBJECTINFO", "id, car_number, car_model, tabnumber")

    def __str__(self) -> str:
        return (
            "Автомобиль:\r\n\t"
            f"ID: {self.data.id}\r\n\t"
            f"Номер: {self.data.car_number}\r\n\t"
            f"Модель: {self.data.car_model}\r\n\t"
            f"Табельный номер: {self.data.tabnumber}"
        )


@dataclass
class ZoneInfo(SigurResponse):
    """
    `ZoneInfo.data`:
        `id`: Zone ID
        `name`: Zone name
    """

    regex: str = 'ID (?P<id>(.*?)) NAME "(?P<name>(.*))"'
    model: type = namedtuple("ZONEINFO", "id, name")

    def __str__(self) -> str:
        return (
            "Зона:\r\n\t"
            f"ID: {self.data.id}\r\n\t"
            f"Название: {self.data.name}\r\n\t"
        )


class APStates(Enum):
    OFFLINE = "Нет связи"
    ONLINE_NORMAL = "Нормальный режим"
    ONLINE_UNLOCKED = "Разблокирована"
    ONLINE_LOCKED = "Заблокирована"

    OPENED = "Открыта"
    CLOSED = "Закрыта"


@dataclass
class APInfo(SigurResponse):
    """
    `APInfo.data`:
        `id`: Access Point ID
        `name`: Access Point name
        `zonea`: Zone A, exit zone
        `zoneb`: Zone B, entry zone
        `state_adm`: Administrative state, normal|locked|unlocked
        `state_phys`: Physical state, online|offline
    """

    regex: str = (
        'APINFO ID (?P<id>(.*?)) NAME "(?P<name>(.*))" ZONEA (?P<zonea>(.*?)) '
        "ZONEB (?P<zoneb>(.*?)) STATE (?P<state_adm>(.*?)) (?P<state_phys>(.*))"
    )
    model: type = namedtuple("APINFO", "id, name, zonea, zoneb, state_adm, state_phys")

    def __str__(self) -> str:
        return (
            "Точка прохода:\r\n\t"
            f"ID: {self.data.id}\r\n\t"
            f"Название: {self.data.name}\r\n\t"
            f"Зона выхода: {self.data.zonea}\r\n\t"
            f"Зона входа: {self.data.zoneb}\r\n\t"
            f"Состояние: {APStates[self.data.state_adm].value}\r\n\t"
            f"Состояние контроллера: {APStates[self.data.state_phys].value}\r\n\t"
        )


@dataclass
class W26Key(SigurResponse):
    """
    `W26Key.data`:
        `key_a`: 1-3 digits
        `key_b`: 1-5 digits
    Keys must be zero-padded from left if used in OIF, and separated with a space symbol.
    """

    regex: str = "(?P<key_a>(\\d{1,3})),(?P<key_b>(\\d{1,5}))"
    model: type = namedtuple("W26KEY", "key_a, key_b")

    def __str__(self) -> str:
        return f"W26 {self.data.key_a:03} {self.data.key_b:05}"


@dataclass
class W34Key(SigurResponse):
    """
    `W34Key.data`:
        `key`: 8 HEX digits
    """

    regex: str = "(?P<key>(([ABCDEF]|[0-9]){8}))"
    model: type = namedtuple("W34KEY", "key")

    def __str__(self) -> str:
        return f"W34 {self.data.key}"


class AccessPolicyReplyResults(Enum):
    """
    These are the same as DELEGATION_REQUEST reply codes
    """

    CODE_1 = "Срок действия идентификатора истёк"
    CODE_2 = "Система не может сейчас решить, что делать"
    CODE_3 = "Идентификатор не известен системе"
    CODE_4 = "Активный режим запрещает (без уточнения как)"
    CODE_5 = "Активный режим запрещает (по точке прохода)"
    CODE_6 = "Активный режим запрещает (по времени)"
    CODE_7 = "Пресечена попытка повторного прохода (antipassback)"
    CODE_255 = "Разрешить доступ"


@dataclass
class AccessPolicyReplyEmp(SigurResponse):
    """
    `AccessPolicyReplyEmp.data`:
        `result_id`: ACCESSPOLICY_REPLY ID
        `emp_id`: Employee ID

    Much unknown on this one.

    Is it always `EMPID` in reply? Documentation says so.

    What is `MASKVERPOLICY_OFF`? Unbeknownst, not mentioned in the documentation.
    """

    regex: str = "ACCESSPOLICY_REPLY RESULT (?P<result_id>(\\d{1,3})) EMPID (?P<emp_id>(\\d{1,5})) MASKVERPOLICY_OFF"
    model: type = namedtuple("ACCESSPOLISY_REPLY", "result_id, emp_id")

    def __str__(self) -> str:
        return f"Сотрудник {self.data.emp_id}, ответ - {AccessPolicyReplyResults["CODE_"+self.data.result_id].value}"


@dataclass
class AccessPolicyReplyNoEmp(SigurResponse):
    """
    `AccessPolicyReplyNoEmp.data`:
        `result_id`: ACCESSPOLICY_REPLY ID

    This is for when the provided key can not be associated with an employee
    """

    regex: str = "ACCESSPOLICY_REPLY RESULT (?P<result_id>(\\d{1,3})) MASKVERPOLICY_OFF"
    model: type = namedtuple("ACCESSPOLISY_REPLY", "result_id")

    def __str__(self) -> str:
        return f"Ответ - {AccessPolicyReplyResults["CODE_"+self.data.result_id].value}"
