import numpy as np
import colorsys



# The function assumes that the input samples are float32 between -1.0, 1.0 and also stereo. (I should normalize in audiohandler to make sure)

def spectrum_overlay( frame: np.ndarray,
                      channel_0: np.ndarray,
                      channel_1: np.ndarray,
                      samplerate: int = 44100,
                      normalize: bool = False,
                      use_db: bool = True,
                      db_min: float = -100,
                      db_max: float = -20,
                      freq_scale = 2.0,   # either "linear" or a float > 1
                      bar_color: tuple = (200,0,0),
                      hanning: bool = False,
                      remove_dc: bool = False,
                      pad: int = 64000,
                      sample_size: int = 8000,
                      visual_type: int = 1,
                      
                      zoom_x: float = 1.0, # display zoom
                      pos_x: float = 0.0,  # display pos [0.0, ..., 1.0]
                      
                      f_min: float = 20.0,
                      f_max: float = 16000.0,
                      
                      freeze: float = 0.0, # the amount of graph freezing, 1.0 is the max
                    ) -> np.ndarray:
                        
    """
    pad             : the number of zeros to pad after the samples (to increase fft frequency resolution)
    f_min, f_max    : the minimum and maximum frequency that is displayed
    """
    
    audio = [channel_0, channel_1]
    fft = []
    mag = []
    
    if hanning:
        window = np.hanning(sample_size)
    else:
        window = np.ones(sample_size)

    N = pad + sample_size

    max_int = 2147483647
    min_int = -2147483648
    full_scale_fft = (N/2) * max_int
    

    
    freqs = np.fft.rfftfreq(N, d=1.0/samplerate) # freqs have linear spacing
    
    # applying low and high cuts
    i_min = np.searchsorted(freqs, f_min, side='left')
    i_max = np.searchsorted(freqs, f_max, side='right')
    freqs = freqs[i_min:i_max]
    
    for i, c in enumerate(audio):
        c = c[:sample_size]
        
        if remove_dc:
            np.subtract(c, np.mean(c), out=c)

        c *= window
    
        if pad > 0:
            c = np.pad(c, (0, pad), mode='constant')

        # Convert to int, idk why though
    
        c *= max_int        
        c = c.astype(np.int32)
        
        fft.append(np.fft.rfft(c, n=N))
    
        mag.append(np.abs(fft[i]))
        
        mag[i] = mag[i][i_min:i_max]
    
        # high-shelf
        mag[i] = pre_emph(mag[i], freqs, samplerate, alpha=0.96)

        """
        phase.append(np.angle(fft[i]))
        """
    
        if use_db:
            scaling = 20.0
            
            mag[i] /= full_scale_fft
            mag[i] += 1e-12
            np.log10(mag[i], out=mag[i])
            
            mag[i] *= scaling
            
            np.clip(mag[i], db_min, db_max, out=mag[i])
            
            mag[i] -= db_min
            
            mag[i] /= (db_max - db_min)
            
            mag[i] *= 150 # scaled randomly
        else:
            mag[i] /= full_scale_fft 
            
            mag[i] *= 30 # scaled up by a random value
    
    
    
    
    frame_h, frame_w, _ = frame.shape    
    
    if freeze > 0.0:
        np.multiply(frame, freeze, out=frame) # np does a uint-float-uint conversion here
    else:
        frame.fill(0)
    
    # reducing the amount of magnitudes and giving it a curve for displaying the bars
    
    indeces = np.linspace(0, 1, frame_w)
    np.power(indeces, 4, out=indeces)
    mn, mx = indeces.min(), indeces.max()
    indeces = ((indeces - mn) / (mx - mn) * (len(mag[0])-1)).round().astype(int)
    
    for i, m in enumerate(mag):
        
        mag[i] = np.maximum.reduceat(mag[i], indeces)
    
        if use_db:
            mag[i] /= -db_min
    
        # local normalization
        if normalize and mag[i].max() > 0:
            mag[i] /= mag[i].max()
            
        mag[i].clip(0.0,1.0,out=mag[i]) # no idea why
    
    display_type = "bars"
    
    if display_type == "bars":    
    
        mag = mag[0] + mag[1]
        mag *= 0.5
        
        heights = (mag * frame_h).astype(int)
        
        shade_type = ""
        if shade_type == "sigm":
            k = 10.0                  
            sig = lambda x: 1/(1+np.exp(-x))
            f0 = sig(-k/2)            
            f1 = sig( k/2)            
            bar_shades = (
                (sig(k*(mag-0.5)) - f0)
                / (f1 - f0)
                * 255
            ).astype(int)
        if shade_type == "exp":
            k = 2.5
            bar_shades = (255 * (np.exp(k*mag) - 1) / (np.exp(k) - 1)).astype(int)
        if shade_type == "log":
            c = 2.0 
            bar_shades = (
                255
                * np.log1p(c * mag)
                / np.log1p(c)
            ).astype(int)
        else:
            bar_shades = np.full(mag.shape,255,dtype=np.int8)
            
        bar_colors = np.vstack([bar_shades,
                        np.zeros_like(bar_shades),
                        np.zeros_like(bar_shades)]).T
    

        for i, bar_h in enumerate(heights):
            frame[frame_h - bar_h : frame_h, i] = bar_colors[i]
    
    elif display_type == "lines":
        
        heights = []
        colors = [(255,0,0),(0,255,0)]
        for i, m in enumerate(mag):
            heights.append((m * frame_h).astype(int))
            for j, height in enumerate(heights):
                for k, h in enumerate(height):
                    frame[frame_h - h - 1, k] = colors[j]
                    
    elif display_type == "field":
                   
        mag_avg = np.zeros_like(mag)
        for m in mag:
            mag_avg += m
        mag_avg /= len(mag)

        # Create a mask for values where you want to draw (z>0)
        mask = mag > 0

        # Extract indices we need to draw
        idx = np.nonzero(mask)[0]

        # Calculate pan: avoid divide-by-zero
        L = current_0[mask_0]
        R = current_1[mask_1]
        T = L + R
        pan = np.where(T == 0, 0, (R - L) / T)

        x = x0 + ((pan + 1) / 2) * width
        y = y0 + height - (idx * (height / n))

        # Convert to integers and clip to surface boundaries
        x_int = np.clip(x.astype(int), 0, surface.get_width()-1)
        y_int = np.clip(y.astype(int), 0, surface.get_height()-1)

        # Lock the surface pixel array (using pygame.surfarray)
        arr3d = pygame.surfarray.pixels3d(surface)      # shape: (width, height, 3)
        arr_alpha = pygame.surfarray.pixels_alpha(surface)  # shape: (width, height)

        # Create a color array for assignment; each pixel gets (R, G, 0)
        # Here, we'll use the provided color's R and G channels and hardcode 0 for blue.
        col_array = np.empty((len(x_int), 3), dtype=np.uint8)
        col_array[:, 0] = color[0]
        col_array[:, 1] = color[1]
        col_array[:, 2] = 0

        # Assign colors to pixels using vectorized advanced indexing.
        arr3d[x_int, y_int] = col_array
        # Set the alpha channel based on z values (converted to uint8)
        arr_alpha[x_int, y_int] = z[mask].astype(np.uint8)
        
        
    return frame




