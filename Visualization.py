from PySide6.QtCore import Signal, Slot, QTimer, QObject
from PySide6.QtMultimedia import QAudioBuffer
from collections import deque
import numpy as np
import time

class VisualizationWorker(QObject):
    dataReady = Signal(list, float, float)

    def __init__(self):
        super().__init__()
        self.buffer_deque = deque([])
        self.timer = QTimer()
        self.timer.start(16) 
        

    @Slot()
    def render_visualization(self, audio_buffer: QAudioBuffer):
        if audio_buffer.data(): 
            self.buffer_deque.append(np.frombuffer(audio_buffer.data(), np.float32))
            t0 = time.perf_counter()
            spectrum = np.fft.fft(self.buffer_deque.popleft())
            fft_time = (time.perf_counter() - t0) * 1e6  # µs

            t0 = time.perf_counter()
            mags = np.abs(spectrum).tolist() 
            prep_time = (time.perf_counter() - t0) * 1e6  # µs
            self.dataReady.emit(mags, fft_time, prep_time)
    
        