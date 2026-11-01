
# Get the list of interfaces from car_helpers and experiment
from opendbc.car.values import BRANDS
from opendbc.car.structs import CarParams, CarControl, CarControlSP
from panda import Panda
from opendbc.car.can_definitions import CanData
import time
from pprint import pprint

# Panda Setup
panda = Panda()

def _can_recv(wait_for_one: bool = False) -> list[list[CanData]]:
  recv = panda.can_recv()
  while len(recv) == 0 and wait_for_one:
    recv = panda.can_recv()
  return [[CanData(addr, dat, bus) for addr, dat, bus in recv], ]

def read(strict: bool = True):
  cs = CI.update([int(time.monotonic()*1e9), _can_recv()[0]])
  if strict:
    assert cs.canValid, "CAN went invalid, check connections"
  return cs

def write(cc: CarControl, c_sp: CarControlSP) -> None:
    print(f"Controls allowed: {cc.enabled} Panda: {panda.health()['controls_allowed']}")
    if cc.enabled and not panda.health()['controls_allowed']:
      # prevent the car from faulting. print a warning?
      cc = CarControl(enabled=False)
      c_sp = CarControlSP()
    _, can_sends = CI.apply(cc, c_sp)
    panda.can_send_many(can_sends, timeout=25)
    panda.send_heartbeat()

# Interface and Car Control Setup
def load_interfaces(brand_names):
  ret = {}
  for brand_name in brand_names:
    path = f'opendbc.car.{brand_name}'
    CarInterface = __import__(path + '.interface', fromlist=['CarInterface']).CarInterface
    for model_name in brand_names[brand_name]:
      ret[model_name] = CarInterface
  return ret


def _get_interface_names() -> dict[str, list[str]]:
  # returns a dict of brand name and its respective models
  brand_names = {}
  for brand in BRANDS:
    brand_name = brand.__module__.split('.')[-2]
    brand_names[brand_name] = [model.value for model in brand]

  return brand_names


# imports from directory opendbc/car/<name>/
interface_names = _get_interface_names()
interfaces = load_interfaces(interface_names)

# print(interface_names)
# print(interfaces)
candidate = "AUDI_Q4_MK1"

# fingerprint: dict[int, dict[int, int]]
# Taken with ignition off, see if problem
fingerprints = {0: {252: 48, 253: 8, 317: 32, 316495165: 8, 64: 8, 565: 8, 1312: 8, 1716: 8, 173: 8, 134: 8, 261: 8, 299: 8, 159: 8, 192: 32, 333: 32, 387: 64, 564: 64, 258: 48, 285: 8, 975: 8, 795: 8, 1124: 8, 981: 8, 522: 64, 960: 4, 792: 8, 316495015: 32, 316495081: 8, 278: 8, 313: 32, 267: 32, 332: 32, 988: 8, 523: 8, 518: 24, 389241616: 8, 1163: 8, 619: 8, 591: 64, 768: 48, 441800001: 8, 1622: 8, 1019: 8, 976: 8, 616: 32, 896: 8, 1710: 8, 380196094: 8, 599: 24, 316495086: 8}, 1: {252: 48, 253: 8, 207: 8, 64: 8, 316495165: 8, 1312: 8, 181: 8, 1716: 8, 869: 8, 173: 8, 167: 8, 168: 8, 134: 8, 246: 32, 452984950: 8, 261: 8, 190: 48, 316495056: 8, 316495057: 8, 299: 8, 247: 8, 626: 8, 192: 32, 333: 32, 258: 48, 795: 8, 1124: 8, 960: 4, 441800119: 8, 1452: 8, 267: 32, 278: 8, 313: 32, 324: 8, 330: 32, 332: 32, 374: 8, 316495015: 32, 1283: 8, 441800103: 8, 441800104: 8, 608: 8, 518: 24, 316494999: 16, 1057: 8, 591: 64, 380196006: 8, 441800001: 8, 1019: 8}, 2: {252: 48, 253: 8, 317: 32, 316495165: 8, 64: 8, 565: 8, 1312: 8, 1716: 8, 173: 8, 134: 8, 261: 8, 299: 8, 159: 8, 192: 32, 333: 32, 387: 64, 564: 64, 258: 48, 285: 8, 975: 8, 795: 8, 1124: 8, 981: 8, 522: 64, 960: 4, 792: 8, 316495015: 32, 316495081: 8, 278: 8, 313: 32, 267: 32, 332: 32, 988: 8, 523: 8, 518: 24, 389241616: 8, 1163: 8, 619: 8, 591: 64, 768: 48, 441800001: 8, 1622: 8, 1019: 8, 976: 8, 616: 32, 896: 8, 1710: 8, 380196094: 8, 599: 24}, 3: {}, 4: {}, 5: {}, 6: {}, 7: {}}
vin = "WAUZZZFZ8NP031807"
car_fw = []
alpha_long_allowed = False
is_release = False
is_release_sp = False
# print(interfaces[my_car])

CarInterface = interfaces[candidate]
CP: CarParams = CarInterface.get_params(candidate, fingerprints, car_fw, alpha_long_allowed, is_release, docs=False)
# print(CP)
CP.carVin = vin
CP.carFw = car_fw
# CP.fingerprintSource = source
# CP.fuzzyFingerprint = not exact_match
CP_SP = CarInterface.get_params_sp(CP, candidate, fingerprints, car_fw, alpha_long_allowed, is_release_sp, docs=False)

# sunnypilot_interfaces(CarInterface, CP, CP_SP, init_params_list_sp, can_recv, can_send)
CI = interfaces[CP.carFingerprint](CP, CP_SP)

# Initialize CarInterface and Panda
# safety_model = CI.CP.safetyConfigs[0].safetyModel
safety_model = CarParams.SafetyModel.volkswagenMeb

safety_param = CI.CP.safetyConfigs[0].safetyParam
panda.set_safety_mode(CarParams.SafetyModel.elm327, 1)
CI.init(CI.CP, CI.CP_SP, _can_recv, panda.can_send_many)
panda.set_safety_mode(safety_model, safety_param)

CC = CarControl(enabled=True)

C_SP = CarControlSP()

while True:
  # CC.actuators.accel = 0
  # CC.actuators.torque = 0
  # CC.leftBlinker = True

  pprint(CC)

  read(False)
  write(CC, C_SP)

  # 100Hz
  time.sleep(0.01)