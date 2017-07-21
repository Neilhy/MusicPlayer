#! /usr/bin/env python
# -*- coding:utf-8 -*-


import sip

sip.setapi('QString', 2)

import sys
import random

from PyQt4 import QtCore, QtGui

try:
    from PyQt4.phonon import Phonon
except ImportError:
    app = QtGui.QApplication(sys.argv)
    QtGui.QMessageBox.critical(
        None,
        "Music Player",
        "You don't have Phonon support.",
        QtGui.QMessageBox.Ok | QtGui.QMessageBox.Default,
        QtGui.QMessageBox.NoButton)
    sys.exit(1)


class MusicPlayer(QtGui.QMainWindow):
    STATE_PLAY_WAY_SEQUENTIAL = 1
    STATE_PLAY_WAY_SHUFFLE = 1 << 1
    STATE_PLAY_WAY_REPEAT = 1 << 2

    def __init__(self):
        super(MusicPlayer, self).__init__()

        self.audioOutput = Phonon.AudioOutput(
            Phonon.MusicCategory, self)  # send data to audio output device
        self.mediaObject = Phonon.MediaObject(
            self)  # an interface for media playback
        self.metaInformationResolver = Phonon.MediaObject(self)
        self.mediaObject.setTickInterval(1000)

        self.mediaObject.tick.connect(self.mpTick)
        self.mediaObject.stateChanged.connect(self.mpStateChanged)
        self.metaInformationResolver.stateChanged.connect(
            self.mpMetaStateChanged)
        self.mediaObject.currentSourceChanged.connect(self.mpSourceChanged)
        self.mediaObject.aboutToFinish.connect(self.mpAboutToFinish)

        Phonon.createPath(self.mediaObject, self.audioOutput)

        self.setupActions()
        self.setupMenus()
        self.setupUi()
        self.timeLcd.display("00:00")
        self.state_play_way = MusicPlayer.STATE_PLAY_WAY_SEQUENTIAL  # 初始化为顺序播放

        self.sources = []
        self.file_dir = ''

    def addFiles(self):
        if not self.file_dir:
            self.file_dir = QtGui.QDesktopServices.storageLocation(
                QtGui.QDesktopServices.MusicLocation)
        files = QtGui.QFileDialog.getOpenFileNames(
            self, u"Select Music Files", self.file_dir
        )
        if not files:
            return
        index = len(self.sources)
        self.file_dir = "/".join(files[0].split("\\")[:-1])
        # print self.file_dir
        for string in files:
            self.sources.append(Phonon.MediaSource(string))

        if self.sources:  # 刚刚加进来的文件
            self.metaInformationResolver.setCurrentSource(self.sources[index])

    def mpStateChanged(self, newState, oldState):
        """
        This signal is emitted when the state of the MediaObject has changed.
        And it will also be emitted with PausedState,
        which is the state the media object takes when the playback is finished
        """
        if len(self.sources) >= 1:
            self.nextAction.setEnabled(True)
            self.previousAction.setEnabled(True)
        else:
            self.nextAction.setEnabled(False)
            self.previousAction.setEnabled(False)

        if newState == Phonon.ErrorState:
            if self.mediaObject.errorType() == Phonon.FatalError:
                QtGui.QMessageBox.warning(self, "Fatal Error",
                                          self.mediaObject.errorString())
            else:
                QtGui.QMessageBox.warning(self, "Error",
                                          self.mediaObject.errorString())

        elif newState == Phonon.PlayingState:
            self.playAction.setVisible(False)
            self.pauseAction.setVisible(True)
            self.stopAction.setEnabled(True)

        elif newState == Phonon.StoppedState:
            self.playAction.setVisible(True)
            self.playAction.setEnabled(True)
            self.pauseAction.setVisible(False)
            self.stopAction.setEnabled(False)
            self.timeLcd.display("00:00")

        elif newState == Phonon.PausedState:
            self.playAction.setVisible(True)
            self.pauseAction.setVisible(False)
            self.stopAction.setEnabled(True)

    def mpTick(self, time):
        displayTime = QtCore.QTime(0, (time / 60000) % 60,
                                   (time / 1000) % 60)
        self.timeLcd.display(displayTime.toString('mm:ss'))

    def mpMetaStateChanged(self, newState, oldState):
        if newState == Phonon.ErrorState:
            QtGui.QMessageBox.warning(self, "Error opening files",
                                      self.metaInformationResolver.errorString())

            while self.sources and self.sources.pop() != self.metaInformationResolver.currentSource():
                pass

            return

        if newState != Phonon.StoppedState and newState != Phonon.PausedState:
            return

        if self.metaInformationResolver.currentSource().type() == Phonon.MediaSource.Invalid:
            return

        metaData = self.metaInformationResolver.metaData()

        title = metaData.get('TITLE', [''])[0]
        print title,type(title)
        print title.encode('utf-8'),type(title.encode('utf-8'))
        if not title:
            title = self.metaInformationResolver.currentSource().fileName()
        titleItem = QtGui.QTableWidgetItem(title.encode('raw_unicode_escape').decode('gbk'))
        titleItem.setFlags(titleItem.flags() ^ QtCore.Qt.ItemIsEditable)

        artist = metaData.get('ARTIST', [''])[0]
        artistItem = QtGui.QTableWidgetItem(artist.encode('raw_unicode_escape').decode('gbk'))
        artistItem.setFlags(artistItem.flags() ^ QtCore.Qt.ItemIsEditable)

        album = metaData.get('ALBUM', [''])[0]
        albumItem = QtGui.QTableWidgetItem(album.encode('raw_unicode_escape').decode('gbk'))
        albumItem.setFlags(albumItem.flags() ^ QtCore.Qt.ItemIsEditable)

        year = metaData.get('DATE', [''])[0]
        yearItem = QtGui.QTableWidgetItem(year.encode('raw_unicode_escape').decode('gbk'))
        yearItem.setFlags(yearItem.flags() ^ QtCore.Qt.ItemIsEditable)

        currentRow = self.musicTable.rowCount()  # Insert new row for new file
        self.musicTable.insertRow(currentRow)
        self.musicTable.setItem(currentRow, 0, titleItem)
        self.musicTable.setItem(currentRow, 1, artistItem)
        self.musicTable.setItem(currentRow, 2, albumItem)
        self.musicTable.setItem(currentRow, 3, yearItem)

        if not self.musicTable.selectedItems():
            self.musicTable.selectRow(0)
            self.mediaObject.setCurrentSource(
                self.metaInformationResolver.currentSource())

        index = self.sources.index(
            self.metaInformationResolver.currentSource()) + 1

        if len(self.sources) > index:
            self.metaInformationResolver.setCurrentSource(self.sources[index])
        else:
            self.musicTable.resizeColumnsToContents()
            if self.musicTable.columnWidth(0) > 300:
                self.musicTable.setColumnWidth(0, 300)

    def mpSourceChanged(self, source):
        self.musicTable.selectRow(self.sources.index(source))
        self.timeLcd.display('00:00')

    def mpAboutToFinish(self):
        index = self.sources.index(self.mediaObject.currentSource())
        if self.state_play_way & MusicPlayer.STATE_PLAY_WAY_SEQUENTIAL:  # 顺序播放
            pos = index + 1
            if len(self.sources) > pos:
                self.mediaObject.enqueue(self.sources[pos])  # 队列加入新的文件

        elif self.state_play_way & MusicPlayer.STATE_PLAY_WAY_SHUFFLE:  # 随机播放
            pos = index
            if len(self.sources) > 1:  # 防止进入while死循环
                while True:
                    pos = random.randint(0, len(self.sources) - 1)
                    if pos != index:
                        break
            self.mediaObject.enqueue(self.sources[pos])  # 队列加入新的文件

        else:
            if len(self.sources) > index + 1:
                self.mediaObject.enqueue(self.sources[index + 1])
            else:
                assert (len(self.sources) >= 1)
                self.mediaObject.enqueue(self.sources[0])

    def tableClicked(self, row, column):
        self.mediaObject.stop()
        self.mediaObject.clearQueue()
        self.mediaObject.setCurrentSource(self.sources[row])  # 正在播放的文件
        self.mediaObject.play()

    def doPlayWay(self):
        way_sender = self.sender()

        if way_sender.text() == 'Sequential':
            self.sequentialAction.setVisible(False)
            self.shuffleAction.setVisible(True)
            self.repeatAction.setVisible(False)
            self.state_play_way = MusicPlayer.STATE_PLAY_WAY_SHUFFLE

        elif way_sender.text() == 'Shuffle':
            self.sequentialAction.setVisible(False)
            self.shuffleAction.setVisible(False)
            self.repeatAction.setVisible(True)
            self.state_play_way = MusicPlayer.STATE_PLAY_WAY_REPEAT

        elif way_sender.text() == 'Repeat':
            self.sequentialAction.setVisible(True)
            self.shuffleAction.setVisible(False)
            self.repeatAction.setVisible(False)
            self.state_play_way = MusicPlayer.STATE_PLAY_WAY_SEQUENTIAL

    def nextToPlay(self):
        if len(self.sources) <= 1:
            return
        play_sender = self.sender()

        self.mediaObject.stop()
        self.mediaObject.clearQueue()

        index = self.sources.index(self.mediaObject.currentSource())
        if self.state_play_way & MusicPlayer.STATE_PLAY_WAY_SHUFFLE:  # 随机播放
            while True:
                pos = random.randint(0, len(self.sources) - 1)
                if pos != index:
                    break
            index = pos

        else:
            if play_sender.text() == 'Next':
                if len(self.sources) > index + 1:
                    index += 1
                else:
                    index = 0
            elif play_sender.text() == "Previous":
                index -= 1
        self.mediaObject.setCurrentSource(self.sources[index])  # 正在播放的文件
        self.mediaObject.play()

    def setupActions(self):
        self.playAction = QtGui.QAction(
            QtGui.QIcon('pic/play.png'), "Play",
            self, shortcut="Ctrl+P", enabled=False,
            triggered=self.mediaObject.play)

        self.pauseAction = QtGui.QAction(
            QtGui.QIcon('pic/pause.png'),
            "Pause", self, shortcut="Ctrl+A", visible=False,
            triggered=self.mediaObject.pause)

        self.stopAction = QtGui.QAction(
            QtGui.QIcon('pic/stop.png'), "Stop",
            self, shortcut="Ctrl+S", enabled=False,
            triggered=self.mediaObject.stop)

        self.nextAction = QtGui.QAction(
            QtGui.QIcon('pic/next.png'),
            "Next", self, shortcut="Ctrl+N", enabled=False)
        self.connect(self.nextAction, QtCore.SIGNAL('triggered()'),
                     self.nextToPlay)

        self.previousAction = QtGui.QAction(
            QtGui.QIcon('pic/previous.png'),
            "Previous", self, shortcut="Ctrl+R", enabled=False)
        self.connect(self.previousAction, QtCore.SIGNAL('triggered()'),
                     self.nextToPlay)

        self.repeatAction = QtGui.QAction(
            QtGui.QIcon('pic/repeat.png'), 'Repeat', self, shortcut="Ctrl+E",
            visible=False)
        self.connect(self.repeatAction, QtCore.SIGNAL('triggered()'),
                     self.doPlayWay)

        self.shuffleAction = QtGui.QAction(
            QtGui.QIcon('pic/shuffle.png'), 'Shuffle', self, shortcut="Ctrl+H",
            visible=False)
        self.connect(self.shuffleAction, QtCore.SIGNAL('triggered()'),
                     self.doPlayWay)

        self.sequentialAction = QtGui.QAction(
            QtGui.QIcon('pic/sequential.png'), 'Sequential', self,
            shortcut="Ctrl+U", enabled=True)
        self.connect(self.sequentialAction, QtCore.SIGNAL('triggered()'),
                     self.doPlayWay)

        self.addFilesAction = QtGui.QAction(QtGui.QIcon('pic/add_file.png'),
                                            "Add &Files", self,
                                            shortcut="Ctrl+F",
                                            triggered=self.addFiles)

        self.exitAction = QtGui.QAction(QtGui.QIcon('pic/Exit_48px.png'),
                                        "E&xit", self, shortcut="Ctrl+X",
                                        triggered=self.close)

    def setupMenus(self):
        fileMenu = self.menuBar().addMenu("&File")
        fileMenu.addAction(self.addFilesAction)
        fileMenu.addSeparator()
        fileMenu.addAction(self.exitAction)

    def sizeHint(self):
        return QtCore.QSize(550, 300)

    def setupUi(self):
        toolbar = QtGui.QToolBar()

        toolbar.addAction(self.playAction)
        toolbar.addAction(self.pauseAction)
        toolbar.addAction(self.stopAction)
        toolbar.addSeparator()
        toolbar.addAction(self.previousAction)
        toolbar.addAction(self.nextAction)
        toolbar.addSeparator()
        toolbar.addAction(self.sequentialAction)
        toolbar.addAction(self.shuffleAction)
        toolbar.addAction(self.repeatAction)

        self.seekSlider = Phonon.SeekSlider(self)
        self.seekSlider.setMediaObject(self.mediaObject)

        self.volumeSlider = Phonon.VolumeSlider(self)
        self.volumeSlider.setAudioOutput(self.audioOutput)
        self.volumeSlider.setSizePolicy(QtGui.QSizePolicy.Maximum,
                                        QtGui.QSizePolicy.Maximum)

        palette = QtGui.QPalette()
        palette.setBrush(QtGui.QPalette.Light, QtCore.Qt.darkGreen)

        self.timeLcd = QtGui.QLCDNumber()
        self.timeLcd.setPalette(palette)

        headers = (u"Title", u"Artist", u"Album", u"Year")

        self.musicTable = QtGui.QTableWidget(0, 4)
        self.musicTable.setHorizontalHeaderLabels(headers)
        self.musicTable.setSelectionMode(
            QtGui.QAbstractItemView.SingleSelection)
        self.musicTable.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        self.musicTable.cellDoubleClicked.connect(self.tableClicked)

        seekerLayout = QtGui.QHBoxLayout()
        seekerLayout.addWidget(self.seekSlider)
        seekerLayout.addWidget(self.timeLcd)

        playbackLayout = QtGui.QHBoxLayout()
        playbackLayout.addWidget(toolbar)
        playbackLayout.addStretch()
        playbackLayout.addWidget(self.volumeSlider)

        mainLayout = QtGui.QVBoxLayout()
        mainLayout.addWidget(self.musicTable)
        mainLayout.addLayout(seekerLayout)
        mainLayout.addLayout(playbackLayout)

        main_widget = QtGui.QWidget()
        main_widget.setLayout(mainLayout)

        self.setCentralWidget(main_widget)
        self.setWindowTitle("中文".decode('utf-8'))
        print "中文1",type("中文1")
        print "中文1".decode('utf-8'),type("中文1".decode('utf-8'))

def main():
    app = QtGui.QApplication(sys.argv)
    app.setApplicationName(u"Music Player")
    app.setQuitOnLastWindowClosed(True)

    music_player = MusicPlayer()
    music_player.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
