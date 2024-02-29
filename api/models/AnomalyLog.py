class AnomalyLog:
    def __init__(
        self,
        occurredAt=None,
        fromDevice=None,
        clipFileName=None,
        endedAt=None,
        fromCamera=None,
    ):
        self.occurredAt = occurredAt
        self.fromDevice = fromDevice
        self.clipFileName = clipFileName
        self.endedAt = endedAt
        self.fromCamera = fromCamera

    def reset(self):
        self.occurredAt = None
        self.fromDevice = None
        self.clipFileName = None
        self.endedAt = None
        self.fromCamera = None

    def clone(self):
        return AnomalyLog(
            occurredAt=self.occurredAt,
            fromDevice=self.fromDevice,
            clipFileName=self.clipFileName,
            endedAt=self.endedAt,
            fromCamera=self.fromCamera,
        )
