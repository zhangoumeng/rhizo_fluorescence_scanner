import tkinter as tk
from PIL import Image, ImageTk
import ctypes
import tisgrabber as tis
import time
import numpy as np
import conexcc as cc
import arduino_control as ad
import imagingcontrol4 as ic4
import os
import cv2
import tifffile
import scipy

def update_frame():
    ic.IC_SnapImage(hGrabber, 2000)
    
    ic.IC_GetImageDescription(hGrabber, Width, Height,
                              BitsPerPixel, colorformat)
    
    bpp = int(BitsPerPixel.value / 8.0)
    buffer_size = Width.value * Height.value * BitsPerPixel.value

    imagePtr = ic.IC_GetImagePtr(hGrabber)

    imagedata = ctypes.cast(imagePtr,
                            ctypes.POINTER(ctypes.c_ubyte *
                                           buffer_size))

    image = np.ndarray(buffer=imagedata.contents,
                       dtype=np.uint8,
                       shape=(Height.value,
                              Width.value,
                              bpp))
    
    imagec = cv2.resize(image, (800, 600))
    
    imageTmp = Image.fromarray(imagec)
    photo = ImageTk.PhotoImage(image=imageTmp)
    label.config(image=photo)
    label.image = photo  # Keep a reference!
    window.after(10, update_frame)  # Update every 10ms

def move_stage(direction):
    xy_step = float(xy_step_input.get())
    z_step = float(z_step_input.get())
    conex_cc.read_cur_pos()
    currentZ = conex_cc.cur_pos
    
    bypassLim = xyBypassLim.get()

    if os.path.exists("xyPos.txt"):
        with open("xyPos.txt", "r") as f:
            xc, yc = map(float, f.read().split(","))
    else:
        xc, yc = 0.0, 0.0

    if direction == "up":
        xc, yc = controller.moveStage('up', stepSizeMM=xy_step, currentX=xc, currentY=yc, 
                             xMax=280, yMax=150, bypass_limit=bypassLim)
    elif direction == "down":
        xc, yc = controller.moveStage('down', stepSizeMM=xy_step, currentX=xc, currentY=yc, 
                             xMax=280, yMax=150, bypass_limit=bypassLim)
    elif direction == "left":
        xc, yc = controller.moveStage('left', stepSizeMM=xy_step, currentX=xc, currentY=yc, 
                             xMax=280, yMax=150, bypass_limit=bypassLim)
    elif direction == "right":
        xc, yc = controller.moveStage('right', stepSizeMM=xy_step, currentX=xc, currentY=yc, 
                             xMax=280, yMax=150, bypass_limit=bypassLim)
    elif direction == "z_up":
        conex_cc.move_absolute(currentZ+z_step)
        time.sleep(z_step/3+.2)
    elif direction == "z_down":
        conex_cc.move_absolute(currentZ-z_step)
        time.sleep(z_step/3+.2)
    
    conex_cc.read_cur_pos()
    currentZ = conex_cc.cur_pos
    
    with open("xyPos.txt", "w") as f:
        f.write(f"{xc},{yc}")
        
    update_position()
    
def home_position():
    xc, yc = 0.0, 0.0
    with open("xyPos.txt", "w") as f:
        f.write(f"{xc},{yc}")
    update_position()

def update_position():
    conex_cc.read_cur_pos()
    currentZ = conex_cc.cur_pos

    if os.path.exists("xyPos.txt"):
        with open("xyPos.txt", "r") as f:
            try:
                xc, yc = map(float, f.read().split(","))
            except ValueError:
                xc, yc = 0.0, 0.0  # Default values if file is corrupted
    else:
        xc, yc = 0.0, 0.0

    xy_pos_label.config(text=f"Current Position (mm): [{xc:.2f}, {yc:.2f}, {currentZ:.2f}]")

def control_camera():
    ic.IC_SnapImage(hGrabber, 2000)

