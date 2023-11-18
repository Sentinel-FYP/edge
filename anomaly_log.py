class AnomalyLog:
    def __init__(self, occurredAt, fromDevice, clipFileName):
        self.occurredAt = occurredAt
        self.fromDevice = fromDevice
        self.clipFileName = clipFileName
        self.endedAt = None
