"""RNG có seed, TÁCH LUỒNG theo mục đích để thêm tính năng không làm lệch chuỗi của luồng khác.

Dùng: rng = Streams(seed); rng.get("fish_spawn").random() ...
Không dùng random toàn cục, không dùng đồng hồ hệ thống (phá tính tất định).
"""

import random


class Streams:
    def __init__(self, seed: int):
        self._seed = seed
        self._streams = {}

    def get(self, name: str) -> random.Random:
        if name not in self._streams:
            # seed ổn định theo (seed, name), không phụ thuộc thứ tự gọi
            self._streams[name] = random.Random(f"{self._seed}:{name}")
        return self._streams[name]

    def stream(self, name: str) -> random.Random:
        return self.get(name)
