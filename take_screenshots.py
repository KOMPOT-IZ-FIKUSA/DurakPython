import keyboard

import utils

if __name__ == "__main__":
    prev = False
    while True:
        pressed = keyboard.is_pressed("q")
        if pressed and not prev:
            utils.save_test_screenshot()
        prev = pressed