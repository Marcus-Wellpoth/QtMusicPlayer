import sys
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QSlider,
    QLabel,
    QFileDialog,
)
from PySide6.QtCore import Qt, QDir, QThread, Signal, Slot
from PySide6.QtWidgets import QListView
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput, QAudioBufferOutput
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtCore import QUrl, QAbstractListModel, QModelIndex
from Visualization import VisualizationWorker


class SongListModel(QAbstractListModel):
    """
    A data model for the playlist. Inherits from QAbstractListModel.
    Implements data() and rowCount()
    
    Attributes:
        FilePathRole (int): User-defined view that triggers returning the full path of a .mp3 file.
        songs (List[str]): List of full paths to the .mp3 files
    """
    
    FilePathRole = Qt.UserRole + 1

    def __init__(self, songs):
        """
        Constructor.  Takes a list of path to the .mp3 files as argument.
        
        Args:
            songs (List[str]): A list of strings representing the full paths to .mp3 files.
        """
        super().__init__()
        self.songs = songs or []

    def data(self, index, role=Qt.DisplayRole) -> str | None:
        """
        Returns the data to be displayed depending on the role identifier given.
        
        Args:
            index(QModelIndex): The index of the entry to be displayed.
            role (Qt.DisplayRole | FilePathRole): The identifier. 
        
        Returns:
            str | None: The filename without suffix if role=Qt-DisplayRole, 
                        the full path if role=FilePathRole, 
                        None if the index is invalid.
        """
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            return self.songs[index.row()].split("/")[-1]
        if role == self.FilePathRole:
            return self.songs[index.row()]
        return None

    def rowCount(self, parent=QModelIndex()) -> int:
        """
        Returns the length of the list of .mp3 files
        
        Args:
            parent (QModelIndex) : The parent, required by QAbstractListModel
        
        Returns:
            int: The length of the list.
        """
        return len(self.songs)

    def append(self, item_list):
        """
        Appends a list of paths of .mp3 files.
        
        Args:
            item_list (List[str]): The list of paths to append.
        
        """
        row = self.rowCount()
        self.beginInsertRows(QModelIndex(), row, row + len(item_list) - 1)
        self.songs.extend(item_list)
        self.endInsertRows()


