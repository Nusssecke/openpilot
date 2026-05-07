from panda import Panda
from opendbc.car.can_definitions import CanData
from opendbc.can.parser import CANParser
import time

# This snippet reads out the can bus from the panda and uses the parser to read out if a door is open

panda = Panda()

def read():
  parser = CANParser("vw_meb", [], 1)

  while(True):
      messages = panda.can_recv()
      can_data = [CanData(rx_addr, rx_data_bytearray, rx_bus) for rx_addr, rx_data_bytearray, rx_bus in messages]
      can_data = [int(time.monotonic() * 1e9), can_data] # Add when the data was received

      parser.update(can_data)
      doors = parser.vl["ZV_02"] if bool(parser.vl["Gateway_72"]["ZV_02_alt"]) else parser.vl["Gateway_72"]
      print(f"Door: {doors['ZV_FT_offen']}")

if __name__ == "__main__":
  read()