def vertical_spectrum(frame: np.ndarray,
                      channel_0: np.ndarray,
                      channel_1: np.ndarray,
                      samplerate: int = 44100,
                      normalize: bool = True,
                      use_db: bool = True,
                      db_min: float = -100,
                      db_max: float = -20,
                      freq_scale = 2.0,   # either "linear" or a float > 1
                      bar_color: tuple = (200,0,0),
                      hanning: bool = False,
                      remove_dc: bool = False,
                      pad: int = 16000,
                      sample_size: int = 4048,
                      visual_type: int = 1,
                      resolution_multiplyer: int = 10000000,
                      zoom_x: float = 1.0, # display zoom
                      pos_x: float = 0.0,  # display pos [0.0, ..., 1.0]
                      
                      f_min: float = 2000.0,
                      f_max: float = 16000.0,
                      
                      freeze: float = 0.0, # the amount of graph freezing, 1.0 is the max
                    ) -> np.ndarray:
                        
    """
    pad             : the number of zeros to pad after the samples (to increase fft frequency resolution)
    f_min, f_max    : the minimum and maximum frequency that is displayed
    """
    
    audio = [channel_0, channel_1]
    fft = []
    mag = []
    
    if hanning:
        window = np.hanning(sample_size)
    else:
        window = np.ones(sample_size)

    N = pad + sample_size

    max_int = 2147483647
    min_int = -2147483648
    full_scale_fft = (N/2) * max_int
    

    
    freqs = np.fft.rfftfreq(N, d=1.0/samplerate) # freqs have linear spacing
    
    # applying low and high cuts
    i_min = np.searchsorted(freqs, f_min, side='left')
    i_max = np.searchsorted(freqs, f_max, side='right')
    freqs = freqs[i_min:i_max]
    
    phase = []
    
    for i, c in enumerate(audio):
        c = c[:sample_size]
        
        if remove_dc:
            np.subtract(c, np.mean(c), out=c)

        c *= window
    
        if pad > 0:
            c = np.pad(c, (0, pad), mode='constant')

        # Convert to int, idk why though
    
        c *= max_int        
        c = c.astype(np.int32)
        
        fft.append(np.fft.rfft(c, n=N))
    
        mag.append(np.abs(fft[i]))
        
        mag[i] = mag[i][i_min:i_max]

        phase.append(np.angle(fft[i])[i_min:i_max])
        
    color_phases = False
    if color_phases:
        mag = np.array(mag)
        phase = np.array(phase)
        
        X = mag * np.exp(1j * phase)
        X_mid = X.mean(axis=0)
        phase_mid = np.angle(X_mid)    
        h = (phase_mid + np.pi) / (2*np.pi)   # normalize to [0…1]
        rgb = np.array([colorsys.hsv_to_rgb(h_i,1,1) for h_i in h])

        
    for i, c in enumerate(audio):
        # high-shelf
        mag[i] = pre_emph(mag[i], freqs, samplerate, alpha=0.96)
    
        if use_db:
            scaling = 20.0
            
            mag[i] /= full_scale_fft
            mag[i] += 1e-12
            np.log10(mag[i], out=mag[i])
            
            mag[i] *= scaling
            
            np.clip(mag[i], db_min, db_max, out=mag[i])
            
            mag[i] -= db_min
            
            mag[i] /= (db_max - db_min)
            
            mag[i] *= 150 # scaled randomly
        else:
            mag[i] /= full_scale_fft 
            
            mag[i] *= 30 # scaled up by a random value
    
        
    
    
    frame_h, frame_w, _ = frame.shape    
    
    if freeze > 0.0:
        np.multiply(frame, freeze, out=frame) # np does a uint-float-uint conversion here
    else:
        frame.fill(0)
        
    res = frame_w * resolution_multiplyer
    if res > len(mag[0]): res = len(mag[0])
    
    indeces = np.linspace(0, 1, res)
    np.power(indeces, 4, out=indeces)
    mn, mx = indeces.min(), indeces.max()
    indeces = ((indeces - mn) / (mx - mn) * (len(mag[0])-1)).round().astype(int)
    
    for i, m in enumerate(mag):
        
        mag[i] = np.maximum.reduceat(mag[i], indeces)
    
        if use_db:
            mag[i] /= -db_min
    
        # local normalization
        if normalize and mag[i].max() > 0:
            mag[i] /= mag[i].max()
            
        mag[i].clip(0.0,1.0,out=mag[i]) # no idea why

    if True:
        
        mag = np.array(mag)
        mag_avg = np.zeros_like(mag[0])
        for m in mag:
            mag_avg += m
        mag_avg /= len(mag)
        n = len(mag_avg)
        
        # Create a mask for values where you want to draw (z>0)
        mask = mag_avg > 0
        
        # Extract indices we need to draw
        idx = np.nonzero(mask)[0]
        
        # Calculate pan: avoid divide-by-zero
            
        L = mag[0][mask]
        R = mag[1][mask]
        T = L + R
        
        special_pan = False
        if special_pan:
            pan = np.where(T == 0, 0, (R - L) / T)
            pan = (np.arcsin(pan) + np.pi/2) / np.pi     # semicircle warp: 0.5→center, 0/1→ends
            """
            gamma = 0.5
            pan = np.sign(pan) * np.abs(pan)**gamma  # still –1…+1
            pan = (pan + 1) / 2
            """
        else:
            pan = np.where(T == 0, 0, (R - L) / T)
            pan += 1
            pan /= 2
        
        x = pan * frame_w
        y = frame_h - (idx * (frame_h / n))
                
        # Convert to integers and clip to surface boundaries
        x_int = np.clip(x.astype(int), 0, frame_w-1)
        y_int = np.clip(y.astype(int), 0, frame_h-1)

        mag_avg = mag_avg[mask]
        
        shade_type = "exp"
        if shade_type == "sigm":
            k = 10.0                  
            sig = lambda x: 1/(1+np.exp(-x))
            f0 = sig(-k/2)            
            f1 = sig( k/2)            
            shades = (
                (sig(k*(mag_avg-0.5)) - f0)
                / (f1 - f0)
                * 255
            ).astype(int)
        if shade_type == "exp":
            k = 2
            shades = (255 * (np.exp(k*mag_avg) - 1) / (np.exp(k) - 1)).astype(int)
        if shade_type == "log":
            c = 2.0 
            shades = (
                255
                * np.log1p(c * mag_avg)
                / np.log1p(c)
            ).astype(int)
        else:
            shades = np.full(mag_avg.shape,255,dtype=np.uint8)
            
        
        if color_phases:
            rgb = rgb[mask]

            rgb[:,0] *= mag_avg
            rgb[:,1] *= mag_avg
            rgb[:,2] *= mag_avg
            rgb = rgb.astype("uint8")
        else:
            rgb = np.empty((len(x_int), 3), dtype=np.uint8)
            rgb[:, 0] = shades
            rgb[:, 1] = 0
            rgb[:, 2] = 0

            frame[y_int, x_int] = rgb
        return frame



def pre_emph(mag, freqs, samplerate, alpha=0.95):
    omega = 2*np.pi*freqs/samplerate
    H = np.abs(1 - alpha * np.exp(-1j * omega))
    return mag * H
    