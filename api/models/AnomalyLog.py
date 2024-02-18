class AnomalyLog:
    def __init__(
        self, occurredAt=None, fromDevice=None, clipFileName=None, endedAt=None
    ):
        self.occurredAt = occurredAt
        self.fromDevice = fromDevice
        self.clipFileName = clipFileName
        self.endedAt = endedAt

    def reset(self):
        self.occurredAt = None
        self.fromDevice = None
        self.clipFileName = None
        self.endedAt = None

    def clone(self):
        return AnomalyLog(
            occurredAt=self.occurredAt,
            fromDevice=self.fromDevice,
            clipFileName=self.clipFileName,
            endedAt=self.endedAt,
        )
