from typing import Tuple

from opendbc.can import CANPacker
from opendbc.car import make_tester_present_msg
from opendbc.car.interfaces import CarControllerBase
from opendbc.car.volkswagen.values import CanBus, CarControllerParams
from opendbc.sunnypilot.car.hyundai.tests.test_tuning_controller import CS

class CarController():
  def __init__(self, dbc_names, CP, CP_SP):
    pass

    # self.CCP = CarControllerParams(CP)

  def update(self, CC, CC_SP, now_nanos):
    hud_control = CC.hudControl
    can_sends = []

    # **** Steering Controls *****************
    if self.frame % self.CCP.STEER_STEP == 0:
      # can_sends.append(self.CCS.create_steering_control(self.packer_pt, self.CAN.pt, apply_curvature, hca_enabled, steering_power))
      # self.apply_curvature_last = apply_curvature
      # self.steering_power_last = steering_power


      # if self.CP.flags & VolkswagenFlags.STOCK_HCA_PRESENT:
      pass

    # **** Blinker Controls *****************
    if self.frame % 2 == 0:
      blinker_active = CS.left_blinker_active or CS.right_blinker_active
      left_blinker = CC.leftBlinker if not blinker_active else False
      right_blinker = CC.rightBlinker if not blinker_active else False
      can_sends.append(mebcan.create_blinker_control(self.packer_pt, self.CAN.pt, CS.ea_hud_stock_values, CS.ea_control_stock_values, left_blinker, right_blinker, self.hide_ea_error))

    # **** Acceleration Controls *****************
    if self.frame % self.CCP.ACCEL_STEP == 0:
      pass

    # **** Radar disable *****************
    if self.frame % self.CCP.AEB_CONTROL_STEP == 0:
      can_sends.append(make_tester_present_msg(0x700, self.CAN.pt, suppress_response=True)) # Tester Present to keep the programming session
      can_sends.append(self.CCS.create_aeb_control(self.packer_pt, self.CAN.pt, self.CP)) # AEB Control (1 Hz)

      if self.frame % self.CCP.AEB_HUD_STEP == 0:
        can_sends.append(self.CCS.create_aeb_hud(self.packer_pt, self.CAN.pt, self.radar_disabled_warning_timer < 600)) # AEB HUD (5 Hz), show deactivation for several seconds

      if self.frame % 4 == 0:
        can_sends.append(self.CCS.create_radar_objects(self.packer_pt, self.CAN.pt)) # Radar Objects (25 Hz)

    # **** HUD Controls *****************
    # LDW: Lane Departure Warning
    if self.frame % self.CCP.LDW_STEP == 0:
      can_sends.append(self.CCS.create_lka_hud_control(self.packer_pt, self.CAN.pt, CS.ldw_stock_values, CC.latActive,
        CS.out.steeringPressed, hud_alert, hud_control, sound_alert))

    if self.frame % self.CCP.ACC_HUD_STEP == 0:
      can_sends.append(self.CCS.create_acc_hud_control(self.packer_pt, self.CAN.pt, acc_hud_status, hud_control.setSpeed * CV.MS_TO_KPH,
                                                         hud_control.leadVisible, hud_control.leadDistanceBars + 1, show_distance_bars,
                                                         CS.esp_hold_confirmation, distance, gap, fcw_alert, acc_hud_event, speed_limit))


    # **** Stock ACC Button Controls *****************

    # **** Retun actuatos and can_sends *****************
    return can_sends