class SigurBaseException(BaseException):
    pass


class SigurTimeoutException(SigurBaseException):
    def __init__(self) -> None:
        self.message = "Query was cancelled due to timeout. Try increasing timeout limit for longer queries."
        super().__init__(self.message)


class SigurModelMismatch(SigurBaseException):
    def __init__(self, *args) -> None:
        self.message = "Incorrect model."
        super().__init__(self.message, ", ".join([str(arg) for arg in args]))


class SigurException(SigurBaseException):
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


class E_1_UNABLE_TO_CONNECT_TO_DB(SigurBaseException):
    pass


class E_2_UNKNOWN_COMMAND(SigurBaseException):
    pass


class E_3_UNSUPPORTED_INTERFACE_VERSION(SigurBaseException):
    pass


class E_4_NOT_LOGGED_IN(SigurBaseException):
    pass


class E_5_GENERIC_SQL_ERROR(SigurBaseException):
    pass


class E_6_SYNTAX_ERROR(SigurBaseException):
    pass


class E_7_UNKNOWN_OBJECT(SigurBaseException):
    pass


class E_8_INTERNAL_ERROR(SigurBaseException):
    pass


class E_9_CONCURRENT_TRANSACTION_IS_IN_PROGRESS(SigurBaseException):
    pass


class E_10_UNKNOWN_ACCESS_POINT(SigurBaseException):
    pass


class E_11_AUTHENTICATION_FAILED(SigurBaseException):
    pass


class E_12_DELEGATION_IS_DISABLED(SigurBaseException):
    pass


class E_13_DELEGATION_IS_NOT_ACTIVE(SigurBaseException):
    pass


class E_14_NOT_SUBSCRIBED(SigurBaseException):
    pass


class E_15_ALREADY_SUBSCRIBED(SigurBaseException):
    pass


class E_16_SPECIFIED_KEY_ALREADY_IN_USE(SigurBaseException):
    pass


class E_17_SPECIFIED_RULE_DOESNT_EXIST(SigurBaseException):
    pass


class E_18_SPECIFIED_KEY_DOESNT_EXIST(SigurBaseException):
    pass


class E_19_UNKNOWN_VIDEO_CHANNEL(SigurBaseException):
    pass


class E_20_UNKNOWN_ALARM_LINE(SigurBaseException):
    pass


class E_21_OIF_ACCESS_IS_DISABLED_FOR_THIS_USER(SigurBaseException):
    pass


class E_22_VIDEO_IS_NOT_AVAILABLE(SigurBaseException):
    pass


class E_23_STREAM_IS_NOT_OPENED(SigurBaseException):
    pass


class E_24_FACE_RECOGNITION_IS_OFF(SigurBaseException):
    pass


class E_25_ACCESS_POLICY_ERROR(SigurBaseException):
    pass


class E_26_TIMED_OUT(SigurBaseException):
    pass


class E_27_SOCKET_BIND_FAILED(SigurBaseException):
    pass


class E_28_UNKNOWN_ERROR(SigurBaseException):
    pass


class E_29_EXTMEM_ERROR(SigurBaseException):
    pass
