from numpy import ndarray
import numpy as np
from multiprocessing import Lock
import os
from datetime import datetime
import pygame

def getmem(meta, shm):
    lock = Lock()
    var = {}
    with lock:
        for k, v in meta.items():
           var[k] = ndarray(v["shape"],
                      dtype=v["dtype"],
                      buffer=shm.buf,
                      offset=v["offset"])
    return var


    
def extract_path(a: ndarray) -> str:
    b = a[a != ""]
    return "".join(b)


    
def log(string):
    n = 29
    string = string.replace("\n", "\n" + " " * n)
    t = datetime.now()
    print(f"[{t:%Y-%m-%d %H:%M:%S}.{t.microsecond:6d}] {string}")

    
    
class Window():
    
    def __init__(self,
                 width       = 800, 
                 height      = 600,
                 min_width   = 800,
                 min_height  = 600,
                 fullscreen  = False,):
        
        self.w    = width
        self.h    = height
        self.minw = min_width
        self.minh = min_height
        self.fscr = fullscreen
        
        self.iconified       = False 
        self.grabbing        = False
        self.dragging        = False 
        self.drag_start      = (0, 0)  
        self.size_start      = (self.w, self.h) 
        
        self.build()

    def build(self):
        if self.fscr:
            self.mode = "fullscreen"
            self.disp = pygame.display.set_mode((self.w, self.h), pygame.FULLSCREEN)
        else:
            self.mode = "windowed"
            self.disp = pygame.display.set_mode((self.w, self.h), pygame.NOFRAME)








    
def draw_stereo_field(surface, current_0, current_1, color, pos_rect, normalize=False, fixed_range=(-40, 0), sr=48000):
    
    x0, y0, width, height = pos_rect
    eps     = 1e-8 ## ?
    
    db_0    = 20 * np.log10(current_0 + eps)
    db_1    = 20 * np.log10(current_1 + eps)
    db_avg  = (db_0 + db_1) / 2
    
    if normalize:
        db_all = np.concatenate((db_0, db_1))
        db_min = np.min(db_all)
        db_max = np.max(db_all)
    else:
        db_min, db_max = fixed_range
        
    clipped_db_avg = np.clip(db_avg, db_min, db_max)
    z = (clipped_db_avg - db_min) / (db_max - db_min) * 255
    
    optimized_draw(surface, z, current_0, current_1, color, pos_rect)




def open_audio(audio_path): ##### needs some work
    
    with lock:
        
        path = audio_path
        var["audio_path"][:len(path)] = list(path)
        log(f"audio_path      = {path}")
        var["call_read"][0] = 0
        log( "call_read       = 1")
    
