import threading

from opendbc.can.parser import CANParser
from opendbc.car import Bus
from panda import Panda
from opendbc.car.structs import CarParams # <- These are in car.capnp

from opendbc.car.car_helpers import get_car
from opendbc.car.can_definitions import CanData
from opendbc.car.structs import CarParams, CarControl
from opendbc.car.vin import get_vin
from opendbc.can.parser import CANParser
from opendbc.can.packer import CANPacker
from opendbc.can.dbc import DBC
import time

from collections import Counter
from debug.car_state.q4_car_state import CarState

def panda_update(panda, car_state):
  can_parsers = get_can_parsers_meb()

  while(True):
    messages = panda.can_recv()
    can_data = [CanData(rx_addr, rx_data_bytearray, rx_bus) for rx_addr, rx_data_bytearray, rx_bus in messages]
    can_data = [int(time.monotonic() * 1e9), can_data] # Add when the data was received
    for parser in can_parsers.values():
      parser.update(can_data)

    car_state.update(can_parsers)


def get_can_parsers_meb():
    pt_messages = [
      # frequency changes too much for the CANParser to figure out
      ("Blinkmodi_02", 1),  # From J519 BCM (sent at 1Hz when no lights active, 50Hz when active)
      ("SMLS_01", 1),       # From Stalk Controls
    ]

    cam_messages = []
    # if not (CP.flags & VolkswagenFlags.DISABLE_RADAR):
    #   cam_messages.append(("AWV_03", 1)) # Front Collision Detection (1 Hz when inactive, 50 Hz when active)

    return {
      Bus.pt: CANParser("vw_meb", pt_messages, 0),
      Bus.cam: CANParser("vw_meb", cam_messages, 2),
      Bus.alt: CANParser("vw_meb", [], 1),
    }


def create_active_car_state():
  panda = Panda()

  # panda.reset() # Test if necessary
  # panda.set_safety_mode(CarParams.SafetyModel.allOutput, 0) # <- Might have something do to with all the car popups

  car_state = CarState()

  threading.Thread(target=panda_update, args=(panda, car_state), daemon=True).start()

  # Wait for the Thread to start and the car_state to have updated before reading out values
  time.sleep(1)

  return car_state

if __name__ == "__main__":
  car_state = create_active_car_state()
  while True:
    print(car_state.diagnose_01_values)
    time.sleep(0.1)