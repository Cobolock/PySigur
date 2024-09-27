class SigurWrongModel:
    def __init__(self, *args) -> None:
        self.args = [str(arg) for arg in [*args]]

    def __str__(self) -> str:
        return f"Incorrect model format. {', '.join([*self.args])}"