class MusicPlayerGUI(QMainWindow):

    dataReady = Signal(list, float, float)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("QtMusicPlayer")
        self.setGeometry(100, 100, 1000, 700)
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.player.mediaStatusChanged.connect(self.player_state_change)
        self.playlist_widget = QListView()
        self.song_list = SongListModel(songs=[])
        self.playlist_widget.setModel(self.song_list)
        self.playlist_widget.clicked.connect(self.play_at_index)
        self.current_index: QModelIndex | None = None
        self.visualization_worker_thread = QThread()
        self.visualization_worker = VisualizationWorker()
        self.audio_buffer = QAudioBufferOutput()
        self.player.setAudioBufferOutput(self.audio_buffer)
        self.audio_buffer.audioBufferReceived.connect(
            self.visualization_worker.render_visualization
        )
        self.visualization_worker.dataReady.connect(self.receive_data)
        self.visualization_worker.moveToThread(self.visualization_worker_thread)
        self.visualization_worker_thread.start()
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        self.create_menu_bar()

        # Steuerelemente
        controls_widget = QWidget()
        controls_layout = QVBoxLayout(controls_widget)
        btn_play = QPushButton("▶️ Play")
        btn_play.clicked.connect(self.play_music)
        controls_layout.addWidget(btn_play)
        btn_pause = QPushButton("⏸️ Pause")
        btn_pause.clicked.connect(self.pause_music)
        controls_layout.addWidget(btn_pause)
        btn_stop = QPushButton("⏹️ Stop")
        btn_stop.clicked.connect(self.stop_music)
        controls_layout.addWidget(btn_stop)
        btn_next = QPushButton("⏭️ Next")
        btn_next.clicked.connect(self.play_next)
        controls_layout.addWidget(btn_next)
        btn_previous = QPushButton("⏮️ Previous")
        btn_previous.clicked.connect(self.play_previous)
        controls_layout.addWidget(btn_previous)
        controls_layout.addStretch(1)
        controls_layout.addWidget(QLabel("Lautstärke"))
        slider_volume = QSlider(Qt.Horizontal)
        slider_volume.setValue(50)
        slider_volume.valueChanged.connect(self.set_volume)
        controls_layout.addWidget(slider_volume)
        main_layout.addWidget(controls_widget, 1)

        self.visualization_widget = QQuickWidget()
        self.visualization_widget.rootContext().setContextProperty("worker", self)
        self.visualization_widget.setSource(QUrl.fromLocalFile("oscilloscope.qml"))
        main_layout.addWidget(self.visualization_widget, 2)

        playlist_container = QWidget()
        playlist_layout = QVBoxLayout(playlist_container)

        label_playlist = QLabel("Song-Liste")
        playlist_layout.addWidget(label_playlist)
        playlist_layout.addWidget(self.playlist_widget, 1)
        playlist_layout.addStretch(1)
        main_layout.addWidget(playlist_container, 1)

    def play_music(self):
        if self.current_index != None:
            row = self.current_index.row()
            if self.song_list.index(row, 0).isValid():
                if (
                    self.player.playbackState()
                    == QMediaPlayer.PlaybackState.StoppedState
                ):
                    self.player.setSource(
                        self.song_list.data(
                            self.current_index, SongListModel.FilePathRole
                        )
                    )
                    self.player.play()
                elif (
                    self.player.playbackState()
                    == QMediaPlayer.PlaybackState.PausedState
                ):
                    self.player.play()

    def pause_music(self):
        if (self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState):
            self.player.pause()

    def stop_music(self):
        if (self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState):
            self.player.stop()

    def set_volume(self, value):
        self.audio_output.setVolume(value / 100.0)

    def create_menu_bar(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&Datei")

        open_file_action = file_menu.addAction("&Dateien öffnen...")
        open_file_action.triggered.connect(self.open_file_dialog)

        open_folder_action = file_menu.addAction("&Ordner öffnen...")
        open_folder_action.triggered.connect(self.open_folder_dialog)

        exit_action = file_menu.addAction("&Beenden")
        exit_action.triggered.connect(self.close)

    def player_state_change(self, state):
        if state == QMediaPlayer.MediaStatus.EndOfMedia:
            row = self.current_index.row() + 1
            if self.song_list.index(row, 0).isValid():
                self.current_index = self.song_list.index(row, 0)
                self.play_at_index(self.current_index)

    def open_folder_dialog(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Ordner auswählen")
        if folder_path:
            file_list = [
                item.absoluteFilePath()
                for item in QDir(folder_path).entryInfoList(
                    ["*.mp3"], QDir.Filter.Files
                )
            ]
            self.song_list.append(file_list)
            if self.player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
                if self.current_index == None:
                    self.current_index = self.song_list.index(0, 0)
                    self.play_at_index(self.current_index)
                else:
                    self.play_at_index(self.current_index)

    def open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileNames(
            self, "Dateien auswählen", filter="*.mp3"
        )
        self.song_list.append(file_path)
        if self.player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
            if self.current_index == None:
                self.current_index = self.song_list.index(0, 0)
                self.play_at_index(self.current_index)
            else:
                self.play_at_index(self.current_index)

    def play_at_index(self, index: QModelIndex):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.stop_music()
        row = index.row()
        if self.song_list.index(row, 0).isValid():
            self.current_index = index
            self.player.setSource(
                self.song_list.data(index, SongListModel.FilePathRole)
            )
            self.playlist_widget.setCurrentIndex(self.current_index)
            self.player.play()

    def play_next(self):
        row = self.current_index.row()
        if self.song_list.index(row + 1, 0).isValid():
            self.play_at_index(self.song_list.index(row + 1, 0))

    def play_previous(self):
        row = self.current_index.row()
        if self.song_list.index(row - 1, 0).isValid():
            self.play_at_index(self.song_list.index(row - 1, 0))

    @property
    def current_index(self) -> QModelIndex | None:
        return self._current_index

    @current_index.setter
    def current_index(self, index: QModelIndex | None):
        if index is not None and not isinstance(index, QModelIndex):
            raise TypeError(
                f"current_index must be a QModelIndex or None, got {type(index).__name__}"
            )
        self._current_index = index

    def closeEvent(self, event):
        self.visualization_worker_thread.quit()
        self.visualization_worker_thread.wait()
        event.accept()
    
    @Slot()
    def receive_data(self, mags: list, fft_time: float, prep_time: float):
        self.dataReady.emit(mags, fft_time, prep_time)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MusicPlayerGUI()
    window.show()
    sys.exit(app.exec())
