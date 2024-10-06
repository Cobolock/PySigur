import logging
import re
import traceback
from dataclasses import dataclass, field
from enum import StrEnum

from .exceptions import SigurModelMismatch


@dataclass
class SigurResponse:
    """Common class for OIF responses"""

    @dataclass
    class Model:
        pass

    _raw_line: str
    _regex: str
    _model: type
    data: Model = field(init=False)

    def __post_init__(self):
        self.parse()

    def parse(self) -> None:
        try:
            m = re.search(self._regex, self._raw_line)
            if not m:
                raise SigurModelMismatch(self.__class__, self._raw_line)
            self.data = self._model(**m.groupdict())
        except (TypeError, AttributeError):
            raise SigurModelMismatch(self.__class__, self._raw_line)
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

    @dataclass
    class Model:
        id: int = 0
        text: str = ""

    _regex: re.Pattern = re.compile("ERROR (?P<id>(.*?)) (?P<text>(.*?))")
    _model: type = Model
    data: Model = field(default_factory=Model)


@dataclass
class SigurOK(SigurResponse):
    """
    `SigurOK.data`:
        `ok`: it's always "OK" in Sigur
    """

    @dataclass
    class Model:
        ok: str = ""

    _regex: re.Pattern = re.compile("(?P<ok>(OK))")
    _model: type = Model
    data: Model = field(default_factory=Model)


@dataclass
class ObjectInfoEmp(SigurResponse):
    """
    `ObjectInfoEmp.data`:
        `id`: Object ID
        `name`: Employee's full name
        `position`: Employee's position
        `tabnumber`: Employee's table number
    """

    @dataclass
    class Model:
        id: int = 0
        name: str = ""
        position: str = ""
        tabnumber: str = ""

    _regex: re.Pattern = re.compile(
        'EMP ID (?P<id>(.*?)) NAME "(?P<name>(.*))" '
        'POSITION "(?P<position>(.*))" TABNUMBER "(?P<tabnumber>(.*?))"'
    )
    _model: type = Model
    data: Model = field(default_factory=Model)

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

    @dataclass
    class Model:
        id: int = 0
        name: str = ""
        tabnumber: str = ""

    # _regex MUST start with 'GUESTBADGE ID' despite the 'GUEST ID' in the documentation
    _regex: re.Pattern = re.compile(
        'GUESTBADGE ID (?P<id>(.*?)) NAME "(?P<name>(.*))" '
        'TABNUMBER "(?P<tabnumber>(.*?))"'
    )
    _model: type = Model
    data: Model = field(default_factory=Model)

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
        `car__model`: Car _model
        `tabnumber`: Car table number
    """

    @dataclass
    class Model:
        id: int = 0
        car_number: str = ""
        car_model: str = ""
        tabnumber: str = ""

    # _regex MUST have two spaces before 'MODEL' despite the documentation
    _regex: re.Pattern = re.compile(
        'CAR ID (?P<id>(.*?)) NUMBER "(?P<car_number>(.*))"  '
        'MODEL "(?P<car_model>(.*?))" TABNUMBER "(?P<tabnumber>(.*?))"'
    )
    _model: type = Model
    data: Model = field(default_factory=Model)

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

    @dataclass
    class Model:
        id: int = 0
        name: str = ""

    _regex: re.Pattern = re.compile('ID (?P<id>(.*?)) NAME "(?P<name>(.*))"')
    _model: type = Model
    data: Model = field(default_factory=Model)

    def __str__(self) -> str:
        return (
            "Зона:\r\n\t"
            f"ID: {self.data.id}\r\n\t"
            f"Название: {self.data.name}\r\n\t"
        )


class APStates(StrEnum):
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

    @dataclass
    class Model:
        id: int = 0
        name: str = ""
        zonea: int = 0
        zoneb: int = 0
        state_adm: str = ""
        state_phys: str = ""

    _model: type = Model
    _regex: re.Pattern = re.compile(
        'APINFO ID (?P<id>(.*?)) NAME "(?P<name>(.*))" ZONEA (?P<zonea>(.*?)) '
        "ZONEB (?P<zoneb>(.*?)) STATE (?P<state_adm>(.*?)) (?P<state_phys>(.*))"
    )
    data: Model = field(default_factory=Model)

    def __str__(self) -> str:
        return (
            "Точка прохода:\r\n\t"
            f"ID: {self.data.id}\r\n\t"
            f"Название: {self.data.name}\r\n\t"
            f"Зона выхода: {self.data.zonea}\r\n\t"
            f"Зона входа: {self.data.zoneb}\r\n\t"
            f"Состояние: {APStates[self.data.state_adm]}\r\n\t"
            f"Состояние контроллера: {APStates[self.data.state_phys]}\r\n\t"
        )


@dataclass
class W26Key(SigurResponse):
    """
    `W26Key.data`:
        `key_a`: 1-3 digits
        `key_b`: 1-5 digits
    Keys must be zero-padded from left if used in OIF, and separated with a space symbol.
    """

    @dataclass
    class Model:
        key_a: str = ""
        key_b: str = ""

    _regex: re.Pattern = re.compile("(?P<key_a>(\\d{1,3})),(?P<key_b>(\\d{1,5}))")
    _model: type = Model
    data: Model = field(default_factory=Model)

    def __str__(self) -> str:
        return f"W26 {self.data.key_a:03} {self.data.key_b:05}"


@dataclass
class W34Key(SigurResponse):
    """
    `W34Key.data`:
        `key`: 8 HEX digits
    """

    @dataclass
    class Model:
        key: str = ""

    _regex: re.Pattern = re.compile("(?P<key>(([ABCDEF]|[0-9]){8}))")
    _model: type = Model
    data: Model = field(default_factory=Model)

    def __str__(self) -> str:
        return f"W34 {self.data.key}"


class AccessPolicyReplyResults(StrEnum):
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

    @dataclass
    class Model:
        result_id: int = 0
        emp_id: int = 0

    _regex: re.Pattern = re.compile("ACCESSPOLICY_REPLY RESULT (?P<result_id>(\\d{1,3})) EMPID (?P<emp_id>(\\d{1,5})) MASKVERPOLICY_OFF")
    _model: type = Model
    data: Model = field(default_factory=Model)

    def __str__(self) -> str:
        return f"Сотрудник {self.data.emp_id}, ответ - {AccessPolicyReplyResults["CODE_"+str(self.data.result_id)]}"


@dataclass
class AccessPolicyReplyNoEmp(SigurResponse):
    """
    `AccessPolicyReplyNoEmp.data`:
        `result_id`: ACCESSPOLICY_REPLY ID

    This is for when the provided key can not be associated with an employee
    """

    @dataclass
    class Model:
        result_id: int = 0

    _regex: re.Pattern = re.compile(
        "ACCESSPOLICY_REPLY RESULT (?P<result_id>(\\d{1,3})) MASKVERPOLICY_OFF"
    )
    _model: type = Model
    data: Model = field(default_factory=Model)

    def __str__(self) -> str:
        return f"Ответ - {AccessPolicyReplyResults["CODE_"+str(self.data.result_id)]}"
