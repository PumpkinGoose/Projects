import pyautogui
import time
import random

while True:
    print('Moving! (Press Ctrl + C to cancel)')
    pyautogui.moveTo(random.randint(0, 2560), random.randint(0, 1600))
    time.sleep(random.randint(10, 30))
