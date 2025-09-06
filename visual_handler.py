import sys, time, numpy as np, pygame
from pydub import AudioSegment
import matplotlib.pyplot as plt
import matplotlib.colors as mpl_colors
import math
import librosa
from PIL import Image, ImageDraw, ImageFont
import threading
import time
from multiprocessing import shared_memory, Lock
from utils import *
import json
import ctypes
from typing import Tuple
from menus import *
from visuals import *

user32 = ctypes.windll.user32


### <PARAMS> ###

CHUNK_SIZE          = 32768 # the size of a channel in the audio buffer

# window
FPS                 = 60
WINDOW_W            = 1200
WINDOW_H            = 800
fullscreen          = 0

# memory handling
shm                 = shared_memory.SharedMemory(create=False, name='shm_AudioHandler') 
meta                = json.load(open("meta.json"))
lock                = Lock()

# reading variables from shared memory
with lock:
    var = getmem(meta, shm)



### < COLORS > ###
menu_bg             = (  25,  25,  25)
screen_bg           = (   0,   0,   0)
visual_bg           = (   0,   0,   0)


border              = 1
border_color        = ( 200,   0,   0)



### < WINDOW INIT > ###
pygame.init()
window = Window(WINDOW_W, WINDOW_H, fullscreen=fullscreen)
window.iconified = False
running = True


# this should be removed and merge it into the window class
screen = Screen((0       , 0       , 0), 
                (WINDOW_H, WINDOW_W), 
                var, lock)


visual = Field((border           , border            , 0),
               (window.h-border*2, window.w-border*2))
visual_type = "field"
visual.active = False
visual.enabled = False
screen.add_child(visual)
visual.border = 0
visual.z = -1



bot_menu_h = 88
bot_menu = MenuBar((window.h-bot_menu_h-border,    border           ,  0), 
                   (bot_menu_h,        window.w-border*2                ))
screen.add_child(bot_menu)
bot_menu.visible = False



top_menu_h = 200
top_menu = MenuBar((border           , border    , 0), 
                   (top_menu_h,    window.w-border*2 ))
screen.add_child(top_menu)
top_menu.visible = False






side_menu_w = 400
side_menu = SideMenu((border,     window.w-side_menu_w-1           , 0), 
                     (window.h-border*2, side_menu_w ), 
                     var, lock)
screen.add_child(side_menu)
side_menu.visible = False








currentdir          = ('./user/audio')
files               = list_valid_files(currentdir)
file_offset         = 0

clock               = pygame.time.Clock()
font                = pygame.font.SysFont("Consolas", 18)







# audio handler functions for buttons

def playpause(**kwargs):
    var = kwargs["var"]
    if kwargs["paused"]:
        var["call_resume"][0] = 1          
    else:
        var["call_pause"][0] = 1
            
def stop(**kwargs):
    var = kwargs["var"]
    with lock:
        var["call_stop"][0] = 1

def adjust_brightness(arr ,level):
    """
    Takes in an int8 and adjusts the brightness levels
    """
    return np.clip(arr.astype(int) + level, 0, 255).astype(np.uint8)





### not used
tileset             = np.array(Image.open("tiles/tileset.png"))
button_small        = np.array(Image.open("tiles/button_small.png"))[...,0:3]
bt_s    = button_small
bt_s_h  = adjust_brightness(button_small, 30)
bt_s_a  = adjust_brightness(button_small, -30)
### - - -





s_color   = (0,0,0)
s_p_color = (50,0,0)
s_h_color = (100,0,0)
bt_s    = np.full_like(button_small, s_color)
bt_s_h  = np.full_like(button_small, s_h_color)
bt_s_a  = np.full_like(button_small, s_p_color)

playpause_button = Button((8, 8, 0), (32, 64), function=playpause)
bot_menu.add_child(playpause_button)
playpause_button.bg       = bt_s
playpause_button.bg_hover = bt_s_h
playpause_button.bg_active= bt_s_a
playpause_button.text     = "PLAY"

stop_button = Button((48, 8, 0), (32, 64), function=stop)
bot_menu.add_child(stop_button)
stop_button.bg            = bt_s
stop_button.bg_hover      = bt_s_h
stop_button.bg_active     = bt_s_a
stop_button.text          = "STOP"

