import numpy as np
from typing import Tuple
from PIL import Image, ImageDraw, ImageFont
import pygame
import os
from functools import partial

from text_utils import draw_text
from file_utils import list_valid_files

### tkinter is here to speed up things, will be replaced
import tkinter as tk
from tkinter import filedialog
root = tk.Tk()
root.withdraw()



class Component():
    """
    The most basic unit of the graphical interface.
    """
        
    def __init__(self, pos, shape):
        
        self.x              = pos[1]
        self.y              = pos[0]
        self.z              = pos[2]
        
        self.h              = shape[0]
        self.w              = shape[1]
                
        
        
        self.visible        = True
        self.enabled        = True
        self.hover          = False
        self.active         = False
        
        self.parent         = None
        self.children       = []
        
        
        
        self.border         = 1
        self.border_color   = (200, 0, 0)
        
        self.bg_color       = (0,0,0)
        
        self.bg             = np.full((self.h,self.w,3),self.bg_color, dtype=np.uint8)
        self.bg_active      = np.full((self.h,self.w,3),self.bg_color, dtype=np.uint8)
        self.bg_hover       = np.full((self.h,self.w,3),self.bg_color, dtype=np.uint8)
        
        self.img            = np.full((self.h,self.w,3),self.bg_color, dtype=np.uint8)
        self.img_active     = np.full((self.h,self.w,3),self.bg_color, dtype=np.uint8)
        self.img_hover      = np.full((self.h,self.w,3),self.bg_color, dtype=np.uint8)
        
        
        
    def add_child(self, child):
        child.parent = self
        self.children.append(child)

    def remove_child(self, child):
        if child in self.children:
            self.children.remove(child)
            child.parent = None



    def fill(self, color=(0,0,0)):
        self.img[:] = color
        self.img_active[:] = color
        self.img_hover[:] = color



    def add_border(self, x=None):
        """
        add border to the existing images, intrinsically
        """
        if x is not None:
            if self.border > 0:
                x[:self.border , :, :]     = self.border_color
                x[-self.border:, :, :]     = self.border_color
                x[:, :self.border , :]     = self.border_color
                x[:, -self.border:, :]     = self.border_color
            
        else:
            if self.border > 0:
                self.img[:self.border , :, :]     = self.border_color
                self.img[-self.border:, :, :]     = self.border_color
                self.img[:, :self.border , :]     = self.border_color
                self.img[:, -self.border:, :]     = self.border_color

                self.img_active[:self.border , :, :]     = self.border_color
                self.img_active[-self.border:, :, :]     = self.border_color
                self.img_active[:, :self.border , :]     = self.border_color
                self.img_active[:, -self.border:, :]     = self.border_color
                
                self.img_hover[:self.border , :, :]     = self.border_color
                self.img_hover[-self.border:, :, :]     = self.border_color
                self.img_hover[:, :self.border , :]     = self.border_color
                self.img_hover[:, -self.border:, :]     = self.border_color
        
        
        
    def build(self):
        for child in self.children:
            child.build()
              

              
    def draw(self, canvas):
        if self.visible:
            self.add_border()
            for child in self.children:
                child.draw(canvas)
        
        
        
    # this one is for animations
    def update(self, dt):
        for child in self.children:
            child.update(dt)        



    def global_pos(self):
        """
        returns the position of an element relative to the window
        """
        if self.parent:
            px, py = self.parent.global_pos()
            return px + self.x, py + self.y
        return self.x, self.y
        
        
        
    def hit_test(self, mx, my):
        if not self.enabled:
            return False
        gx, gy = self.global_pos()
        hit = gx <= mx < gx + self.w and gy <= my < gy + self.h
        if self.parent:
            hitparent = self.parent.hit_test(mx, my)
            return hit and hitparent
        else:
            return hit
        
        
        
    def handle_event(self, event):
        
        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            hover = self.hit_test(mx, my)
            if hover != self.hover:
                if hover : self.on_mouse_enter(event)
                else     : self.on_mouse_leave(event)
                self.hover = hover
            if self.hover:
                self.on_mouse_hover(event)
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = event.pos
            if self.hit_test(mx, my):
                self.on_mouse_down(event)
        if event.type == pygame.MOUSEBUTTONUP:
            mx, my = event.pos
            if self.hit_test(mx, my):
                self.on_mouse_up(event)
        if event.type == pygame.KEYDOWN:
            self.on_key_down(event)
        if event.type == pygame.KEYUP:
            self.on_key_up(event)
            
        self.children = sorted(self.children, key=lambda obj: obj.z)
        for child in reversed(self.children):
            if child.enabled:
                if child.handle_event(event): 
                    return True
                    
        return False
        
        
    
    def on_mouse_hover(self, event): pass
    def on_mouse_enter(self, event): pass
    def on_mouse_leave(self, event): pass
    def on_mouse_down(self, event): pass
    def on_mouse_up(self, event): pass
    def on_key_down(self, event): pass
    def on_key_up(self, event): pass
        


