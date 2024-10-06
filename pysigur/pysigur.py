import asyncio
import logging
from datetime import datetime

from . import exceptions
from .models import (
    AccessPolicyReplyEmp,
    AccessPolicyReplyNoEmp,
    APInfo,
    ObjectInfoCar,
    ObjectInfoEmp,
    ObjectInfoGuest,
    SigurExceptionModel,
    SigurOK,
    SigurResponse,
    W26Key,
    W34Key,
    ZoneInfo,
)


class SigurAsyncService:
    """
    Asynchronous interface for client to Sigur Integrational Interface OIF.
    """

    def __init__(
        self,
        host: str,
        port: int = 3312,
    ) -> None:
        self._host: str = host
        self._port: int = port

        self._EOL: str = "\r\n"
        self._EOLbytes: bytes = b"\r\n"
        self._read_timeout: int = 3
        self._buffer_limit: int = 65536

    async def open_connection(self) -> None:
        self._reader, self._writer = await asyncio.open_connection(
            host=self._host, port=self._port, limit=self._buffer_limit
        )

    async def close_connection(self) -> None:
        self._writer.close()
        await self._writer.wait_closed()

    async def query(self, query: str) -> str:
        """
        Sends 'query' to the server, returns reply decoded as UTF-8
        """
        query_bytes = (query + self._EOL).encode("utf-8")
        self._writer.write(query_bytes)
        await self._writer.drain()
        data = await self.read_utf8()
        if data.startswith("ERROR"):
            error = SigurExceptionModel(data)
            raise exceptions.SigurException(str(error.data.id))
        return data

    async def readline(self) -> bytes:
        """
        Returns a bytearray read from the interface, ending with newline symbols
        """
        result = bytes()
        while True:
            try:
                data: bytes = await asyncio.wait_for(
                    self._reader.readuntil(self._EOLbytes), timeout=self._read_timeout
                )
                result += data
                break
            except asyncio.exceptions.LimitOverrunError as e:
                data: bytes = await self._reader.readexactly(e.consumed)  # type: ignore[no-redef]
                result += data
            except TimeoutError:
                raise exceptions.SigurTimeoutException
        return result

    async def read_utf8(self) -> str:
        """
        Returns a UTF-8 decoded string from the interface, newline symbols removed
        """
        line_bytes = await self.readline()
        return line_bytes.decode("utf-8").removesuffix(self._EOL)


