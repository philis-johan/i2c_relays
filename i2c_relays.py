"""
Relay control using I2C for the Grove 4 Channel SPDT Relay
"""
from smbus2 import SMBus
import time
import random
from typing import Callable
from argparse import ArgumentParser

"""
Documentation:
https://wiki.seeedstudio.com/Grove-4-Channel_SPDT_Relay/
https://github.com/Seeed-Studio/Multi_Channel_Relay_Arduino_Library
https://pypi.org/project/smbus2/
"""

RELAY_I2C_ADRESS = 0x11
RELAY_REGISTER = 0x10
ALLOWED_IDS = [1, 2, 3, 4]


class RelayBoard:
    """Class to control the relays"""
    state = 0b0000

    def __init__(self, initial_state: int = 0b0000, persistent: bool = False) -> None:
        """
        param initial_state: int, 0b0000-0b1111
        """
        self._relay_I2C_adress = RELAY_I2C_ADRESS
        self._relay_I2C_register = RELAY_REGISTER
        self.allowed_ids = ALLOWED_IDS
        self.persistent = persistent
        self.set_state(initial_state)
    
    def set_state(self, state: int) -> None:
        """Sets the state of the relays
        
        param state: int, 0b0000-0b1111
        """
        self.state = state
        with SMBus(1) as bus:
                bus.write_byte_data(self._relay_I2C_adress, self._relay_I2C_register, self.state) #type:ignore
    
    def switch(self, id: int) -> None:
        """Toggles the state of a relay
        
        param id: int, 1-4
        """
        if id not in self.allowed_ids:
            raise Exception(f"ID not in {self.allowed_ids = }")
        self.set_state(self.state ^ 2**(id-1))
    
    def turn_on(self, id: int) -> None:
        """Turns on a relay
        
        param id: int, 1-4
        """
        if id not in self.allowed_ids:
            raise Exception(f"ID not in {self.allowed_ids = }")
        self.set_state(self.state | 2**(id-1))
    
    def turn_off(self, id: int) -> None:
        """Turns off a relay
        
        param id: int, 1-4
        """
        if id not in self.allowed_ids:
            raise Exception(f"ID not in {self.allowed_ids = }")
        self.set_state(self.state & ~2**(id-1))

    def get_state(self) -> int:
        """Returns the state of the relays"""
        return self.state #type:ignore
    
    def __str__(self) -> str:
        state_1 = "1 is On" if self.get_state() & 2**(1-1) else "1 is Off"
        state_2 = "2 is On" if self.get_state() & 2**(2-1) else "2 is Off"
        state_3 = "3 is On" if self.get_state() & 2**(3-1) else "3 is Off"
        state_4 = "4 is On" if self.get_state() & 2**(4-1) else "4 is Off"

        return f"Relay {state_1}, {state_2}, {state_3}, {state_4}"
    
    def kill(self):
        """Turns off all relays"""
        for id in self.allowed_ids:
            self.turn_off(id)
    
    def __del__(self):
        """Turns off all relays"""
        if not self.persistent:
            self.kill()
    
    def __enter__(self):
        """Enter method for context manager"""
        return self
         
    def __exit__(self, exc_type: type[BaseException], exc_value: str, exc_traceback: str) -> None: #-type:ignore
        """Exit method for context manager
        Turns off all relays
        
        param exc_type: Exception type
        param exc_value: Exception value
        param exc_traceback: Exception traceback
        """
        self.__del__()


class Relay():
    '''Class to control a single relay'''
    def __init__(self, relay: RelayBoard, id: int, initially_on: bool=False) -> None:
        """
        param Relay: Relays object
        param id: int, 1-4
        param initially_on: bool, if True, relay will be turned on on init
        """
        self.relays: RelayBoard = relay
        if id not in self.relays.allowed_ids:
            raise Exception(f"ID not in {self.relays.allowed_ids = }")
        
        self.id: int = id
        if initially_on:
            self.on()
    
    def on(self) -> None:
        """Turns on the relay"""
        return self.relays.turn_on(self.id)
    
    def off(self) -> None:
        """Turns off the relay"""
        return self.relays.turn_off(self.id)
    
    def cycle(self, duration : float) -> None:
        """Turns on the relay for a given duration
        
        param duration: float, seconds
        """
        self.on()
        time.sleep(duration)
        self.off()

    def toggle(self) -> None:
        """Toggles the relay"""
        return self.relays.switch(self.id)
    
    def get_state(self):
        """Returns the state of the relays"""
        return "On" if self.relays.get_state() & 2**(self.id-1) else "Off"


def example(example: int):
    if example == 1:
        sleep_time = 1/20

        relays = RelayBoard(persistent=True)
        button_1 = Relay(relays, 1)
        disconnect_1 = Relay(relays, 2)
        button_2 = Relay(relays, 3)
        disconnect_2 = Relay(relays, 4)

        hardware = [button_1,  button_2, disconnect_1, disconnect_2]
        for hw in random.choices(hardware,k=100):
            hw.toggle()
            time.sleep(sleep_time)
    elif example == 2:
        def iter_func(func: Callable[[int], Relay], loop: list[int]) -> list[Relay]:
            return [func(i) for i in loop]

        with RelayBoard() as r:
            for relay in iter_func(lambda i: Relay(r,i), [1,2,3,4]):
                print("                                                     ",end="\r")
                relay.toggle()
                print(r,end="\r")
                time.sleep(1)
                print("                                                     ",end="\r")
                relay.toggle()
                print(r,end="\r")
                time.sleep(1)
            else:
                print()
    elif example == 3:
        with RelayBoard() as r:
            button3 = Relay(r,1)
            button3.on()
            time.sleep(1)
            print(button3.get_state())

def get_arguments():
    parser = ArgumentParser(description="add description")

    parser.add_argument("-r", '--relays', type=int, nargs="+",choices=[1, 2, 3, 4], help='isotope to test', default=None)
    parser.add_argument("-k", "--kill", action="store_true")
    parser.add_argument("-e", "--example", type=int, choices=[1,2,3], default=None)

    return parser.parse_args()

def test():
    bus = SMBus(1)
    relays = RelayBoard()
    for i in range(0, 0x99):
        print(f"Register: {i:>02x}")
        for state in range(0b1111+1):
            relays.set_state(state)
            time.sleep(0.1)
            # res = bin(bus.read_byte(0x11))
            res = bus.read_byte_data(0x11, i,force = True)
            # res = bus.read_block_data(0x11, i, force=True)
            # res = bus.read_i2c_block_data(0x11,i, 4)
            # res = bus.read_word_data(0x11, i)
            print(f"{state = :>04b} {res = }")
            # time.sleep(0.1)

def main():
    """
    Main program
    """
    args = get_arguments()
    if args.relays:
        r = RelayBoard(persistent=True)
        for id in args.relays:
            Relay(r,id).toggle()
    elif args.example:
        example(args.example)
    elif args.kill:
        RelayBoard()
    

if __name__ == "__main__":
    main()

