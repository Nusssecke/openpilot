from panda import Panda
from opendbc.car.structs import CarParams # <- These are in car.capnp

from opendbc.car.car_helpers import get_car
from opendbc.car.can_definitions import CanData
from opendbc.car.structs import CarParams, CarControl, CarParamsT
from opendbc.car.vin import get_vin
from opendbc.can.parser import CANParser
from opendbc.can.dbc import DBC
from opendbc.car.can_definitions import CanRecvCallable, CanSendCallable
from opendbc.car.fw_versions import ObdCallback, get_fw_versions_ordered, get_present_ecus, match_fw_to_car
import time

from collections import Counter

def can_recv(self, wait_for_one: bool = False) -> list[list[CanData]]:
  "Package the data from the panda. Allows to wait for messages"
  recv = self.p.can_recv()
  while len(recv) == 0 and wait_for_one:
    recv = self.p.can_recv()
    return [[CanData(addr, dat, bus) for addr, dat, bus in recv], ]


# Initialize the car inteface
panda = Panda()
panda.reset()

# setup + fingerprinting
panda.set_safety_mode(CarParams.SafetyModel.elm327, 1)

# Variables used for fingerprinting
can_recv_callable: CanRecvCallable = can_recv
can_send_callable: CanSendCallable = panda.can_send_many
set_obd_multiplexing: ObdCallback = panda.set_obd
alpha_long_allowed: bool = True
is_release = False
# cached_params: CarParamsT = None
# fixed_fingerprint: str = ""
init_params_list_sp: list[dict[str, str]]
is_release_sp: bool = False

candidate, fingerprints, vin, car_fw, source, exact_match = fingerprint(can_recv, can_send, set_obd_multiplexing, cached_params,
                                                                          fixed_fingerprint)

if candidate is None:
  carlog.error({"event": "car doesn't match any fingerprints", "fingerprints": repr(fingerprints)})
  candidate = "MOCK"

CarInterface = interfaces[candidate]
CP: CarParams = CarInterface.get_params(candidate, fingerprints, car_fw, alpha_long_allowed, is_release, docs=False)
CP.carVin = vin
CP.carFw = car_fw
CP.fingerprintSource = source
CP.fuzzyFingerprint = not exact_match
CP_SP = CarInterface.get_params_sp(CP, candidate, fingerprints, car_fw, alpha_long_allowed, is_release_sp, docs=False)

sunnypilot_interfaces(CarInterface, CP, CP_SP, init_params_list_sp, can_recv, can_send)
CI = interfaces[CP.carFingerprint](CP, CP_SP)

assert CI.CP.carFingerprint.lower() != "mock", "Unable to identify car. Check connections and ensure car is supported."

safety_model = CI.CP.safetyConfigs[0].safetyModel
panda.set_safety_mode(CarParams.SafetyModel.elm327, 1)
CI.init(CI.CP, can_recv, panda.can_send_many)
panda.set_safety_mode(safety_model, CI.CP.safetyConfigs[0].safetyParam)


# p = PandaRunner()
# CC = CarControl(enabled=False)
  # while True:
    # CC.actuators.accel = float(4.0*np.clip(joystick.axes_values['gb'], -1, 1))
    # CC.actuators.torque = float(np.clip(joystick.axes_values['steer'], -1, 1))
    # print(CC)

    # p.read()
    # p.write(CC)

    # 100Hz
    # time.sleep(0.01)
