from PySide6.QtCore import Signal, Slot, QObject
from PySide6.QtMultimedia import QAudioBuffer
import numpy as np
import time

class VisualizationWorker(QObject):
    """
    Prepares audio data for visual representation. Inherits from QObject.
    Signals:
        dataReady: Signal(list, float, float)
    """
    dataReady = Signal(list, float, float)

    def __init__(self):
        """
        Constructor
        """
        super().__init__()
        
    @Slot()
    def render_visualization(self, audio_buffer: QAudioBuffer):
        """
        Intercepts a QAudioBuffer.audioBufferReceived signal. Performs a FFT on the data
        and emits a dataReady signal
        
        Args:
            audio_buffer (QAudioBuffer): the AudioBuffer intercepted
            
        Emits:
            dataReady (Signal(list, float, float)): Contains the FFT magnitudes of the audio data,
                                                    the time taken to perform the FFT (µs), 
                                                    and the time to prepare the FFT data for rendering (µs).
        """
        if audio_buffer.data(): 
            buffer = np.frombuffer(audio_buffer.data(), np.float32)
            t0 = time.perf_counter()
            spectrum = np.fft.fft(buffer)
            fft_time = (time.perf_counter() - t0) * 1e6

            t0 = time.perf_counter()
            mags = np.abs(spectrum).tolist() 
            prep_time = (time.perf_counter() - t0) * 1e6
            self.dataReady.emit(mags, fft_time, prep_time)
    
        