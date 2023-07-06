import asyncio
from dataclasses import dataclass
from functools import cached_property
import sys # We need sys so that we can pass argv to QApplication
import os

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QLineEdit,
    QMainWindow,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from pyqtgraph import PlotWidget, plot
import pyqtgraph as pg

import qasync

from bleak import BleakScanner, BleakClient
from bleak.backends.device import BLEDevice

UART_SERVICE_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
UART_RX_CHAR_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
UART_TX_CHAR_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

UART_SAFE_SIZE = 20


@dataclass
class QBleakClient(QObject):
    device: BLEDevice
    

    messageChanged = pyqtSignal(object)

    def __post_init__(self):
        super().__init__()

    @cached_property
    def client(self) -> BleakClient:
        print(self.device)
        return BleakClient(self.device, disconnected_callback=self._handle_disconnect)

    async def start(self):
        await self.client.connect()
        await self.client.start_notify(UART_TX_CHAR_UUID, self._handle_read)

    async def stop(self):
        await self.client.disconnect()

    async def write(self, data):
        await self.client.write_gatt_char(UART_RX_CHAR_UUID, data)
        print("sent:", data)

    def _handle_disconnect(self, device) -> None:
        print("Device was disconnected, goodbye.")
        # cancelling all tasks effectively ends the program
        for task in asyncio.all_tasks():
            if task is not None:
                task.cancel()

    def _handle_read(self, _: int, data: bytearray) -> None:
        #print("received:", data)
        self.messageChanged.emit(data)
        '''
        global PreTime
        temp = 0
        temp = (data[2] ) | (data[3] << 8) | (data[4] << 16) | data[5] << 24 | data[6] << 32 | data[7] << 40 | data[8] << 48 |data[9] << 56
        diffT = temp - PreTime
        PreTime = temp
        print(diffT)

        global g_SampleTme
        global g_SampleSeqNum

        g_SampleTime.append(temp)

        #print (''.join('{:02x} '.format(x) for x in data))
        '''

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(1280, 720)

        self._client = None
        self.ppgGraph = PlotWidget()
        self.tintervalGraph = PlotWidget()
        self.seqNumGraph = PlotWidget()
        scan_button = QPushButton("Scan Devices")
        self.devices_combobox = QComboBox()
        connect_button = QPushButton("Connect")
        self.message_lineedit = QLineEdit()
        send_button = QPushButton("Send Message")
        self.log_edit = QPlainTextEdit()
        self.bConnected = False
        self.uPreTime = 0
        self.g_SampleTime = []
        self.g_SampleSeqNum = []
        self.g_SampleCh0 = []
        self.g_SampleCh1 = []
        self.PreSampleCh0 = -1
        self.PreSampleCh1 = -1       
        #self.g_SampleCh2 = []
        #self.g_SampleCh3 = []
        #self.g_SampleCh4 = []
        #self.g_SampleCh5 = []
        #self.g_SampleCh6 = []
        #self.g_SampleCh7 = []

        self.DiffSampleCh_1_0 = []
        self.DiffSampleCh_1_1 = []

        self.uCnt = 0

        self.ExpectSeqNum = -1

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        lay = QVBoxLayout(central_widget)
        lay.addWidget(self.ppgGraph)
        lay.addWidget(self.seqNumGraph)
        lay.addWidget(self.tintervalGraph)
        lay.addWidget(self.ppgGraph)
        lay.addWidget(scan_button)
        lay.addWidget(self.devices_combobox)
        lay.addWidget(connect_button)
        lay.addWidget(self.message_lineedit)
        lay.addWidget(send_button)
        lay.addWidget(self.log_edit)

        scan_button.clicked.connect(self.handle_scan)
        connect_button.clicked.connect(self.handle_connect)
        send_button.clicked.connect(self.handle_send)

    @cached_property
    def devices(self):
        return list()

    @property
    def current_client(self):
        return self._client

    async def build_client(self, device):
        if self._client is not None:
            await self._client.stop()
        self._client = QBleakClient(device)
        self._client.messageChanged.connect(self.handle_message_changed)
        await self._client.start()

    @qasync.asyncSlot()
    async def handle_connect(self):
        device = self.devices_combobox.currentData()
        if False == self.bConnected:
            self.log_edit.appendPlainText("try connect to " + device.name)
        else:
            self.log_edit.appendPlainText("try disconnect from " + device.name)

        if isinstance(device, BLEDevice):
            if False == self.bConnected:
                await self.build_client(device)
                self.log_edit.appendPlainText("connected")
                self.bConnected = True
                self.ppgGraph.clear()
                self.seqNumGraph.clear()
            else:
                await self._client.stop()
                self.bConnected = False
                self.log_edit.appendPlainText("disconnected")


    @qasync.asyncSlot()
    async def handle_scan(self):
        self.log_edit.appendPlainText("Started scanner")
        self.devices.clear()
        devices = await BleakScanner.discover()
        self.devices.extend(devices)
        self.devices_combobox.clear()
        for i, device in enumerate(self.devices):
            self.devices_combobox.insertItem(i, device.name, device)
        self.log_edit.appendPlainText("Finish scanner")

    def handle_message_changed(self, data):
        if -1 == self.ExpectSeqNum:
            self.ExpectSeqNum = data[1]
        temp = -1
        temp = data[1]
        if(temp != self.ExpectSeqNum):
            print('lost data {0} {1}'.format(temp, self.ExpectSeqNum))
        self.ExpectSeqNum = temp +1
        if(255 < self.ExpectSeqNum):
            self.ExpectSeqNum = 0
        temp = (data[2] ) | (data[3] << 8) | (data[4] << 16) | data[5] << 24 | data[6] << 32 | data[7] << 40 | data[8] << 48 |data[9] << 56
        diffTime = temp - self.uPreTime
        self.uPreTime = temp

        self.g_SampleTime.append(temp)
        self.g_SampleSeqNum.append(data[1])

        #SampleCh0 = (data[22] ) | (data[23] << 8) | (data[24] << 16) | data[25] << 24
        SampleCh0 = int.from_bytes((data[22], data[23], data[24], data[25]), byteorder='little', signed=True)/4096
        #print(hex(SampleCh0))
        self.g_SampleCh0.append(SampleCh0)

        #SampleCh1 = (data[26] ) | (data[27] << 8) | (data[28] << 16) | data[29] << 24
        SampleCh1 = int.from_bytes((data[26], data[27], data[28], data[29]), byteorder='little', signed=True)/4096
        #print(hex(SampleCh1))
        self.g_SampleCh1.append(SampleCh1)

        #sampleDiff = SampleCh1 - SampleCh0
        sampleDiff = SampleCh0 - self.PreSampleCh0
        self.PreSampleCh0 = SampleCh0;
        self.DiffSampleCh_1_0.append(sampleDiff)
        sampleDiff = SampleCh1 - self.PreSampleCh1
        self.PreSampleCh1 = SampleCh1;
        self.DiffSampleCh_1_1.append(sampleDiff)

        '''
        SampleCh = (data[30] ) | (data[31] << 8) | (data[32] << 16) | data[33] << 24
        self.g_SampleCh2.append(SampleCh)

        SampleCh = (data[34] ) | (data[35] << 8) | (data[36] << 16) | data[37] << 24
        self.g_SampleCh3.append(SampleCh)

        SampleCh = (data[38] ) | (data[39] << 8) | (data[40] << 16) | data[41] << 24
        self.g_SampleCh4.append(SampleCh)

        SampleCh = (data[42] ) | (data[43] << 8) | (data[44] << 16) | data[45] << 24
        self.g_SampleCh5.append(SampleCh)

        SampleCh = (data[46] ) | (data[47] << 8) | (data[48] << 16) | data[49] << 24
        self.g_SampleCh6.append(SampleCh)

        SampleCh = (data[50] ) | (data[51] << 8) | (data[52] << 16) | data[53] << 24
        self.g_SampleCh7.append(SampleCh)
        '''
        if(2088 <= len(self.g_SampleTime) ):
            #print("*****************")
            self.g_SampleSeqNum = self.g_SampleSeqNum[-2048:]
            self.g_SampleTime = self.g_SampleTime[-2048:]
                  
            self.g_SampleCh0 = self.g_SampleCh0[-2048:]
            self.g_SampleCh1 = self.g_SampleCh1[-2048:]
            '''
            self.g_SampleCh2 = self.g_SampleCh2[-500:]
            self.g_SampleCh3 = self.g_SampleCh3[-500:]
            self.g_SampleCh4 = self.g_SampleCh4[-500:]
            self.g_SampleCh5 = self.g_SampleCh5[-500:]
            self.g_SampleCh6 = self.g_SampleCh6[-500:]
            self.g_SampleCh7 = self.g_SampleCh7[-500:]
            '''
            self.DiffSampleCh_1_0 = self.DiffSampleCh_1_0[-2048:]
            self.DiffSampleCh_1_1 = self.DiffSampleCh_1_1[-2048:]
 
            
        self.uCnt += 1
        if(40 <= self.uCnt):
            self.uCnt = 0
            self.ppgGraph.clear()
            self.seqNumGraph.clear()
            self.tintervalGraph.clear()

            self.seqNumGraph.plot(self.g_SampleTime, self.g_SampleSeqNum)
            samplepen = pg.mkPen(color=(255,0,0))
            self.ppgGraph.plot(self.g_SampleTime, self.g_SampleCh0, pen = samplepen)
            samplepen = pg.mkPen(color=(0, 255, 0))
            self.ppgGraph.plot(self.g_SampleTime, self.g_SampleCh1, pen = samplepen)
            '''          
            samplepen = pg.mkPen(color=(0, 0, 255))
            self.ppgGraph.plot(self.g_SampleTime, self.g_SampleCh2, pen = samplepen)
            samplepen = pg.mkPen(color=(0, 255, 255))
            self.ppgGraph.plot(self.g_SampleTime, self.g_SampleCh3, pen = samplepen)
            samplepen = pg.mkPen(color=(255, 255, 0))
            self.ppgGraph.plot(self.g_SampleTime, self.g_SampleCh4, pen = samplepen)
            samplepen = pg.mkPen(color=(255, 0, 255))
            self.ppgGraph.plot(self.g_SampleTime, self.g_SampleCh5, pen = samplepen)
            samplepen = pg.mkPen(color=(128, 128, 128))
            self.ppgGraph.plot(self.g_SampleTime, self.g_SampleCh6, pen = samplepen)
            samplepen = pg.mkPen(color=(128, 0, 0))
            self.ppgGraph.plot(self.g_SampleTime, self.g_SampleCh7, pen = samplepen)
            '''

            samplepen = pg.mkPen(color=(255, 0, 0))
            self.tintervalGraph.plot(self.g_SampleTime, self.DiffSampleCh_1_0, pen = samplepen)
            samplepen = pg.mkPen(color=(0, 255, 0))
            self.tintervalGraph.plot(self.g_SampleTime, self.DiffSampleCh_1_1, pen = samplepen)


        #self.log_edit.appendPlainText(f"msg: {message.decode()}")
        
    @qasync.asyncSlot()
    async def handle_send(self):
        message = self.message_lineedit.text()
        splitStr = message.split(' ')
        for rS in splitStr:
                print(rS)  

        if self.current_client is None:
            return
        message = self.message_lineedit.text()

        #if message:
        #    await self.current_client.write(message.encode())

def main():
    app = QApplication(sys.argv)
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    w = MainWindow()
    w.show()
    with loop:
        loop.run_forever()


if __name__ == "__main__":
    main()