class Screen(Component):
    
    def __init__(self, pos, shape, var, lock):
        super().__init__(pos, shape)
        self.menu_opened = False
        self.var = var
        self.lock = lock
        
    def draw(self):
        self.add_border()
        for child in self.children:
            if child.visible:
                child.draw(self.img)    
    
    def on_key_down(self, event):
        if event.key == 32:
            with self.lock:
                if self.var["paused"][0] == 1:
                    self.var["call_resume"][0] = 1
                else:
                    self.var["call_pause"][0] = 1



class Field(Component):

    def __init__(self, pos, shape):
        super().__init__(pos, shape)
            
    def draw(self, canvas):
        if self.visible:
            
            for child in self.children:
                child.draw(self.img)
            
            bottom = self.y + self.h - 1
            right = self.x + self.w - 1
            
            
            if self.y < 0:
                y = 0
                y2 = -self.y
            else:
                y = self.y
                y2 = 0
                
            if self.x < 0: 
                x = 0
                x2 = -self.x
            else:
                x = self.x
                x2 = 0
                
                
            if canvas.shape[0]-1 < bottom:
                height = self.h - (bottom+1 - canvas.shape[0])
            else:
                height = self.h
                
            if canvas.shape[1]-1 < right:
                width = self.w - (right+1 - canvas.shape[1])
            else:
                width = self.w
                
            height -= y2
            width -= x2
            
            if height > 0 and width > 0:
                sub = canvas[y:y+height, x:x+width, :]
                sub[...] = self.img[y2:y2+height, x2:x2+width, :]
                self.add_border(sub)
                
        return canvas



class MenuBar(Field):

    def __init__(self, pos, shape):
        super().__init__(pos, shape)
        
    def on_mouse_enter(self, event):
        if not self.parent.menu_opened:
            self.visible = True
            self.parent.menu_opened = True
            self.z = 1
        
    def on_mouse_leave(self, event):
        if self.visible:
            self.visible = False
            self.parent.menu_opened = False
            self.z = 0



class SideMenu(MenuBar):

    def __init__(self, pos, shape, var, lock):
        super().__init__(pos, shape)

        self.file_list_path = "./user/audio"
        self.file_list = []
        self.var  = var
        self.lock = lock
        self.offset = 0
        self.g = 20
        
        self.update_files()

    
    def generate_wall(self):
        
        btn_h   = 32
        gap     = 8
        self.frame = Field((self.g*2+32,self.g,2),(585, self.w-2*self.g))
        self.add_child(self.frame)
        self.content = Field((self.offset,0,3), ((btn_h+gap)*self.file_count+gap, self.frame.w))
        self.content.border = 0
                
        for i, fn in enumerate(self.file_list):
            fullpath = os.path.abspath(os.path.join(self.file_list_path, fn))
            cb = partial(self.button_function, file_path=fullpath)
            btn = Button((gap+i*(btn_h+gap), gap, 4), (32, self.frame.w-2*gap), function=cb)
            btn.bg        = np.full_like(btn.img, (0  ,0  ,0))
            btn.bg_active = np.full_like(btn.img, (50 ,0  ,0))
            btn.bg_hover  = np.full_like(btn.img, (100,0  ,0))
            btn.text      = fn
            btn.build()
            self.content.add_child(btn)
        
        self.frame.add_child(self.content)


    def update_wall(self):
        self.content.y = self.offset


    def update_files(self):
        self.children = []
        
        self.filtered = list_valid_files(self.file_list_path)
        self.file_list = [".."] + self.filtered
        self.file_count = len(self.file_list)
        
        self.path_display = Button((self.g, self.g, 2), (32, self.w-2*self.g), function=self.path_button_func)
        pd          = self.path_display
        pd.bg       = np.full_like(pd.img, (0,0,0))
        pd.bg_press = np.full_like(pd.img, (50,0,0))
        pd.bg_hover = np.full_like(pd.img, (100,0,0))
        pd.text     = self.file_list_path
        pd.build()
        self.add_child(pd)
        self.generate_wall()



    def button_function(self, **kwargs):
        p=kwargs["file_path"]
        if os.path.isfile(p) and p.lower().endswith((".mp3",".wav")):
            with self.lock:
                self.var["audio_path"][:] = [""]*256
                self.var["audio_path"][:len(p)] = list(p)
                self.var["call_read"][0] = 1
        elif os.path.isdir(p):
            self.offset = 0
            self.file_list_path = p
            self.update_files()
            
            
    
    def path_button_func(self,  **kwargs):
        path = filedialog.askdirectory()
        if path == '': return
        else: self.file_list_path = path
        print(self.file_list_path)
        self.offset = 0
        self.update_files()


    
    def on_mouse_down(self, event):
        if event.button == 4:
            if self.offset < 0:
                self.offset += 10
                if self.offset > 0: self.offset = 0
            self.update_wall()
        if event.button == 5:
            min_offs = self.frame.h - self.content.h
            if self.offset > min_offs:
                self.offset -= 10
                if self.offset < min_offs: self.offset = min_offs
            self.update_wall()




