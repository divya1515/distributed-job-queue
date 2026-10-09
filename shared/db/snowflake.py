import threading
import time
import os 

class SnowflakeGenerator:
    EPOCH = 1704067200000 # custom epoch, e.g. 2024-01-01T00:00:00Z in ms

    DATACENTER_ID_BITS = 5
    MACHINE_ID_BITS = 5
    SEQUENCE_BITS = 12

    MAX_DATACENTER_ID = (1 << DATACENTER_ID_BITS) - 1   # 31
    MAX_MACHINE_ID = (1 << MACHINE_ID_BITS) - 1          # 31
    MAX_SEQUENCE = (1 << SEQUENCE_BITS) - 1              # 4095

    # shifts — build from the bottom up
    MACHINE_ID_SHIFT = SEQUENCE_BITS                                   # 12
    DATACENTER_ID_SHIFT = SEQUENCE_BITS + MACHINE_ID_BITS              # 17
    TIMESTAMP_SHIFT = SEQUENCE_BITS + MACHINE_ID_BITS + DATACENTER_ID_BITS  # 22

    def __init__(self, datacenter_id: int, machine_id: int):
        if datacenter_id < 0 or datacenter_id > self.MAX_DATACENTER_ID:
            raise ValueError(f"datacenter_id must be between 0 and {self.MAX_DATACENTER_ID}")
        if machine_id < 0 or machine_id > self.MAX_MACHINE_ID:
            raise ValueError(f"machine_id must be between 0 and {self.MAX_MACHINE_ID}")

        self.datacenter_id = datacenter_id
        self.machine_id = machine_id
        self.sequence = 0
        self.last_timestamp = -1
        self._lock = threading.Lock()

    def _current_millis(self) -> int:
        return int(time.time() * 1000)

    def _wait_next_millis(self, last_timestamp: int) -> int:
        ts = self._current_millis()
        while ts <= last_timestamp:
            ts = self._current_millis()
        return ts

    def next_id(self) -> int:
        with self._lock:
            ts = self._current_millis()

            if ts < self.last_timestamp:
                raise RuntimeError("Clock moved backwards. Refusing to generate id.")

            if ts == self.last_timestamp:
                self.sequence = (self.sequence + 1) & self.MAX_SEQUENCE
                if self.sequence == 0:
                    ts = self._wait_next_millis(ts)
            else:
                self.sequence = 0

            self.last_timestamp = ts

            return (
                ((ts - self.EPOCH) << self.TIMESTAMP_SHIFT)
                | (self.datacenter_id << self.DATACENTER_ID_SHIFT)
                | (self.machine_id << self.MACHINE_ID_SHIFT)
                | self.sequence
            )

DATACENTER_ID = int(os.getenv("DATACENTER_ID", "0"))
MACHINE_ID = int(os.getenv("MACHINE_ID", "0"))

snowflake = SnowflakeGenerator(DATACENTER_ID,MACHINE_ID)

def generate_id() -> int:
    return snowflake.next_id()
