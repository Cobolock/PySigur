import asyncio
import logging
from datetime import datetime

import exceptions as ex
from models import (
    AccessPolicyReplyEmp,
    AccessPolicyReplyNoEmp,
    APInfo,
    ObjectInfoCar,
    ObjectInfoEmp,
    ObjectInfoGuest,
    SigurExceptionModel,
    SigurResponse,
    W26Key,
    W34Key,
    ZoneInfo,
)

from .errors import SigurWrongModel


class SigurAsyncInterface:
    """
    Asynchronous interface for client to Sigur Integrational Interface OIF.
    """

    def __init__(self, host: str, port: int = 3312) -> None:
        self._host: str = host
        self._port: int = port

        self._EOL: str = "\r\n"
        self._EOLbytes: bytes = b"\r\n"
        self._read_timeout: int = 3
        self._buffer_limit: int = 65536

        self.exceptions = ex

    async def open_connection(self) -> None:
        self._reader, self._writer = await asyncio.open_connection(
            host=self._host, port=self._port, limit=self._buffer_limit
        )

    async def close_connection(self) -> None:
        self._writer.close()
        await self._writer.wait_closed()

    async def __aenter__(self):
        await self.open_connection()
        if not await self.login():
            return None
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close_connection()

    async def request(self, query: str, expected_reply="") -> bool:
        """
        Request is a query that expects a reply, most commonly 'OK',

        which is conveniently predefined as the 'OK' parameter of the Client class.

        Client's 'login' method is a request.
        """
        data = await self.query(query)
        return data == expected_reply

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
            raise self.exceptions.SigurException(error.data.id)
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
                raise self.exceptions.SigurTimeoutException
        return result

    async def read_utf8(self) -> str:
        """
        Returns a UTF-8 decoded string from the interface, newline symbols removed
        """
        line_bytes = await self.readline()
        return line_bytes.decode("utf-8").removesuffix(self._EOL)


