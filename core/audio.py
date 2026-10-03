import threading
import numpy as np
import sounddevice as sd


class AudioRecorder:
    def __init__(self, samplerate=16000, blocksize=512):
        self.samplerate = samplerate
        self.blocksize = blocksize
        self.frames = []
        self.level = 0.0
        self._lock = threading.Lock()
        self._stream = None
        self.noise_floor = 0.002

    def _callback(self, indata, frames, time_info, status):
        chunk = indata[:, 0].copy()

        with self._lock:
            self.frames.append(chunk)

        rms = float(np.sqrt(np.mean(chunk * chunk)))

        if rms < self.noise_floor * 2.0:
            self.noise_floor = (
                self.noise_floor * 0.98 + rms * 0.02
            )

        level = max(0.0, rms - self.noise_floor)
        self.level = float(np.clip(level * 25.0, 0.0, 1.0))

    def start(self):
        self._stream = sd.InputStream(
            samplerate=self.samplerate,
            channels=1,
            blocksize=self.blocksize,
            dtype="float32",
            callback=self._callback,
        )
        self._stream.start()

    def stop(self):
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        with self._lock:
            if not self.frames:
                return np.empty(0, dtype=np.float32)

            audio = np.concatenate(self.frames).astype(
                np.float32, copy=False
            )
            self.frames.clear()

        return audio
