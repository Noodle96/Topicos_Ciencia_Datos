import time
from typing import Optional, TextIO

class Timer:
    def __init__(self, name: str = ""):
        self.name = name
        self.start_time = time.perf_counter()

    # Reinicia el cronómetro
    def reset(self, new_name: str = ""):
        self.name = new_name
        self.start_time = time.perf_counter()

    # Retorna el tiempo en segundos desde el último reset/start
    def elapsed(self) -> float:
        return time.perf_counter() - self.start_time

    # Imprime el tiempo transcurrido si hay nombre
    def printElapsed(self, out: Optional[TextIO], suffix: str = "seg"):
        if self.name and out is not None:
            print(f"[Timer] {self.name}: {self.elapsed():.6f} {suffix}", file=out)