class SigurAsyncClient(SigurAsyncInterface):
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
        super().__init__(host, port)
        self._username: str = username
        self._password: str = password

        self._version: str = "1.8"
        self._date_format: str = "%Y-%m-%d %H:%M:%S"
        self.OK = "OK"

    async def login(self) -> bool:
        return await self.request(
            f"LOGIN {self._version} {self._username} {self._password}", self.OK
        )

    async def quit(self) -> None:
        """
        Redundant, one can simply close connection
        """
        await self.query("QUIT")
        await self.close_connection()

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
            ObjectInfoEmp.prefix: ObjectInfoEmp,
            ObjectInfoGuest.prefix: ObjectInfoGuest,
            ObjectInfoCar.prefix: ObjectInfoCar,
        }
        for prefix, obj in prefixes.items():
            if string.startswith(prefix):
                return obj(string)
        return None

    async def get_object_info(self, object_id: str | int) -> SigurResponse | None:
        reply = await self.query(f"GETOBJECTINFO OBJECTID {object_id}")
        if reply == "OBJECTINFO" or not reply.startswith("OBJECTINFO"):
            return None
        reply_modified = reply.removeprefix("OBJECTINFO ")
        if obj := self._match_object_info(reply_modified):
            return obj
        logging.error(SigurWrongModel(reply))
        return None

    async def get_object_info_all(self) -> list[SigurResponse] | None:
        reply = await self.query("GETOBJECTINFO ALL")
        if reply == "OBJECTINFO" or not reply.startswith("OBJECTINFO"):
            return None
        # here's how we fight against commas in names and positions
        reply_modified = (
            reply.removeprefix("OBJECTINFO ")
            .replace(f", {ObjectInfoEmp.prefix} ", f"_!_{ObjectInfoEmp.prefix} ")
            .replace(f", {ObjectInfoGuest.prefix} ", f"_!_{ObjectInfoGuest.prefix} ")
            .replace(f", {ObjectInfoCar.prefix} ", f"_!_{ObjectInfoCar.prefix} ")
        )
        replies_list = reply_modified.split("_!_")
        objects = list()
        for object_item in replies_list:
            if obj := self._match_object_info(object_item):
                objects.append(obj)
            else:
                logging.error(SigurWrongModel(object_item))
        return objects

    async def get_zone_info(self) -> list[ZoneInfo] | None:
        reply = await self.query("GETZONEINFO")
        if reply == "ZONEINFO" or not reply.startswith("ZONEINFO"):
            return None
        reply_modified = reply.removeprefix("ZONEINFO ")
        replies_list = reply_modified.split(", ")
        zones = list()
        for zone_item in replies_list:
            if zone := ZoneInfo(zone_item):
                zones.append(zone)
            else:
                logging.error(SigurWrongModel(zone_item))
        return zones

    async def get_ap_info(self, ap_id: str | int) -> APInfo | None:
        reply = await self.query(f"GETAPINFO {ap_id}")
        if reply == "APINFO" or not reply.startswith("APINFO"):
            return None
        if ap := APInfo(reply):
            return ap
        logging.error(SigurWrongModel(reply))
        return None

    async def get_ap_list(self) -> dict[int, APInfo] | None:
        """
        This method gets all the Access Points info, as opposed to API's

        `GETAPLIST` which only retrieves list of AP's numbers.

        Returns a `dict{ap_id: APInfo}`
        """
        reply = await self.query("GETAPLIST")
        if reply == "APLIST EMPTY" or not reply.startswith("APLIST"):
            return None
        reply_modified = reply.removeprefix("APLIST ")
        ap_ids_list = reply_modified.split(" ")
        ap_list = dict()
        for ap_id in ap_ids_list:
            if ap := await self.get_ap_info(ap_id):
                ap_list[int(ap_id)] = ap
            else:
                logging.error(SigurWrongModel("AP#" + ap_id))
        return ap_list

    async def accesspolicy_request(
        self,
        ap_id: str | int,
        object_id: str | int | None = None,
        key: str | None = None,
        lpnumber: str | None = None,
        date_time: str | datetime = datetime.now(),
        direction: str = "X",
        extra_rules: dict | None = None,
    ) -> AccessPolicyReplyEmp | None:
        """
        Requests the server if a user can pass through an access point.

        `ap_id`: required.

        `object_id`, `key`, `lpnumber`: optional, but must provide one of these.

            `object_id`: person's ID.

            `key`: `AABBCCDD` for W34 or `111,22222` for W26.

            `lpnumber`: car number, maybe? Documentation tells nothing.

        `date_time`: optional; the time when a user is allowed to pass through. Defaults to `datetime.now()`. Datetime format is "%Y-%m-%d %H:%M:%S".

        `direction`: optional; allowed values are `IN`, `OUT`, and `X` - 'unknown'. Default is `X`.

        `extra_rules`: optional; a `dict` with some extra arguments. Look them up in the OIF document.
        """
        query_object = str()
        if lpnumber:
            query_object = f"LPNUMBER {str(lpnumber)}"
        if key:
            try:
                key = W26Key(key)
            except self.exceptions.SigurModelMismatch:
                try:
                    key = W34Key(key.upper())  # type: ignore[union-attr]
                except self.exceptions.SigurModelMismatch:
                    key = None
        if key:
            query_object = f"KEY {str(key)}"
        if object_id:
            query_object = f"EMPID {str(object_id)}"
        if direction not in ["IN", "OUT", "X"]:
            direction = "X"
        if type(date_time) is str:
            try:
                date_time = datetime.strptime(date_time, self._date_format)
            except ValueError:
                logging.error(
                    f"`date_time` value `{date_time}` does not comply with the format '%Y-%m-%d %H:%M:%S', `datetime.now()` used instead."
                )
                date_time = datetime.now()

        query = (
            f'ACCESSPOLICY_REQUEST TYPE NORMAL TIME "{date_time.strftime(self._date_format)}" {query_object} '  # type: ignore[union-attr]
            f'DIRECTION {direction} APID {ap_id}{str(" " + str(extra_rules)) if extra_rules else ""}'
        )
        reply = await self.query(query)
        try:
            if accesspolicy_reply := AccessPolicyReplyEmp(reply):
                return accesspolicy_reply
        except self.exceptions.SigurModelMismatch:
            if accesspolicy_reply := AccessPolicyReplyNoEmp(reply):
                return accesspolicy_reply
        logging.error(SigurWrongModel(reply))
        return None


if __name__ == "__main__":

    async def main():
        async with SigurAsyncClient(
            "10.0.7.232", 3312, username="script", password="ANONYMOUS"
        ) as sb:
            reply = await sb.accesspolicy_request(
                146,
                key="9693208A",
            )
            logging.error(reply)

    asyncio.run(main())
