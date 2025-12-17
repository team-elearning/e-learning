class SyncResultDomain:
    """Domain object đơn giản để hứng kết quả sync"""
    def __init__(self, status, message, count):
        self.status = status
        self.message = message
        self.processed_count = count