class Control(Component):
    
    def __init__(self, pos, shape):
        
        super().__init__(pos, shape)
        self.text = ""
        self.margin = (0,0)
        self.color = (255, 255, 255)
        self.padding = (3,6)
        
    def build(self):
        
        self.img        = self.bg.copy()
        self.img_hover  = self.bg_hover.copy()
        self.img_active  = self.bg_active.copy()
        
        w,h,_ = self.img.shape
        wp, hp = (self.border + self.padding[0], self.border + self.padding[1])
        
        draw_text(self.img[wp:w-wp, hp:h-hp], self.text, color=self.color)
        draw_text(self.img_hover[wp:w-wp, hp:h-hp], self.text, color=self.color)
        draw_text(self.img_active[wp:w-wp, hp:h-hp], self.text, color=self.color)





class Button(Control):
    
    def __init__(self, pos, shape, 
                 function=None, 
                 kwargs={}):
        super().__init__(pos, shape)
        self.function  = function
        self.kwargs    = kwargs

    def draw(self, canvas):
        if self.visible:
                        
            bottom = self.y + (self.h - 1)
            right  = self.x + (self.w - 1)
            
            
            if self.y < 0:
                y  = 0
                y2 = -self.y
            else:
                y  = self.y
                y2 = 0
                
            if self.x < 0: 
                x  = 0
                x2 = -self.x
            else:
                x  = self.x
                x2 = 0
                
                
            if canvas.shape[0]-1 < bottom:
                height = self.h - (bottom+1 - canvas.shape[0])
            else:
                height = self.h
                
            if canvas.shape[1]-1 < right:
                width = self.w - (right+1 - canvas.shape[1])
            else:
                width = self.w
                
            height -= y2
            width -= x2
            
            if height > 0 and width > 0:
                sub = canvas[y:y+height, x:x+width, :]                
                if self.active:
                    sub[...] = self.img_active[y2:y2+height, x2:x2+width, :]
                elif self.hover:
                    sub[...] = self.img_hover[y2:y2+height, x2:x2+width, :]
                else:
                    sub[...] = self.img[y2:y2+height, x2:x2+width, :]
                for child in self.children:
                    child.draw(sub)    
                self.add_border(sub)
        return canvas
        
    def on_mouse_down(self, event):
        if event.button == 1:
            self.active = True
        
    def on_mouse_up(self, event):
        if event.button == 1:
            self.active = False
            if self.function:
                self.function(**self.kwargs)
    
    def on_mouse_leave(self, event):
        self.active = False



class SeekBar(Component):

    def __init__(self, pos, shape, var, lock):
        super().__init__(pos, shape)
        self.active_pos = 0
        self.active_color = (200,0,0)
        self.passive_color = (100,0,0)
        self.var  = var
        self.lock = lock
        
    def draw(self, canvas):
        if self.visible:
            sub = canvas[self.y:self.y+self.h, self.x:self.x+self.w, :]
            self.img[:] = self.passive_color     
            self.img[:, :int(self.active_pos*self.w), :] = self.active_color
            sub[...] = self.img

    def on_mouse_up(self, event):
        if event.button == 1:
            x = event.pos[0]
            gx = self.global_pos()[0]
            x = x - gx
            norm_pos = x / self.w
            with self.lock:
                audio_length = self.var["length"][0]
                self.var["position"][0] = int(audio_length*norm_pos)



class VerticalScrollBar(Field):
    
    def __init__(self, pos, shape):
        super().__init__(pos, shape)
        self.z = 2
        self.pos = 0
        self.scroller_h = 128
        self.max_pos = self.h-self.scroller_h-1
        self.scroller = Button((0,0,3),(self.scroller_h, self.w))
        self.scroller.bg = np.full_like(self.scroller.bg, (100,0,0))
        self.scroller.bg_press = np.full_like(self.scroller.bg, (100,0,0))
        self.scroller.bg_hover = np.full_like(self.scroller.bg, (100,0,0))   
        self.add_child(self.scroller)
        self.build()
        
    def draw(self, canvas):
        if self.visible:
            self.add_border()
            sub = canvas[self.y:self.y+self.h, self.x:self.x+self.w, :]
            sub[...] = self.img
            for child in self.children:
                child.draw(sub)
        return canvas