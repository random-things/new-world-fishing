import win32gui
import pyautogui
import pydirectinput
import time
import logging
import math
import win32com
import win32com.client
import random

from enum import Enum
from typing import Union

MAX_QUEUE_LENGTH = 10


class PlayerState(Enum):
    NONE = 1
    FISHING_CAN_CAST = 2
    FISHING_WAITING = 3
    FISHING_CAN_SINK = 4
    FISHING_CAN_REEL = 5
    GATHERING = 6


class Player:
    def __init__(self):
        self.x: float = 0
        self.y: float = 0
        self.z: float = 0
        self.last_x: float = 0
        self.last_y: float = 0
        self.last_z: float = 0
        self.movement_direction: int = 0
        self.bearing: int = 0
        self.should_have_moved = False
        self._is_moving = False
        self.last_move_time: int = 0
        self.move_duration: float = 0
        self.last_move_duration: float = 0
        self.maintain_bearing = None
        self.destination = ()
        self.points_of_interest = [
            (9221.578, 2674.259),
            (9112.5, 2657.5),
            (9110, 2646),
            (9094, 2645.5),
            (9052, 2627.5),
            (9034, 2596)
        ]
        self.point_index = 0
        self.bearing_offset_x = 0
        self.bearing_offset_y = 0
        self.reframes = 0
        self.distance_from_target = 0
        self.state = PlayerState.NONE

        self.bearing_queue = []

    @staticmethod
    def focus_game(title: str = "New World"):
        hwnd = win32gui.FindWindow(None, title)
        if hwnd:
            # <Bizarre workaround for SetForegroundWindow failing>
            shell = win32com.client.Dispatch("WScript.Shell")
            shell.SendKeys('%')
            # </Bizarre workaround for SetForegroundWindow failing>
            win32gui.SetForegroundWindow(hwnd)

        time.sleep(0.1)

    def is_moving(self):
        logging.debug(f"{time.time()} - {self.last_move_time} < {self.move_duration} = {time.time() - self.last_move_time < self.move_duration}")
        ret = time.time() - self.last_move_time < self.move_duration
        if not ret:
            self._is_moving = False
            self.move_duration = 0
        return ret

    def interact(self):
        Player.focus_game()
        pydirectinput.press('e')
        time.sleep(3)

    def distance_from(self, x: float, y: float):
        dist_x = pow(self.x - x, 2)
        dist_y = pow(self.y - y, 2)
        return math.sqrt(dist_x + dist_y)

    def angle_between(self, x: float, y: float):
        d_x = self.x - x
        d_y = self.y - y
        angle = math.degrees(math.atan2(d_x, d_y))

        return angle

    def click(self, duration: float = 0.01):
        pyautogui.mouseDown()
        time.sleep(duration)
        pyautogui.mouseUp()

    def fishing_cast(self):
        Player.focus_game()
        self.click()
        time.sleep(0.25)

    def fishing_sink_hook(self):
        Player.focus_game()
        self.click()

    def fishing_reel(self):
        Player.focus_game()
        for i in range(0, random.randint(1, 3)):
            self.click(duration=0.75)
        time.sleep(1.05)

    def move(self, distance: float = None, direction: int = None):
        Player.focus_game()

        if direction is not None: # and self.bearing:
            self.turn_to_bearing(direction)

        duration = 0
        if distance < 2.0:
            duration = 0.15
        elif distance < 5.0:
            duration = .25
        else:
            duration = distance / 20

        self._is_moving = True
        self.last_move_time = time.time()
        self.move_duration = duration
        self.last_move_duration = duration
        logging.debug(f"Moving for {duration} seconds")
        pyautogui.press('=')
        time.sleep(duration)
        pyautogui.press('s')

    def move_to(self, x: float, y: float, jitter: bool = False):
        if not self.x and not self.y:
            logging.debug("Wanted to move, but don't have position yet.")
            return

        if self.should_have_moved and self.last_x == self.x and self.last_y == self.y:
            self.turn_to_random_bearing()
            self.stuck()
            return

        self.last_x = self.x
        self.last_y = self.y
        self.last_z = self.z

        if jitter:
            random_x = (random.random() - 0.5)
            random_y = (random.random() - 0.5)
            # Minimize the jitter when we're close
            if self.distance_from_target < 10:
                random_x = random_x / 5
                random_y = random_y / 5
            x += random_x
            y += random_y

        logging.debug(f"Moving from {self.x}, {self.y} to {x}, {y}")
        logging.debug(f"d_x = {self.x - x}, d_y = {self.y - y}")
        # Determine if we're there.
        self.distance_from_target = self.distance_from(x, y)
        logging.debug(f"Distance from target: {self.distance_from_target}")
        if self.distance_from_target < 0.4:
            if len(self.destination) > 0:
                self.point_index += 1
                if self.point_index == len(self.points_of_interest):
                    self.point_index = 0
                self.destination = self.points_of_interest[self.point_index]

            self.should_have_moved = False
            return

        Player.focus_game()

        angle = round(self.angle_between(x, y))
        logging.debug(f"Bearing to target: {180 + angle}")
        self.turn_to_bearing(180 + angle)
        self.move(distance=self.distance_from_target)
        self.should_have_moved = True

    def move_to_destination(self):
        if len(self.destination) == 0:
            self.destination = self.points_of_interest[self.point_index]
            self.move_to(self.destination[0], self.destination[1], jitter=True)
            logging.debug(f"Moving to next point of interest at {self.destination}")
        else:
            self.move_to(self.destination[0], self.destination[1], jitter=True)

    def stuck(self):
        logging.debug("Appear to be stuck, moving randomly.")
        self.move(distance=self.distance_from_target)

    def turn_to_random_bearing(self):
        self.should_have_moved = False
        Player.focus_game()

        move_amount_x = random.randint(-180, 180)
        move_amount_y = random.randint(-180, 180)
        logging.debug(f"Turning randomly by {move_amount_x}, {move_amount_y}")
        self.bearing_offset_x += move_amount_x
        self.bearing_offset_y += move_amount_y
        self.reframes += 1
        pydirectinput.moveRel(move_amount_x, move_amount_y, relative=True)

        if self.reframes > 6:
            self.restore_bearing()
            self.reframes = 0
            self.stuck()

    def restore_bearing(self):
        Player.focus_game()

        pydirectinput.moveRel(0 - self.bearing_offset_x, 0 - self.bearing_offset_y)
        self.bearing_offset_x = 0
        self.bearing_offset_y = 0

    def turn_to_bearing(self, bearing: int = 0):
        Player.focus_game()

        degrees_to_turn = (bearing - self.bearing) % 360
        self.turn("New World", degrees_to_turn)

    def turn(self, title: str, degrees: int, left: bool = False):
        logging.debug(f"Starting to turn from bearing {self.bearing}")
        Player.focus_game()

        self.bearing = (self.bearing + degrees) % 360
        logging.debug(f"Adjusting bearing to {self.bearing}")

        if degrees > 180:
            degrees = 360 - degrees
            left = True
        # while degrees > 180:
        #     degrees -= 180
        #     left = not left

        pixel_per_degree = 20
        move_amount = degrees * pixel_per_degree
        if left:
            move_amount = 0 - move_amount

        logging.debug(f"Turning {'left' if left else 'right'} by {degrees}")
        pydirectinput.moveRel(move_amount, 0, relative=True)
        #self.bearing += (degrees + 180 if left else degrees)

    def update_bearing(self, bearing: Union[int, None]):
        if bearing is not None:
            self.bearing_queue.append(bearing)
            self.bearing = bearing

            if self.maintain_bearing is not None:
                if abs(self.maintain_bearing - bearing) > 2:
                    self.turn_to_bearing(self.maintain_bearing)

        if len(self.bearing_queue) > MAX_QUEUE_LENGTH:
            self.bearing_queue.pop()

    def update_state(self, state: PlayerState):
        self.state = state

        if self.state == PlayerState.FISHING_CAN_CAST:
            self.fishing_cast()
        elif self.state == PlayerState.FISHING_CAN_SINK:
            self.fishing_sink_hook()
        elif self.state == PlayerState.FISHING_CAN_REEL:
            self.fishing_reel()
        elif self.state == PlayerState.FISHING_WAITING:
            pass