def move_stage_scan(direction,step_size):
    
    bypassLim = xyBypassLim.get()

    if os.path.exists("xyPos.txt"):
        with open("xyPos.txt", "r") as f:
            xc, yc = map(float, f.read().split(","))
    else:
        xc, yc = 0.0, 0.0

    if direction == "up":
        xc, yc = controller.moveStage('up', stepSizeMM=step_size, currentX=xc, currentY=yc, 
                             xMax=280, yMax=150, bypass_limit=bypassLim)
    elif direction == "down":
        xc, yc = controller.moveStage('down', stepSizeMM=step_size, currentX=xc, currentY=yc, 
                             xMax=280, yMax=150, bypass_limit=bypassLim)
    elif direction == "left":
        xc, yc = controller.moveStage('left', stepSizeMM=step_size, currentX=xc, currentY=yc, 
                             xMax=280, yMax=150, bypass_limit=bypassLim)
    elif direction == "right":
        xc, yc = controller.moveStage('right', stepSizeMM=step_size, currentX=xc, currentY=yc, 
                             xMax=280, yMax=150, bypass_limit=bypassLim)
    
    with open("xyPos.txt", "w") as f:
        f.write(f"{xc},{yc}")
        
    update_position()


def data_acquisition():
    
    def stitch_image(data, step_size, x_num, y_num):

        overlap = 1 - step_size * 1e3 / (2.2 / 50 * 45 * 1944)
        im_sz = data.shape[0]
        overlap_px = round(im_sz * overlap)
                
        img_full = np.zeros((round((im_sz - overlap_px) * (x_num - 1) + im_sz), 
                             round((im_sz - overlap_px) * (y_num - 1) + im_sz), 2), dtype=np.uint16)
        
        for excitation in range(2):

            weight = np.vstack([
                np.kron(np.linspace(0, 1, overlap_px).reshape(overlap_px,1), np.ones((1, im_sz))),
                np.ones((im_sz - 2 * overlap_px, im_sz)),
                np.kron(np.linspace(1, 0, overlap_px).reshape(overlap_px,1), np.ones((1, im_sz)))]) * np.hstack([
                np.kron(np.linspace(0, 1, overlap_px), np.ones((im_sz, 1))),
                np.ones((im_sz, im_sz - 2 * overlap_px)),
                np.kron(np.linspace(1, 0, overlap_px), np.ones((im_sz, 1)))])
            
            img_full_tmp = np.zeros((round((im_sz - overlap_px) * (x_num - 1) + im_sz), 
                                     round((im_sz - overlap_px) * (y_num - 1) + im_sz)))
            
            for i in range(x_num * y_num):
                img = data[:, :, i, excitation].astype(np.float64)
                
                y_pos = round((x_num - 1 - (i // y_num)) * (im_sz - overlap_px))
                if (i // y_num) % 2:
                    x_pos = round((i % y_num) * (im_sz - overlap_px))
                else:
                    x_pos = round((y_num - 1 - (i % y_num)) * (im_sz - overlap_px))
                
                img_full_tmp[y_pos:y_pos + im_sz, x_pos:x_pos + im_sz] += img * weight * 255
            
            img_full[:, :, excitation] = np.round(img_full_tmp).astype(np.uint16)
            
        img_full_crop = img_full[overlap_px:-overlap_px, overlap_px:-overlap_px, :]
        
        return img_full_crop
    
    def submit_parameters():
        # Gather all values from the entry fields
        path_name = path_entry.get()
        file_name = file_entry.get()
        t_interval = float(time_interval_entry.get()) * 60
        num_timepoints = int(num_timepoints_entry.get())
        x_range = float(x_range_entry.get())
        y_range = float(y_range_entry.get())
        xy_step_scan = float(xy_step_entry.get())
        return path_name,file_name,t_interval,num_timepoints,x_range,y_range,xy_step_scan
        
    def start_acquisition():
        
        mat_data = scipy.io.loadmat('excitation_profile.mat')
        profile_488 = mat_data.get('profile_488')
        profile_565 = mat_data.get('profile_565') 
        
        adaptive_exp = adaptive_exposure.get()
        
        exposureList = []
        
        controller.laser488Off()
        controller.laser565Off()
        
        path_name,file_name,t_interval,num_timepoints,x_range,y_range,xy_step_scan = submit_parameters()
        
        x_slices = int(np.ceil(x_range / xy_step_scan))
        y_slices = int(np.ceil(y_range / xy_step_scan))
    
        num_img_captured = 0
    
        # Setup data structure for image storage
        image_stack = np.zeros((389, 389, int(x_slices * y_slices), 2), dtype=np.uint8)
    
        for t in range(num_timepoints):
            start_timepoint = time.time()
               
            current_exposure_tmp = ctypes.c_float()
            ic.IC_GetPropertyAbsoluteValue(hGrabber, tis.T("Exposure"), tis.T("Value"),
                                           current_exposure_tmp)
            current_expousre = current_exposure_tmp.value
            
            img_max_val = 0
            num_img_captured_t = 0
    
            for x_num in range(int(x_slices)):
                for y_num in range(int(y_slices)):
                    for excitation_line in range(1, 3):
                        if excitation_line == 1:
                            controller.laser488On()
                        else:
                            controller.laser565On()
                        
                        time.sleep(current_expousre+.3)
                        ic.IC_SnapImage(hGrabber, 5000)
                        ic.IC_GetImageDescription(hGrabber, Width, Height,
                                                  BitsPerPixel, colorformat)
                        
                        bpp = int(BitsPerPixel.value / 8.0)
                        buffer_size = Width.value * Height.value * BitsPerPixel.value

                        imagePtr = ic.IC_GetImagePtr(hGrabber)

                        imagedata = ctypes.cast(imagePtr,
                                                ctypes.POINTER(ctypes.c_ubyte *
                                                               buffer_size))

                        image = np.ndarray(buffer=imagedata.contents,
                                           dtype=np.uint8,
                                           shape=(Height.value,
                                                  Width.value,
                                                  bpp))
                        
                        imageData = image[:,:,0]
                        imageData = cv2.medianBlur(imageData, 3)
                        imageData = cv2.resize(imageData, None, fx=0.2, fy=0.2, interpolation=cv2.INTER_LINEAR)
                        img_max_val = max(img_max_val, np.percentile(imageData, 95))
    
                        imageDataTmp = np.flipud(imageData[:, 10:-119])
                        
                        # Define filename
                        file_number = (num_img_captured + 1) // 4000 + 1
                        file_path = os.path.join(path_name, f"{file_name}_{excitation_line}_{file_number}.tif")
                        
                        with tifffile.TiffWriter(file_path, append=True) as tf:
                            tf.write(imageData)

                        # Process image based on excitation line
                        if excitation_line == 1:
                            image_stack[:, :, num_img_captured_t, 0] = (imageDataTmp.astype(np.float64) * profile_488).astype(np.uint8)
                        else:
                            image_stack[:, :, num_img_captured_t, 1] = (imageDataTmp.astype(np.float64) * profile_565).astype(np.uint8)
    
                        num_img_captured = num_img_captured + 1
                        
                        if excitation_line == 1:
                            controller.laser488Off()
                        else:
                            controller.laser565Off()
                            num_img_captured_t = num_img_captured_t + 1
                            
    
                    if y_num != y_slices - 1:
                        if x_num % 2 == 0:
                            move_stage_scan('right',xy_step_scan)
                        else:
                            move_stage_scan('left',xy_step_scan)
                    elif x_num != x_slices - 1:
                        move_stage_scan('down',xy_step_scan)
    
            # After all points are captured for a time point
            if x_slices % 2 == 1:
                move_stage_scan('left', xy_step_scan * (y_slices - 1))  # Reset stage position
            move_stage_scan('up', xy_step_scan * (x_slices - 1))
    
            # Save the full dataset or additional processing here
            img_full = stitch_image(image_stack, xy_step_scan, x_slices, y_slices)
            file_path = os.path.join(path_name, f"{file_name}_green_stitch_{file_number}.tif")
            with tifffile.TiffWriter(file_path, append=True) as tf:
                tf.write(img_full[:,:,0])
            file_path = os.path.join(path_name, f"{file_name}_red_stitch_{file_number}.tif")
            with tifffile.TiffWriter(file_path, append=True) as tf:
                tf.write(img_full[:,:,1])
                
            if img_max_val > 200 and adaptive_exp:
                ic.IC_SetPropertyAbsoluteValue(hGrabber, "Exposure".encode("utf-8"),
                                               "Value".encode("utf-8"), ctypes.c_float(current_expousre/2))
            
            exposureList.append(current_expousre)
            file_path = os.path.join(path_name, f"{file_name}_exposureList.mat")
            scipy.io.savemat(file_path, {'exposureList': exposureList})

            controller.laser488Off()
            controller.laser565Off()
            
            # Wait until the next acquisition time point
            if t != num_timepoints-1:
                elapsed_time = time.time() - start_timepoint
                time.sleep(max(0, t_interval - elapsed_time))
        
        root.destroy()
        window.destroy()
    
    root = tk.Tk()
    root.geometry("480x520")
    root.title("Data Acquisition Settings")
    
    # Create Labels and Entry widgets for each parameter
    tk.Label(root, text="Path to save data:", font=("Arial", 10)).place(x=60, y=60, width=180, height=30)
    path_entry = tk.Entry(root, font=("Arial", 10))
    path_entry.insert(0, "C:\\Data\\")
    path_entry.place(x=240, y=60, width=180, height=30)

    
    tk.Label(root, text="File name:", font=("Arial", 10)).place(x=60, y=100, width=180, height=30)
    file_entry = tk.Entry(root, font=("Arial", 10))
    file_entry.insert(0, "data")
    file_entry.place(x=240, y=100, width=180, height=30)
    
    tk.Label(root, text="Time interval (minutes):", font=("Arial", 10)).place(x=60, y=140, width=180, height=30)
    time_interval_entry = tk.Entry(root, font=("Arial", 10))
    time_interval_entry.insert(0, "60")
    time_interval_entry.place(x=240, y=140, width=180, height=30)
    
    tk.Label(root, text="Number of time points:", font=("Arial", 10)).place(x=60, y=180, width=180, height=30)
    num_timepoints_entry = tk.Entry(root, font=("Arial", 10))
    num_timepoints_entry.insert(0, "48")
    num_timepoints_entry.place(x=240, y=180, width=180, height=30)
    
    tk.Label(root, text="X range (mm):", font=("Arial", 10)).place(x=60, y=220, width=180, height=30)
    y_range_entry = tk.Entry(root, font=("Arial", 10))
    y_range_entry.insert(0, "60")
    y_range_entry.place(x=240, y=220, width=180, height=30)
    
    tk.Label(root, text="Y range (mm):", font=("Arial", 10)).place(x=60, y=260, width=180, height=30)
    x_range_entry = tk.Entry(root, font=("Arial", 10))
    x_range_entry.insert(0, "60")
    x_range_entry.place(x=240, y=260, width=180, height=30)
    
    tk.Label(root, text="XY step (mm):", font=("Arial", 10)).place(x=60, y=300, width=180, height=30)
    xy_step_entry = tk.Entry(root, font=("Arial", 10))
    xy_step_entry.insert(0, "3")
    xy_step_entry.place(x=240, y=300, width=180, height=30)
    
    adaptive_exposure = tk.BooleanVar()
    adaptive_exposure_label = tk.Checkbutton(root, text = "Use Adaptive Exposure", variable = adaptive_exposure,
                             onvalue=True, offvalue=False, font=("Arial", 10))
    adaptive_exposure_label.place(x=240, y=340, width=180, height=30)
    
    # Button to submit the form
    submit_btn = tk.Button(root, text="Start Data Acquisition", font=("Arial", 10), command=start_acquisition)
    submit_btn.place(x=120, y=400, width=240, height=30)
    
    # Start the Tkinter main loop
    root.mainloop()

# ConexCC, Arduino, and imaging setup
cc.ConexCC.dump_possible_states()
conex_cc = cc.ConexCC(com_port='COM3', velocity=5)
controller = ad.ArduinoController('COM5')

# Set up the Tkinter window
window = tk.Tk()
window.geometry("1280x720")  # Set the window size, adjust as needed
window.title("Fluorescence Scanner")

# Image display (right side)
label = tk.Label(window)
label.place(x=420, y=60, width=800, height=600)

# Stage controls
xy_step_label = tk.Label(window, text="XY Step (mm):", font=("Arial", 10))
xy_step_label.place(x=60, y=20, width=180, height=30)
xy_step_input = tk.Entry(window, font=("Arial", 10))
xy_step_input.place(x=240, y=20, width=120, height=30)
xy_step_input.insert(0, "1")  # Default step size

xyBypassLim = tk.BooleanVar()
xylimit_label = tk.Checkbutton(window, text = "Bypass Limit", variable = xyBypassLim,
                         onvalue=True, offvalue=False, font=("Arial", 10))
xylimit_label.place(x=20, y=130, width=180, height=30)

xy_home_button = tk.Button(window, text="Home XY", font=("Arial", 10), command=lambda: 
                      home_position())
xy_home_button.place(x=280, y=130, width=80, height=30)

z_step_label = tk.Label(window, text="Z Step (mm):", font=("Arial", 10))
z_step_label.place(x=60, y=200, width=180, height=30)
z_step_input = tk.Entry(window, font=("Arial", 10))
z_step_input.place(x=240, y=200, width=120, height=30)
z_step_input.insert(0, "0.1")  # Default step size


# Directional buttons
up_button = tk.Button(window, text="↑", font=("Arial", 10), command=lambda: 
                      move_stage('up'))
up_button.place(x=180, y=60, width=60, height=30)

down_button = tk.Button(window, text="↓", font=("Arial", 10), command=lambda: 
                      move_stage('down'))
down_button.place(x=180, y=130, width=60, height=30)

left_button = tk.Button(window, text="←", font=("Arial", 10), command=lambda: 
                      move_stage('left'))
left_button.place(x=110, y=95, width=60, height=30)

right_button = tk.Button(window, text="→", font=("Arial", 10), command=lambda: 
                      move_stage('right'))
right_button.place(x=250, y=95, width=60, height=30)


# Z stage controls
z_up_button = tk.Button(window, text="Up", font=("Arial", 10), command=lambda: 
                      move_stage('z_up'))
z_up_button.place(x=60, y=240, width=80, height=30)

z_down_button = tk.Button(window, text="Down", font=("Arial", 10), command=lambda:
                      move_stage('z_down'))
z_down_button.place(x=170, y=240, width=80, height=30)

z_home_button = tk.Button(window, text="Home Z", font=("Arial", 10), command=lambda:
                        conex_cc.init_positioner())
z_home_button.place(x=280, y=240, width=80, height=30)

# current position
xy_pos_label = tk.Label(window, text="Current Position (mm): [0.00, 0.00, 0.00]", font=("Arial", 10))
xy_pos_label.place(x=60, y=300)

# LED control buttons
LED_488_label = tk.Label(window, text="470 LED", font=("Arial", 10))
LED_488_label.place(x=60, y=390, width=120, height=30)
LED_565_label = tk.Label(window, text="565 LED", font=("Arial", 10))
LED_565_label.place(x=240, y=390, width=120, height=30)

LED_488_on_button = tk.Button(window, text="On", font=("Arial", 10), command=lambda: 
                        controller.laser488On())
LED_488_on_button.place(x=60, y=420, width=60, height=30)
LED_488_off_button = tk.Button(window, text="Off", font=("Arial", 10), command=lambda: 
                        controller.laser488Off())
LED_488_off_button.place(x=120, y=420, width=60, height=30)

LED_565_on_button = tk.Button(window, text="On", font=("Arial", 10), command=lambda: 
                        controller.laser565On())
LED_565_on_button.place(x=240, y=420, width=60, height=30)
LED_565_off_button = tk.Button(window, text="Off", font=("Arial", 10), command=lambda: 
                        controller.laser565Off())
LED_565_off_button.place(x=300, y=420, width=60, height=30)

# Camera control button
camera_button = tk.Button(window, text="Camera Settings", font=("Arial", 10), command=lambda:
                          ic.IC_ShowPropertyDialog(hGrabber))
camera_button.place(x=60, y=520, width=300, height=30)

# Data acquisition button
data_button = tk.Button(window, text="Data Acquisition Settings", font=("Arial", 10), command=data_acquisition)
data_button.place(x=60, y=620, width=300, height=30)


ic4.Library.init()
ic4.DeviceEnum.devices()

ic = ctypes.cdll.LoadLibrary("./tisgrabber_x64.dll")
tis.declareFunctions(ic)
ic.IC_InitLibrary(0)
hGrabber = tis.openDevice(ic)
ic.IC_SetVideoFormat(hGrabber, tis.T("Y800 (2592x1944)"))

ic.IC_StartLive(hGrabber, 0)
time.sleep(1)

Width = ctypes.c_long()
Height = ctypes.c_long()
BitsPerPixel = ctypes.c_int()
colorformat = ctypes.c_int()

update_position()

# Start frame update loop
update_frame()

# Start the Tkinter main loop
window.mainloop()
