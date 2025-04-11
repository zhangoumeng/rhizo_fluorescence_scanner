import serial
import time

class ArduinoController:
    def __init__(self, port='COM4', baud_rate=9600, timeout=1):
        self.arduino = serial.Serial(port, baud_rate, timeout=timeout)
        self.arduino.write(b'\r\n')
        time.sleep(2)
        self.arduino.flushInput()

    def laser565Off(self):
        self.arduino.write(b'b')

    def laser565On(self):
        self.arduino.write(b'a')

    def laser488Off(self):
        self.arduino.write(b'd')

    def laser488On(self):
        self.arduino.write(b'c')

    def moveStage(self, direction, stepSizeMM, currentX, currentY, xMax, yMax, bypass_limit=False):
        stepSize = stepSizeMM * 32  # Convert step size from mm to Arduino pulses
        commandStr = ''
        dxy = [0, 0]

        if direction == 'left':
            commandStr = f'-{stepSize}y'
            dxy = [-1, 0]
        elif direction == 'right':
            commandStr = f'{stepSize}y'
            dxy = [1, 0]
        elif direction == 'up':
            commandStr = f'-{stepSize * 1.5}x'
            dxy = [0, 1]
        elif direction == 'down':
            commandStr = f'{stepSize * 1.5}x'
            dxy = [0, -1]

        nextX = currentX + dxy[0] * stepSizeMM
        nextY = currentY + dxy[1] * stepSizeMM
        
        if not bypass_limit:
            if 0 <= nextX <= xMax and 0 <= nextY <= yMax:
                currentX = nextX
                currentY = nextY
                self.arduino.write(commandStr.encode())
            else:
                print("Movement exceeds the range limits.")
        else:
            currentX = nextX
            currentY = nextY
            self.arduino.write(commandStr.encode())

            # Update the display if needed
            # Example: xDisplay.set_text(str(currentX))
            # Example: yDisplay.set_text(str(currentY))

        return currentX, currentY
