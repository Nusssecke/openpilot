from panda import Panda
from opendbc.car.structs import CarParams # <- These are in car.capnp

from opendbc.car.car_helpers import get_car
from opendbc.car.can_definitions import CanData
from opendbc.car.structs import CarParams, CarControl
from opendbc.car.vin import get_vin
from opendbc.can.parser import CANParser
from opendbc.can.dbc import DBC

from collections import Counter

panda = Panda()


def receive():
  panda.reset() # Test if necessary

  panda.set_safety_mode(CarParams.SafetyModel.allOutput, 0) # There is a second argument (1) what does it do? # volkswagenMeb
  panda.set_canfd_auto(0, True) # This seems not necessary but why not?
  panda.set_canfd_auto(1, True)
  panda.set_canfd_auto(2, True)
  # print(f"Panda Health: {panda.health()}")
  # print(f"Panda CAN 0: {panda.can_health(0)}")

  messages = panda.can_recv()
  can_data = []

  # Make what the can parser wants?
  adresses = [msg[0] for msg in messages if msg[2] == 0]
  shortend_messages = [[k,v] for k,v in Counter(adresses).items()]
  print(shortend_messages)
  print([[hex(msg[0]), msg[1]] for msg in shortend_messages])

  # for rx_addr, rx_data_bytearray, rx_bus in messages:
    # print(f"{rx_addr=}, {rx_data_bytearray=}, {rx_bus=}")
    # print(dbc.addr_to_msg.get(rx_addr))
    # can_data.append(CanData(rx_addr, rx_data_bytearray, rx_bus)) # I don't know where or how to use this yet

  # dbc = DBC("vw_meb")
  # print(dbc.addr_to_msg.get(messages[0][0]))

  parser = CANParser("vw_meb", shortend_messages, 0)
  print(parser.vl["ESP_19"]["ESP_VL_Radgeschw_02"])
  # print(parser.addresses)
  # print(parser.bus)
  # print(parser.vl)

  # vin_rx_addr, vin_rx_bus, vin = get_vin(can_recv, panda.can_send_many, (0, 1))
  # print(f"{vin_rx_addr=}, {vin_rx_bus=}, {vin=}")
  # Expected Value: WAUZZZFZ8NPO31807

  # CI = get_car(can_recv, panda.can_send_many, panda.set_obd, True, False)
  # print(CI)
  # assert CI.CP.carFingerprint.lower() != "mock", "Unable to identify car"

def can_recv(wait_for_one: bool = False) -> list[list[CanData]]:
    """Function to pass along that read can messages and returns CanData"""
    recv = panda.can_recv()
    # print(f"Can Message: {recv}")
    while len(recv) == 0 and wait_for_one:
      recv = panda.can_recv()
      # print(f"Can Message: {recv}")
    return [[CanData(addr, dat, bus) for addr, dat, bus in recv], ]


def send():
  panda.set_safety_mode(CarParams.SafetyModel.allOutput, 1)
  panda.can_send(0x1aa, b'message', 0)


if __name__ == "__main__":
  receive()