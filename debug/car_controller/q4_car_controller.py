from typing import Tuple

from debug.car_controller import q4can
from debug.car_state import q4_car_state
from opendbc.can import CANPacker
from opendbc.car.interfaces import CarControllerBase
from opendbc.car.volkswagen.values import CanBus, CarControllerParams

class CarController():
  AEB_CONTROL_STEP        = 100   # AWV_03 message frequency 1Hz
  AEB_HUD_STEP            = 20    # MEB_AWV_01 message frequency 5Hz
  LDW_STEP                = 10    # LDW_02 message frequency 10Hz
  ACC_HUD_STEP            = 6     # MEB_ACC_01 message frequency 16Hz
  STEER_DRIVER_ALLOWANCE  = 60    # Driver torque 0.6 Nm, begin steering reduction from MAX
  STEER_DRIVER_SLIGHT_PRESS = 15  # Driver torque 0.15 Nm for slight steering override detection
  STEER_DRIVER_MAX        = 300   # Driver torque 3.0 Nm, stop steering reduction at MIN
  STEERING_POWER_MAX      = 50    # HCA_03 maximum steering power, percentage
  STEERING_POWER_MIN      = 4     # HCA_03 minimum steering power, percentage
  STEERING_POWER_STEP     = 2     # HCA_03 steering power counter steps

  def __init__(self, dbc_names, CP, CP_SP):
    pass


  def update(self, car_state: q4_car_state.CarState):
    can_sends = []

    # **** Steering Controls *****************
    if self.frame % self.STEER_STEP == 0:
      hca_enabled = False
      apply_curvature = 0.0 # inactive curvature
      steering_power = 0
      can_sends.append(q4can.create_steering_control(self.packer_pt, self.CAN.pt, apply_curvature, hca_enabled, steering_power))

      # Pacify VW Emergency Assist driver inactivity
      stock_values = car_state.eps_stock_values
      simulated_torque = 0
      can_sends.append(q4can.create_eps_update(self.packer_pt, self.CAN.cam, stock_values, simulated_torque))

    # **** Blinker Controls *****************
    if self.frame % 2 == 0:
      blinker_active = CS.left_blinker_active or CS.right_blinker_active
      left_blinker = CC.leftBlinker if not blinker_active else False
      right_blinker = CC.rightBlinker if not blinker_active else False
      can_sends.append(q4can.create_blinker_control(self.packer_pt, self.CAN.pt, CS.ea_hud_stock_values, CS.ea_control_stock_values, left_blinker, right_blinker, self.hide_ea_error))

    # **** Acceleration Controls *****************
    # Needs a lot of debuging or coding in car for it to accept these values
    if self.frame % self.ACCEL_STEP == 0:
      can_sends.extend(self.CCS.create_acc_accel_control(self.packer_pt, self.CAN.pt, self.CP, CS.acc_type, CC.enabled,
                                                           self.long_jerk_control.get_jerk_up() if CC.longComfortMode else 4.0, self.long_jerk_control.get_jerk_down() if CC.longComfortMode else 4.0,
                                                           self.long_limit_control.get_upper_limit() if CC.longComfortMode else 0., self.long_limit_control.get_lower_limit() if CC.longComfortMode else 0.,
                                                           accel, acc_control, acc_hold_type, stopping, starting, CS.esp_hold_confirmation,
                                                           CS.out.vEgoRaw * CV.MS_TO_KPH, long_override, CS.travel_assist_available))


    # **** Radar disable *****************
    # if self.frame % self.AEB_CONTROL_STEP == 0:
    #   # can_sends.append(make_tester_present_msg(0x700, self.CAN.pt, suppress_response=True)) # Tester Present to keep the programming session
    #   can_sends.append(self.CCS.create_aeb_control(self.packer_pt, self.CAN.pt, self.CP)) # AEB Control (1 Hz)
    #
    #   if self.frame % self.CCP.AEB_HUD_STEP == 0:
    #     can_sends.append(self.CCS.create_aeb_hud(self.packer_pt, self.CAN.pt, self.radar_disabled_warning_timer < 600)) # AEB HUD (5 Hz), show deactivation for several seconds
    #
    #   if self.frame % 4 == 0:
    #     can_sends.append(self.CCS.create_radar_objects(self.packer_pt, self.CAN.pt)) # Radar Objects (25 Hz)

    # **** HUD Controls *****************
    # LDW: Lane Departure Warning
    if self.frame % self.LDW_STEP == 0:
      can_sends.append(self.CCS.create_lka_hud_control(self.packer_pt, self.CAN.pt, CS.ldw_stock_values, CC.latActive,
        CS.out.steeringPressed, hud_alert, hud_control, sound_alert))

    if self.frame % self.ACC_HUD_STEP == 0:
      can_sends.append(self.CCS.create_acc_hud_control(self.packer_pt, self.CAN.pt, acc_hud_status, hud_control.setSpeed * CV.MS_TO_KPH,
                                                         hud_control.leadVisible, hud_control.leadDistanceBars + 1, show_distance_bars,
                                                         CS.esp_hold_confirmation, distance, gap, fcw_alert, acc_hud_event, speed_limit))


    # **** Stock ACC Button Controls *****************

    # **** Retun actuatos and can_sends *****************
    self.frame += 1
    return can_sends