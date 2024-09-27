from errors import SigurWrongModel


class SigurTimeoutException(Exception):
    def __init__(self) -> None:
        self.message = "Query was cancelled due to timeout. Try increasing timeout limit for longer queries."
        super().__init__(self.message)


class SigurModelMismatch(BaseException):
    def __init__(self, *args) -> None:
        super().__init__(SigurWrongModel(*args))


class SigurException(BaseException):
    def __init__(self, errno: str) -> None:
        ex = {
            "1": E_1_UNABLE_TO_CONNECT_TO_DB,
            "2": E_2_UNKNOWN_COMMAND,
            "3": E_3_UNSUPPORTED_INTERFACE_VERSION,
            "4": E_4_NOT_LOGGED_IN,
            "5": E_5_GENERIC_SQL_ERROR,
            "6": E_6_SYNTAX_ERROR,
            "7": E_7_UNKNOWN_OBJECT,
            "8": E_8_INTERNAL_ERROR,
            "9": E_9_CONCURRENT_TRANSACTION_IS_IN_PROGRESS,
            "10": E_10_UNKNOWN_ACCESS_POINT,
            "11": E_11_AUTHENTICATION_FAILED,
            "12": E_12_DELEGATION_IS_DISABLED,
            "13": E_13_DELEGATION_IS_NOT_ACTIVE,
            "14": E_14_NOT_SUBSCRIBED,
            "15": E_15_ALREADY_SUBSCRIBED,
            "16": E_16_SPECIFIED_KEY_ALREADY_IN_USE,
            "17": E_17_SPECIFIED_RULE_DOESNT_EXIST,
            "18": E_18_SPECIFIED_KEY_DOESNT_EXIST,
            "19": E_19_UNKNOWN_VIDEO_CHANNEL,
            "20": E_20_UNKNOWN_ALARM_LINE,
            "21": E_21_OIF_ACCESS_IS_DISABLED_FOR_THIS_USER,
            "22": E_22_VIDEO_IS_NOT_AVAILABLE,
            "23": E_23_STREAM_IS_NOT_OPENED,
            "24": E_24_FACE_RECOGNITION_IS_OFF,
            "25": E_25_ACCESS_POLICY_ERROR,
            "26": E_26_TIMED_OUT,
            "27": E_27_SOCKET_BIND_FAILED,
            "28": E_28_UNKNOWN_ERROR,
            "29": E_29_EXTMEM_ERROR,
        }[errno]
        raise ex


class E_1_UNABLE_TO_CONNECT_TO_DB(BaseException): ...


class E_2_UNKNOWN_COMMAND(BaseException): ...


class E_3_UNSUPPORTED_INTERFACE_VERSION(BaseException): ...


class E_4_NOT_LOGGED_IN(BaseException): ...


class E_5_GENERIC_SQL_ERROR(BaseException): ...


class E_6_SYNTAX_ERROR(BaseException): ...


class E_7_UNKNOWN_OBJECT(BaseException): ...


class E_8_INTERNAL_ERROR(BaseException): ...


class E_9_CONCURRENT_TRANSACTION_IS_IN_PROGRESS(BaseException): ...


class E_10_UNKNOWN_ACCESS_POINT(BaseException): ...


class E_11_AUTHENTICATION_FAILED(BaseException): ...


class E_12_DELEGATION_IS_DISABLED(BaseException): ...


class E_13_DELEGATION_IS_NOT_ACTIVE(BaseException): ...


class E_14_NOT_SUBSCRIBED(BaseException): ...


class E_15_ALREADY_SUBSCRIBED(BaseException): ...


class E_16_SPECIFIED_KEY_ALREADY_IN_USE(BaseException): ...


class E_17_SPECIFIED_RULE_DOESNT_EXIST(BaseException): ...


class E_18_SPECIFIED_KEY_DOESNT_EXIST(BaseException): ...


class E_19_UNKNOWN_VIDEO_CHANNEL(BaseException): ...


class E_20_UNKNOWN_ALARM_LINE(BaseException): ...


class E_21_OIF_ACCESS_IS_DISABLED_FOR_THIS_USER(BaseException): ...


class E_22_VIDEO_IS_NOT_AVAILABLE(BaseException): ...


class E_23_STREAM_IS_NOT_OPENED(BaseException): ...


class E_24_FACE_RECOGNITION_IS_OFF(BaseException): ...


class E_25_ACCESS_POLICY_ERROR(BaseException): ...


class E_26_TIMED_OUT(BaseException): ...


class E_27_SOCKET_BIND_FAILED(BaseException): ...


class E_28_UNKNOWN_ERROR(BaseException): ...


class E_29_EXTMEM_ERROR(BaseException): ...