seek_bar = SeekBar((8, 200, 0), (64, 300), var, lock)
bot_menu.add_child(seek_bar)



button_exit = Button((0 ,screen.w-26, 0), (24, 24))
button_exit.text = "X"
button_resize = Button((0, screen.w-50, 0), (24, 24))
button_iconify = Button((0, screen.w-74, 0), (24, 24))

top_menu.add_child(button_exit)
top_menu.add_child(button_resize)
top_menu.add_child(button_iconify)




build = True





visual.fill(visual_bg)











### <LOOP VARIABLES> ###

mouse_pos_last  = pygame.mouse.get_pos()




while running:
    
    
    ### <READING SHARED VARIABLES> ###
    
    with lock:
        current_sample  = var["position"][0].copy()
        samplerate      = var["samplerate"][0].copy()
        length          = var["length"][0].copy()
        paused          = var["paused"][0].copy()
        channel_0       = var["audio_data"][:CHUNK_SIZE].copy()
        channel_1       = var["audio_data"][CHUNK_SIZE:].copy()
    
    
    playpause_button.kwargs["paused"] = paused
    playpause_button.kwargs["var"]    = var
    if paused:
        playpause_button.text = "PLAY"
        playpause_button.build()
    else:
        playpause_button.text = "PAUSE"
        playpause_button.build()

    seek_bar.active_pos = current_sample/length
    
    ### <MOUSE POSITION + MINIMIZE> ###
    
    if not pygame.mouse.get_focused():
        mouse_pos = (window.w//2, window.h//2)
    if window.iconified:
        mouse_pos = (window.w//2, window.h//2)
        pygame.display.iconify()
    else:
        mouse_pos = pygame.mouse.get_pos()
        
        

        
        
    ### <EVENTS> ###
        
    for event in pygame.event.get():
        
        screen.handle_event(event)
        
        if event.type == pygame.QUIT:
            
            running = False
        
        if event.type == pygame.KEYDOWN:
            print(f"keydown: {event.key}")
        
        if event.type == pygame.KEYUP:
            print(f"keydup: {event.key}")
        
        
        
        elif event.type == pygame.WINDOWRESTORED:
            
            window.iconified   = False
            mouse_pos = (window.w//2, window.h//2)
            pygame.mouse.set_pos(mouse_pos)
            
        

        
        elif event.type == pygame.MOUSEBUTTONDOWN:

            if event.button == 1:
                
                if mouse_pos[0] >= window.w - 15 and mouse_pos[1] >= window.h - 15:  
                    
                    window.dragging   = True
                    window.drag_start = mouse_pos[0], mouse_pos[1]  
                    window.size_start = window.w, window.h
                    
            
            
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:  
            window.dragging = False
        
        
        
        elif event.type == pygame.MOUSEMOTION:  
            if window.dragging and not window.fscr:
                dx = mouse_pos[0] - window.drag_start[0]  
                dy = mouse_pos[1] - window.drag_start[1]
                # enforce minimum size  
                new_w = max(200, window.size_start[0] + dx)  
                new_h = max(150, window.size_start[1] + dy)  
                if new_w != window.w or new_h != window.h:
                    window.w = new_w
                    window.h = new_h
                    window.build()

                                            
    
    
    ##########################################################################################
    ##############################   D R A W I N G   #########################################
    ##########################################################################################
    
    if build: screen.build(); build = False
    
    # bg coloring
    screen.fill(screen_bg)
    bot_menu.fill(menu_bg)
    top_menu.fill(menu_bg)
    side_menu.fill(menu_bg)
    
    b = False
    if b:
        visual.img = spectrum_overlay(visual.img, channel_0, channel_1, freeze=0.0) # I do inplace modifications on the channels here for speed
    else:
        visual.img = vertical_spectrum(visual.img, channel_0, channel_1, freeze=0.0) # I do inplace modifications on the channels here for speed
    
    screen.draw()
    canvas = screen.img
    
    window.disp.fill((0, 0, 0))   
    surf = pygame.image.frombuffer(screen.img.tobytes(), (screen.img.shape[1],screen.img.shape[0]), "RGB")
    window.disp.blit(surf,(0,0))
    pygame.display.flip()
    
    clock.tick(FPS)




pygame.quit()
log("Visual Handler withered away.")