class SigurAsyncClient:
    """
    Asynchronous client to Sigur Integrational Interface OIF.

    Current OIF version is 1.8, and it's the only supported.

    Client might be used in an async context manager via `async with`

    If used as an instance, you will have to call `open_connection()` and `login()` by hand
    """

    def __init__(
        self,
        host: str,
        port: int = 3312,
        username: str = "sys",
        password: str = "",
    ) -> None:
        self._username: str = username
        self._password: str = password

        self._version: str = "1.8"
        self._date_format: str = "%Y-%m-%d %H:%M:%S"
        self.service = SigurAsyncService(host=host, port=port)
        self.OK = "OK"

    async def __aenter__(self):
        await self.service.open_connection()
        if not await self.login():
            return None
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.service.close_connection()

    async def login(self) -> bool:
        try:
            SigurOK(
                await self.service.query(
                    f"LOGIN {self._version} {self._username} {self._password}"
                )
            )
        except exceptions.SigurModelMismatch as e:
            logging.error(e)
            return False
        return True

    async def quit(self) -> None:
        """
        Redundant, one can simply close connection
        """
        await self.service.query("QUIT")
        await self.service.close_connection()

    async def exit(self) -> None:
        """
        Alias for the redundant `quit()` method
        """
        await self.quit()

    def _match_object_info(self, string: str) -> SigurResponse | None:
        """
        This method helps differentiate between Employers, Guests and Cars

        OBJECTINFO types. They all have different models but come from the same list,

        having different prefixes. Hence the hustle.

        Returns ObjectInfoEmp | ObjectInfoGuest | ObjectInfoCar | None
        """
        prefixes = {
            "EMP": ObjectInfoEmp,
            "GUESTBADGE": ObjectInfoGuest,
            "CAR": ObjectInfoCar,
        }
        for prefix, obj in prefixes.items():
            if string.startswith(prefix):
                return obj(string)
        return None

    async def get_object_info(self, object_id: str | int) -> SigurResponse | None:
        reply = await self.service.query(f"GETOBJECTINFO OBJECTID {object_id}")
        if reply == "OBJECTINFO" or not reply.startswith("OBJECTINFO"):
            return None
        reply_modified = reply.removeprefix("OBJECTINFO ")
        if obj := self._match_object_info(reply_modified):
            return obj
        logging.error(exceptions.SigurModelMismatch(reply))
        return None

    async def get_object_info_all(self) -> list[SigurResponse] | None:
        reply = await self.service.query("GETOBJECTINFO ALL")
        if reply == "OBJECTINFO" or not reply.startswith("OBJECTINFO"):
            return None
        # here's how we fight against commas in names and positions
        reply_modified = (
            reply.removeprefix("OBJECTINFO ")
            .replace(", EMP ", ",,EMP ")
            .replace(", GUESTBADGE ", ",,GUESTBADGE ")
            .replace(", CAR ", ",,CAR ")
        )
        replies_list = reply_modified.split(",,")
        objects = list()
        for object_item in replies_list:
            if obj := self._match_object_info(object_item):
                objects.append(obj)
            else:
                logging.error(exceptions.SigurModelMismatch(object_item))
        return objects

    async def get_zone_info(self) -> list[ZoneInfo] | None:
        reply = await self.service.query("GETZONEINFO")
        if reply == "ZONEINFO" or not reply.startswith("ZONEINFO"):
            return None
        reply_modified = reply.removeprefix("ZONEINFO ")
        replies_list = reply_modified.split(", ")
        zones = list()
        for zone_item in replies_list:
            if zone := ZoneInfo(zone_item):
                zones.append(zone)
            else:
                logging.error(exceptions.SigurModelMismatch(zone_item))
        return zones

    async def get_ap_info(self, ap_id: str | int) -> APInfo | None:
        reply = await self.service.query(f"GETAPINFO {ap_id}")
        if reply == "APINFO" or not reply.startswith("APINFO"):
            return None
        if ap := APInfo(reply):
            return ap
        logging.error(exceptions.SigurModelMismatch(reply))
        return None

    async def get_ap_list(self) -> dict[int, APInfo] | None:
        """
        This method gets all the Access Points info, as opposed to API's

        `GETAPLIST` which only retrieves list of AP's numbers.

        Returns a `dict{ap_id: APInfo}`
        """
        reply = await self.service.query("GETAPLIST")
        if reply == "APLIST EMPTY" or not reply.startswith("APLIST"):
            return None
        reply_modified = reply.removeprefix("APLIST ")
        ap_ids_list = reply_modified.split(" ")
        ap_list = dict()
        for ap_id in ap_ids_list:
            if ap := await self.get_ap_info(ap_id):
                ap_list[int(ap_id)] = ap
            else:
                logging.error(exceptions.SigurModelMismatch("AP#" + ap_id))
        return ap_list

    async def accesspolicy_request(
        self,
        ap_id: str | int,
        object_id: str | int | None = None,
        key: W26Key | W34Key | None = None,
        lpnumber: str | None = None,
        date_time: datetime | None = None,
        direction: str = "X",
        extra_rules: dict | None = None,
    ) -> AccessPolicyReplyEmp | AccessPolicyReplyNoEmp | None:
        """
        Requests the server if a user can pass through an access point.

        `ap_id`: required, Access Point ID.

        `object_id`, `key`, `lpnumber`: optional, but must provide one of these.

            `object_id`: person's ID.

            `key`: instance of models.W26Key or models.W34Key.

            `lpnumber`: car number, maybe? Documentation tells nothing.

        `date_time`: optional; the time when a user is allowed to pass through. Defaults to `datetime.now()`. Datetime format is "%Y-%m-%d %H:%M:%S".

        `direction`: optional; allowed values are `IN`, `OUT`, and `X` - 'unknown'. Default is `X`.

        `extra_rules`: optional; a `dict` with some extra arguments. Look them up in the OIF document.
        """
        if not (lpnumber or key or object_id):
            logging.error(exceptions.E_7_UNKNOWN_OBJECT)
            return None

        query_object = str()
        if lpnumber:
            query_object = f"LPNUMBER {str(lpnumber)}"
        if key:
            query_object = f"KEY {str(key)}"
        if object_id:
            query_object = f"EMPID {str(object_id)}"
        if not date_time:
            date_time = datetime.now()
        if direction not in ["IN", "OUT", "X"]:
            direction = "X"

        query = (
            f'ACCESSPOLICY_REQUEST TYPE NORMAL TIME "{date_time.strftime(self._date_format)}" {query_object} '  # type: ignore[union-attr]
            f'DIRECTION {direction} APID {ap_id}{str(" " + str(extra_rules)) if extra_rules else ""}'
        )
        reply = await self.service.query(query)
        try:
            if accesspolicy_reply := AccessPolicyReplyEmp(reply):
                return accesspolicy_reply
        except exceptions.SigurModelMismatch:
            if accesspolicy_reply_noemp := AccessPolicyReplyNoEmp(reply):
                return accesspolicy_reply_noemp
        logging.error(exceptions.SigurModelMismatch(reply))
        return None

    async def accesspolicy_request_obj(
        self,
        ap_id: str | int,
        object_id: str | int,
        date_time: datetime | None = None,
        extra_rules: dict | None = None,
    ) -> AccessPolicyReplyEmp | AccessPolicyReplyNoEmp | None:
        """
        Simplified alias for `accesspolicy_request` method for Wiegand26 formatted keys.

        `ap_id`: required, Access Point ID.

        `object_id`: person's ID.

        `date_time`: optional; the time when a user is allowed to pass through. Defaults to `datetime.now()`. Datetime format is "%Y-%m-%d %H:%M:%S".

        `extra_rules`: optional; a `dict` with some extra arguments. Look them up in the OIF document.
        """
        return await self.accesspolicy_request(
            ap_id=ap_id,
            object_id=str(object_id),
            date_time=date_time,
            extra_rules=extra_rules,
        )

    async def accesspolicy_request_w26(
        self,
        ap_id: str | int,
        key: str,
        date_time: datetime | None = None,
        extra_rules: dict | None = None,
    ) -> AccessPolicyReplyEmp | AccessPolicyReplyNoEmp | None:
        """
        Simplified alias for `accesspolicy_request` method for Wiegand26 formatted keys.

        `ap_id`: required, Access Point ID.

        `key`: Wiegand26 string format `xxx,yyyyy`

        `date_time`: optional; the time when a user is allowed to pass through. Defaults to `datetime.now()`. Datetime format is "%Y-%m-%d %H:%M:%S".

        `extra_rules`: optional; a `dict` with some extra arguments. Look them up in the OIF document.
        """
        w26_key = W26Key(key)
        return await self.accesspolicy_request(
            ap_id=ap_id, key=w26_key, date_time=date_time, extra_rules=extra_rules
        )

    async def accesspolicy_request_w34(
        self,
        ap_id: str | int,
        key: str,
        date_time: datetime | None = None,
        extra_rules: dict | None = None,
    ) -> AccessPolicyReplyEmp | AccessPolicyReplyNoEmp | None:
        """
        Simplified alias for `accesspolicy_request` method for Wiegand34 formatted keys.

        `ap_id`: required, Access Point ID.

        `key`: Wiegand26 string format `FFFFFF`

        `date_time`: optional; the time when a user is allowed to pass through. Defaults to `datetime.now()`. Datetime format is "%Y-%m-%d %H:%M:%S".

        `extra_rules`: optional; a `dict` with some extra arguments. Look them up in the OIF document.
        """
        w34_key = W34Key(key)
        return await self.accesspolicy_request(
            ap_id=ap_id, key=w34_key, date_time=date_time, extra_rules=extra_rules
        )
