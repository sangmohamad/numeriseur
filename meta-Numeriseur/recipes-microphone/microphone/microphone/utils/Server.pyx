import socket
from time import sleep
from threading import Thread
from typing import Union
from typing import Optional
import utils.directives as directives


from utils.Audio_stream import AudioStream
from utils.rtsp_packet import RTSPPacket
from utils.rtp_packet import RTPPacket


import netifaces as ni
import uuid
from periphery import GPIO
from multiprocessing import Process


def ledblink():
    gpio_out = GPIO(74, "out")
    gpio_out.write(False)
    sleep(1)
    gpio_out.write(True)
    sleep(1)
    gpio_out.write(False)
    gpio_out.close()
        



class Server:

    FRAME_PERIOD = 1000//AudioStream.DEFAULT_FPS  # in milliseconds
    SESSION_ID =str( (uuid.uuid1()).node)

    try:
        ni.ifaddresses('eth0')
        DEFAULT_HOST =str(  ni.ifaddresses('eth0')[ni.AF_INET][0]['addr'])
    except Exception as e:
        ni.ifaddresses('usb0')
        DEFAULT_HOST=str(ni.ifaddresses('usb0')[ni.AF_INET][0]['addr'])
    
        
    DEFAULT_CHUNK_SIZE = 1024
    RTSP_SOFT_TIMEOUT = 100  

    class STATE:
        INIT = 0
        PAUSED = 1
        PLAYING = 2
        FINISHED = 3
        TEARDOWN = 4

    def __init__(self, rtsp_port: int):

        self._Audio_stream: Union[None, AudioStream] = None
        self._rtp_send_thread: Union[None, Thread] = None
        self._rtsp_connection: Union[None, socket.socket] = None
        self._rtp_socket: Union[None, socket.socket] = None
        self._client_address: (str, int) = None
        self.server_state: int = self.STATE.INIT

        self.rtsp_port = rtsp_port

    def _rtsp_recv(self, size=DEFAULT_CHUNK_SIZE) -> bytes:
        recv = None
        while True:
            try:
                recv = self._rtsp_connection.recv(size)
                break
            except socket.timeout:
                continue
        print(f"Received from client: {repr(recv)}")
        return recv

    def _rtsp_send(self, data: bytes) -> int:
        print(f"Sending to client: {repr(data)}")
        return self._rtsp_connection.send(data)

    def _get_rtsp_packet(self) -> RTSPPacket:
        return RTSPPacket.from_request(self._rtsp_recv())

    def _wait_connection(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        address = self.DEFAULT_HOST, self.rtsp_port
        s.bind(address)
        print(f"Listening on {address[0]}:{address[1]}...")
        s.listen(1)
        print("Waiting for connection...")
        self._rtsp_connection, self._client_address = s.accept()
        self._rtsp_connection.settimeout(self.RTSP_SOFT_TIMEOUT/1000.)
        print(f"Accepted connection from {self._client_address[0]}:{self._client_address[1]}")

    def _wait_setup(self):
        if self.server_state != self.STATE.INIT:
            raise Exception('server is already setup')
        while True:
            packet = self._get_rtsp_packet()
            if packet.request_type == directives.SETUP:
                self.server_state = self.STATE.PAUSED
                print('State set to PAUSED')
                self._client_address = self._client_address[0], packet.rtp_dst_port
                self._setup_rtp()
                self._send_rtsp_response(packet.sequence_number,packet.request_type)
                break

    

    def setup(self):
        self._wait_connection()
        self._wait_setup()

    def _start_rtp_send_thread(self):
        self._rtp_send_thread = Thread(target=self._handle_Audio_send)
        self._rtp_send_thread.setDaemon(True)
        self._rtp_send_thread.start()

    def _setup_rtp(self):
        
        self._Audio_stream = AudioStream()
        print('Setting up RTP socket...')
        self._rtp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._start_rtp_send_thread()

    def handle_rtsp_requests(self):
        print("Waiting for RTSP requests...")
        # main thread will be running here most of the time
        while True:
            packet = self._get_rtsp_packet()
            # assuming state will only ever be PAUSED or PLAYING at this point
            if packet.request_type == directives.PLAY:
                if self.server_state == self.STATE.PLAYING:
                    print('Current state is already PLAYING.')
                    continue
                self.server_state = self.STATE.PLAYING
                print('State set to PLAYING.')
            elif packet.request_type == directives.PAUSE:
                if self.server_state == self.STATE.PAUSED:
                    print('Current state is already PAUSED.')
                    continue
                self.server_state = self.STATE.PAUSED
                print('State set to PAUSED.')
            elif packet.request_type == directives.TEARDOWN:
                print('Received TEARDOWN request, shutting down...')
                self._send_rtsp_response(packet.sequence_number,packet.request_type)
                self._rtsp_connection.close()
                self._Audio_stream.close()
                self._rtp_socket.close()
                self.server_state = self.STATE.TEARDOWN
                # for simplicity's sake, caught on main_server
                raise ConnectionError('teardown requested')
            else:
                # will never happen, since exception is raised inside `parse_rtsp_request()`
                # raise InvalidRTSPRequest()
                pass
            self._send_rtsp_response(packet.sequence_number,packet.request_type)

    def _send_rtp_packet(self, packet: bytes):
        to_send = packet[:]
        while to_send:
            try:
                self._rtp_socket.sendto(to_send[:self.DEFAULT_CHUNK_SIZE], self._client_address)
            except socket.error as e:
                print(f"failed to send rtp packet: {e}")
                return
            # trim bytes sent
            to_send = to_send[self.DEFAULT_CHUNK_SIZE:]

    def _handle_Audio_send(self):
        print(f"Sending Audio to {self._client_address[0]}:{self._client_address[1]}")
        while True:
            if self.server_state == self.STATE.TEARDOWN:
                return
            if self.server_state != self.STATE.PLAYING:
                sleep(0.5)  # diminish cpu hogging
                continue
            ledblink()
            frame = self._Audio_stream.get_next_frame()
            frame_number = self._Audio_stream.current_frame_number
            rtp_packet = RTPPacket(
                payload_type=RTPPacket.TYPE.MJPEG,
                sequence_number=frame_number,
                timestamp=frame_number*self.FRAME_PERIOD,
                payload=frame
            )
            print(f"Sending packet #{frame_number}")
            print('Packet header:')
            rtp_packet.print_header()
            packet = rtp_packet.get_packet()
            self._send_rtp_packet(packet)
            sleep(self.FRAME_PERIOD/1000.)

    def _send_rtsp_response(self, sequence_number: int,request_type,client_port:Optional[int] = None):
        response = RTSPPacket.build_response(sequence_number, self.SESSION_ID,request_type,client_port)
        self._rtsp_send(response.encode())
        print('Sent response to client.')
