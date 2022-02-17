# This Python file uses the following encoding: utf-8
from PyQt5 import QtCore
import serial
import threading

VERSION = "v.3.0.1"

CRC_BASE  = 0x12
PACK_SIGN = 0x69
CMD_START_OK     = 0x00
CMD_SET_POOLS    = 0x01
CMD_SET_RESP     = 0x02
CMD_GET_POOLS    = 0x11
CMD_GET_RESP     = 0x12
CMD_PARMS_GET    = 0x20
CMD_PARMS_RESP   = 0x21
CMD_VERSION_GET  = 0x30
CMD_VERSION_RESP = 0x31

ERR_CRC         = 0x80
ERR_SIGN        = 0x81
ERR_RECV        = 0x90
ERR_UNKNOWN_CMD = 0xA0
ERR_NO_INCOMING = 0xB0


class SerialPort(QtCore.QObject):
    _recvSignal_ = QtCore.pyqtSignal(int, str, name="recvsignal")

    def __init__(self, s_port, baud='9600'):
        super(SerialPort, self).__init__()

        self.port = serial.Serial(s_port, baud, timeout=1)
#        self.port.
        self.received_thread = threading.Thread(target=self.Receive, args=(self,))
        self.received_thread.setDaemon(True)
        self.received_thread.setName("SerialPortRecvThread")
        self.received_thread.start()

    def isRunning(self):
        return self.port.isOpen()

    def registerReceivedCallback(self, callback):
        self._recvSignal_.connect(callback)

    def crc_counter(self, buf):
        crc = CRC_BASE
        for a in buf:
            crc ^= a;
            for _ in range(0,8):
                if (crc & 1):
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc = (crc >> 1)
        return crc

    def prepare_buf(self, cmd, data):
        buf = bytearray(b'\0\0\0\0\0\0\0\0\0\0\0\0')
        buf[0] = PACK_SIGN
        buf[1] = cmd
        data_len = (len(data) if len(data)<=8 else 8)
        b_data = bytearray()
        b_data.extend(map(ord, data))
#        print("AAA: ", data_len, b_data)
        for i in range(data_len):
            buf[i+2] = b_data[i]
        crc = self.crc_counter(buf[:-2])
        b_crc = crc.to_bytes((crc.bit_length() + 7) // 8, 'big')
        buf[10] = b_crc[1]
        buf[11] = b_crc[0]
        print( len(buf), str(buf) )
        return buf

    def Receive(self, context):
#        typedef struct {
#            unsigned char sign;
#            unsigned char cmd;
#            unsigned char data[8];
#            unsigned short crc;
#        } buffer_type;
        while context.isRunning():
#            context.port.write(b'Enter data: ')
            buf = context.port.read(12)
            if (len(buf) == 12):
                sign = int(buf[0])
                cmd = int(buf[1])
                data = buf[+2:-2]
                crc = int.from_bytes(buf[+10:], byteorder='little')
                crc_counted = self.crc_counter(buf[:-2])
                if (PACK_SIGN == sign):
#                   print('Buf: ', buf)
#                   print(sign, cmd, data, "%04X"%crc, "%04X"%crc_counted)
#                   a = crc_counted.to_bytes((crc_counted.bit_length() + 7) // 8, 'big')
                    if crc == self.crc_counter(buf[:-2]):
                        print("Received correct package: ", cmd, CMD_SET_POOLS)

                        if (CMD_SET_POOLS == cmd):
                            print("CMD_SET_POOLS")
                            context.port.write( self.prepare_buf(CMD_SET_RESP, str(data)) )
                            for i in range(2):
                                for p in range(8):
                                    if data[i] & (1<<p):
                                        context._recvSignal_.emit(i*8+p, "background-color : yellow")
                                    else:
                                        context._recvSignal_.emit(i*8+p, "background-color : None")

                        elif (CMD_GET_POOLS == cmd):
                            context.port.write( self.prepare_buf(CMD_GET_RESP, "\0\0\0\0\0\0\0\0") )
                        elif (CMD_PARMS_GET == cmd):
                            context.port.write( self.prepare_buf(CMD_PARMS_RESP, "\x78\x10\0\0\0\0\0\0") )
                        elif (CMD_VERSION_GET == cmd):
                            context.port.write( self.prepare_buf(CMD_VERSION_RESP, VERSION) )

                    else:
                        print("ERROR: Incorect crc: 0x%04X" % crc)
                else:
                    print("ERROR: Incorrect package Sign: 0x%02X" % sign)


#            try:
#                num = int(line)
#                print('Num: ', num)
#                context._recvSignal_.emit(num, "background-color : yellow")
#            except:
#                print("Can't convert to num")
#                context._recvSignal_.emit(15, "background-color : red")
