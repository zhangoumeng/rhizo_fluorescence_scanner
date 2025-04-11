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
    
    imageTmp = Image.fromarray(image)
    photo = ImageTk.PhotoImage(image=imageTmp)
    label.config(image=photo)
    label.image = photo  # Keep a reference!
    window.after(10, update_frame)  # Update every 10ms

def move_stage(direction):
    xy_step = float(xy_step_input.get())
    z_step = float(z_step_input.get())
    print(z_step)
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
                             xMax=100, yMax=100, bypass_limit=bypassLim)
    elif direction == "down":
        xc, yc = controller.moveStage('down', stepSizeMM=xy_step, currentX=xc, currentY=yc, 
                             xMax=100, yMax=100, bypass_limit=bypassLim)
    elif direction == "left":
        xc, yc = controller.moveStage('left', stepSizeMM=xy_step, currentX=xc, currentY=yc, 
                             xMax=100, yMax=100, bypass_limit=bypassLim)
    elif direction == "right":
        xc, yc = controller.moveStage('right', stepSizeMM=xy_step, currentX=xc, currentY=yc, 
                             xMax=100, yMax=100, bypass_limit=bypassLim)
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

def data_acquisition():
    print("Starting data acquisition...")

# ConexCC, Arduino, and imaging setup
cc.ConexCC.dump_possible_states()
conex_cc = cc.ConexCC(com_port='COM3', velocity=5)
controller = ad.ArduinoController('COM4')

# Set up the Tkinter window
window = tk.Tk()
window.geometry("1280x720")  # Set the window size, adjust as needed

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
LED_488_label = tk.Label(window, text="488 LED", font=("Arial", 10))
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
