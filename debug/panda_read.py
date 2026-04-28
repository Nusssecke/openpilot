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

panda = Panda()

panda.reset() # Test if necessary
panda.set_safety_mode(CarParams.SafetyModel.allOutput, 0) # <- Might have something do to with all the car popups

def read():
  parser = CANParser("vw_meb", [], 1)

  while(True):
      messages = panda.can_recv()
      can_data = [CanData(rx_addr, rx_data_bytearray, rx_bus) for rx_addr, rx_data_bytearray, rx_bus in messages]

      can_data = [int(time.monotonic() * 1e9), can_data] # Add when the data was received

      parser.update(can_data)
      doors = parser.vl["ZV_02"] if bool(parser.vl["Gateway_72"]["ZV_02_alt"]) else parser.vl["Gateway_72"]
      print(f"Door: {doors["ZV_FT_offen"]}")


# self.p.set_safety_mode(CarParams.SafetyModel.noOutput)
# self.p.reset()  # avoid siren
# return super().__exit__(exc_type, exc_value, traceback)