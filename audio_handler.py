import threading
import socket
import time
import numpy as np
import librosa
import pyaudio
from multiprocessing import shared_memory, Lock
import json
from utils import getmem, extract_path, log


##  TO DO: - make a thread out of the read() function, because of reasons
##         - zero padding the audio that will be written
##         - maybe make a distinct thread for writing the audio



class AudioHandler:
    def __init__(self, normalize=True, chunk_size=1024, host='', port=50007):

        self._exit         = threading.Event()
        self._pause        = threading.Event()
        self._socket_stop  = threading.Event()
        self._pause.set()
        
        self.play          = True
        self.stop_audio    = False
        self.normalize     = normalize
        self.chunk_size    = chunk_size
        self.samples       = None
        self.channels      = 2
        self.length        = None
        self.host          = host
        self.port          = port
        self.p             = pyaudio.PyAudio()
        self.stream        = None
        self.isaudio       = 0
        
        self.lock          = Lock()
        self.shm_size      = 4194304
        self.shm           = shared_memory.SharedMemory(create=True, size=self.shm_size, name='shm_AudioHandler')
        self.meta          = json.load(open("meta.json"))
        self.var           = getmem(self.meta, self.shm)
        with self.lock: 
            self.var["paused"    ][0] = 1
            self.var["position"  ][0] = 0
            self.var["samplerate"][0] = 44100 
            self.var["length"    ][0] = 1

        self.audio_thread  = threading.Thread(target=self._audio_playback ,   daemon=True)
        self.socket_thread = threading.Thread(target=self._socket_listener,   daemon=True)
        
    
    
    def read(self, audio_file):
        
        self.isaudio = 0
        self.stop()
        if self.stream: 
            self.stream.stop_stream()
            self.stream.close()
        if self.p:
            self.p.terminate()
        self.p = pyaudio.PyAudio()
        try:
            self.samples, self.sr = librosa.load(audio_file, sr=None, mono=False)
            log("audio loaded successfully")
        except Exception as e:
            log("Error loading audio:\n")
            log(e)
        
        if self.normalize:
            max_val = np.max(np.abs(self.samples))
            if max_val == 0:
                raise RuntimeError("Audio file is completely silent.")
            self.samples = self.samples / max_val
        if self.samples.ndim == 1:
            self.samples = np.vstack([self.samples, self.samples])
        
        
        
        self.channels = self.samples.shape[0]
        self.length = self.samples.shape[1]
        
        self.stream = self.p.open(format=pyaudio.paFloat32,
                        channels=self.channels,
                        rate=self.sr,
                        output=True)
                        
        log("audio processed")
        with self.lock:
            self.var[ "position"   ][0] = 0
            self.var[ "samplerate" ][0] = self.sr
            self.var[ "length"     ][0] = self.samples.shape[1]
        self.isaudio = 1
        log("finished reading audio")
        self.resume()
    




    def _audio_playback(self):

        while not self._exit.is_set():
            
            with self.lock:
                pos         = self.var[ "position"    ][0]
                call_read   = self.var[ "call_read"   ][0]
                call_pause  = self.var[ "call_pause"  ][0]
                call_stop   = self.var[ "call_stop"   ][0]
                call_resume = self.var[ "call_resume" ][0]
            
            if call_resume == 1:
                with self.lock:
                    self.var["call_resume"][0] = 0
                self.resume()
            if call_stop == 1:
                with self.lock: 
                    self.var["call_stop"][0]   = 0
                self.stop()
            if call_pause == 1:
                with self.lock:
                    self.var["call_pause"][0]  = 0 
                self.pause()
            if call_read == 1:
                with self.lock: 
                    self.var["call_read"][0]   = 0
                    pth = extract_path(self.var["audio_path"])
                log(f"Reading: {pth}")
                self.read(pth)
                continue
                               
            if self._pause.is_set():
                    time.sleep(0.1)
                    continue
                    
            elif self.isaudio:
                try:
                    with self.lock:
                        self.var["audio_data"][:32768] = self.samples[0, pos:pos+32768]
                        self.var["audio_data"][32768:] = self.samples[1, pos:pos+32768]
                except Exception:
                    log("Error writing audio data. (padding error, I need to replace the buffer with a circular one)")
                    self.stop()
                    continue
                if pos >= self.length:
                    pos = 0
                end_pos = min(pos + self.chunk_size, self.length)
                chunk = self.samples[:, pos:end_pos]
                data = chunk.T.astype(np.float32).tobytes()
                try:
                    self.stream.write(data)
                except Exception:
                    pass
                
                
                with self.lock: # end lock
                    if not self._pause.is_set():
                        if self.var["position"][0] == pos: 
                            pos += self.chunk_size
                            self.var["position"][0] = pos
                    
            else: 
                time.sleep(0.1)
                log("No samples, stopping.")
                self.stop()
                
        if self.stream: 
            self.stream.stop_stream()
            self.stream.close()
        if self.p:
            self.p.terminate()
    
    
    
    
    
    def _socket_listener(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.host, self.port))
        sock.listen(5)
        sock.settimeout(0.5)
        log("Socket is listening")
        while not self._socket_stop.is_set():
            try:
                conn, addr = sock.accept()
            except socket.timeout:
                continue
            except Exception as e:
                log(e)
            
            with conn:
                try:
                    data = conn.recv(1024).strip()
                    if not data:
                        continue
                    decoded = data.decode('utf-8').lower()
                    arg = decoded[5:]
                    cmd = decoded[:4]
                    log(f"received message: {decoded}")
                    
                    try:
                        sock.send(f"received: {decoded}".encode("utf-8"))
                    except Exception as e:
                        log(e)
                    
                    if cmd == "read":
                        self.read(arg)
                    elif cmd == "play":
                        self.resume()
                    elif cmd == "wait":
                        self.pause()
                    elif cmd == "stop":
                        self.stop()
                    elif cmd == "getp": pass # get set position
                    elif cmd == "setp": pass
                    elif cmd == "updt": pass # update variables according to a json
                except Exception:
                    continue
        sock.close()
    
    
    
    def start(self):
        self.audio_thread.start()
        self.socket_thread.start()
    
    def pause(self):
        self._pause.set()
        with self.lock:
            self.var["paused"][0] = 1
        log("paused")
    
    def resume(self):
        if self.isaudio is not None:
            self._pause.clear()
            with self.lock:
                self.var["paused"][0] = 0
            log("Playing audio.")
        else:
            log("No audio to be played.")
    
    def stop(self):
        self._pause.set()
        with self.lock:
            self.var["position"][0] = 0
            self.var["audio_data"][:32768] = np.zeros(32768)
            self.var["audio_data"][32768:] = np.zeros(32768)
            self.var["paused"][0] = 1
        log("Stopped.")
    
    def shutdown(self):
        self._exit.set()
        self._socket_stop.set()
        self.audio_thread.join()
        self.socket_thread.join()

if __name__ == "__main__":
    audio_handler = AudioHandler(port=50007)
    log(f"AudioHandler port is opened.\nPort: {audio_handler.port}\nHost: {audio_handler.host}")
    audio_handler.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        audio_handler.shutdown()
