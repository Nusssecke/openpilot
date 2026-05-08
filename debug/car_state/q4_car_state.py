from debug.car_state.car_state_structs import GasPedal, Wheels
from opendbc.car.interfaces import CarStateBase, GearShifter
from opendbc.car.structs import CarParams
from opendbc.can import CANParser
from opendbc.car import Bus, structs
from enum import StrEnum

from opendbc.car.volkswagen.values import NetworkLocation, VolkswagenFlags
from openpilot.common.constants import CV

class CarState():

  def __init__(self):
    pass

  def update(self, can_parsers: dict[StrEnum, CANParser]):
    # Set up can parsers
    pt_cp = can_parsers[Bus.pt] # Powertrain CANParser
    cam_cp = can_parsers[Bus.cam] # Camera CANParser
    # ext_cp = cam_cp # Exterior, Lights, Mirrors, Doors
    alt_cp = can_parsers[Bus.alt] # Alternative / Auxiliary

    # Update vehicle speed and acceleration from ABS wheel speeds.
    esc_51 = pt_cp.vl["ESC_51"]
    wheel_speeds = [esc_51["VL_Radgeschw"], esc_51["VR_Radgeschw"], esc_51["HL_Radgeschw"], esc_51["HR_Radgeschw"]]
    wheel_brakes = [esc_51["VL_Brake_Pressure"], esc_51["VR_Brake_Pressure"], esc_51["HL_Brake_Pressure"], esc_51["HR_Brake_Pressure"]]
    self.wheels = Wheels(wheel_speeds=wheel_speeds, wheel_brakes=wheel_brakes)

    # VIN
    self.vin = "".join([chr(pt_cp.vl["VIN_01"][f"VIN_{i}"]) for i in range(1, 18)])
    assert self.vin == "WAUZZZFZ8NP031807"

    # Gear
    self.gear1 = pt_cp.vl["Gateway_73"]["GE_Fahrstufe"]
    self.gear2 = pt_cp.vl["Getriebe_11"]["GE_Fahrstufe"]
    assert self.gear1 == self.gear2

    # Parking Brake
    self.parkingBrake = pt_cp.vl["Gateway_73"]["EPB_Status"]

    # Accelerator Pedal
    accelerator_pressure   = pt_cp.vl["Motor_54"]["Accelerator_Pressure"] > 0 # MQBevo offset is not reliable (fluctuation or different statically in small range)
    accel_pedal_pressure = pt_cp.vl["Motor_51"]["Accel_Pedal_Pressure"] > 0 # detects accel pedal "a little bit" later than ["Motor_54"]["Accelerator_Pressure"]
    assert accelerator_pressure == accel_pedal_pressure

    # kickdown
    # Candidates
    # pt_cp.vl["Motor_51"]["MO_Kickdown"] <- More likely
    # pt_cp.vl["Motor_51"]["Accel_Low_Pressed_Support"]
    self.kickdown = 0
    self.gasPedal = GasPedal(accelerator_pressure, self.kickdown)

    # Brakes
    self.brakePressed = bool(pt_cp.vl["Motor_14"]["MO_Fahrer_bremst"]) # includes regen braking by user
    self.brake        = pt_cp.vl["ESC_51"]["Brake_Pressure"]


    # Update door and trunk/hatch lid open status.
    doors = pt_cp.vl["ZV_02"] if bool(pt_cp.vl["Gateway_72"]["ZV_02_alt"]) else pt_cp.vl["Gateway_72"]
    self.doorOpen = any([doors["ZV_FT_offen"], doors["ZV_BT_offen"], doors["ZV_HFS_offen"], doors["ZV_HBFS_offen"], doors["ZV_HD_offen"]])


    # Update seatbelt fastened status.
    seatbelts = pt_cp.vl["Airbag_02"]
    self.seatbelts = [
       seatbelts["AB_Gurtschloss_FA"],
       seatbelts["AB_Gurtschloss_BF"],
       seatbelts["AB_Gurtschloss_Reihe2_FA"],
       seatbelts["AB_Gurtschloss_Reihe2_MI"],
       seatbelts["AB_Gurtschloss_Reihe2_BF"]
    ]


    # Display
    # pt_cp.vl["Dimmung_01"]["DI_Diplay_Nachtdesign"] # Nachtdesign

    # Multifunktionslenkrad
    # MFL_01


    # Verkehrszeichenerkennung
    cam_cp.vl["VZE_04"]["VZE_Verkehrzeichen_1"] # Erlaubtes Tempolimit



    # GRA: Geschwindigkeitsregelanlage
    self.gra_hauptschalter = pt_cp.vl["GRA_ACC_01"]["GRA_Hauptschalter"]
    # GRA_ACC_01 seems to have mainly button information


    # ACC: Adaptive Cruise Control, Abstandsregeltempomat
    # ACC_18, ACC_19


    # Update EPS position and state info. For signed values, VW sends the sign in a separate signal.
    # LWI_01, MEP_EPS_01 steering angle differs from real steering angle (dynamic steering)
    self.steeringAngleDeg = pt_cp.vl["LWI_01"]["LWI_Lenkradwinkel"] * (1, -1)[int(pt_cp.vl["LWI_01"]["LWI_VZ_Lenkradwinkel"])]
    self.steeringRateDeg  = pt_cp.vl["LWI_01"]["LWI_Lenkradw_Geschw"] * (1, -1)[int(pt_cp.vl["LWI_01"]["LWI_VZ_Lenkradw_Geschw"])]

    self.steeringTorque   = pt_cp.vl["LH_EPS_03"]["EPS_Lenkmoment"] * (1, -1)[int(pt_cp.vl["LH_EPS_03"]["EPS_VZ_Lenkmoment"])]
    self.steeringPressed  = abs(self.steeringTorque) > 0 # self.CCP.STEER_DRIVER_ALLOWANCE
    self.steeringSlightlyPressed = abs(self.steeringTorque) > 0 # self.CCP.STEER_DRIVER_SLIGHT_PRESS
    self.steeringCurvature = -pt_cp.vl["QFK_01"]["Curvature"] * (1, -1)[int(pt_cp.vl["QFK_01"]["Curvature_VZ"])]

    self.yawRate = -pt_cp.vl["ESC_50"]["Yaw_Rate"] * (1, -1)[int(pt_cp.vl["ESC_50"]["Yaw_Rate_Sign"])] * CV.DEG_TO_RAD

    # self.hca_status = self.CCP.hca_status_values.get(pt_cp.vl["QFK_01"]["LatCon_HCA_Status"])
    # self.steerFaultTemporary, self.steerFaultPermanent = self.update_hca_state(self.hca_status, drive_mode=self.drive_mode)

    # TODO: Move all messages that need to be passed along together
    # VW Emergency Assist status tracking and mitigation
    self.eps_stock_values = pt_cp.vl["LH_EPS_03"]
    # self.klr_stock_values = pt_cp.vl["KLR_01"] # if self.CP.flags & VolkswagenFlags.STOCK_KLR_PRESENT else {}
    # self.carFaultedNonCritical = cam_cp.vl["EA_01"]["EA_Funktionsstatus"] in (3, 4, 5, 6) # emergency assist always present also if not coded

    # Consume blind-spot monitoring info/warning LED states, if available.
    # Infostufe: BSM LED on, Warnung: BSM LED flashing
    # if self.CP.enableBsm:
    #   bsm_bus = pt_cp if self.CP.flags & (VolkswagenFlags.MEB_GEN2 | VolkswagenFlags.MQB_EVO) else ext_cp
    #   blindspot_driver    = bool(bsm_bus.vl["MEB_Side_Assist_01"]["Blind_Spot_Info_Driver"]) or bool(bsm_bus.vl["MEB_Side_Assist_01"]["Blind_Spot_Warn_Driver"])
    #   blindspot_passenger = bool(bsm_bus.vl["MEB_Side_Assist_01"]["Blind_Spot_Info_Passenger"]) or bool(bsm_bus.vl["MEB_Side_Assist_01"]["Blind_Spot_Warn_Passenger"])
    #   car_is_lhd = True if not self.force_rhd_for_bsm else False # TODO
    #   self.leftBlindspot  = blindspot_driver if car_is_lhd else blindspot_passenger
    #   self.rightBlindspot = blindspot_passenger if car_is_lhd else blindspot_driver

    # Consume factory LDW data relevant for factory SWA (Lane Change Assist)
    # and capture it for forwarding to the blind spot radar controller
    self.ldw_stock_values = cam_cp.vl["LDW_02"]

    # self.stockFcw = bool(ext_cp.vl["AWV_03"]["FCW_Active"]) if not (self.CP.flags & VolkswagenFlags.DISABLE_RADAR) else False # currently most plausible candidate
    # self.stockAeb = False #bool(pt_cp.vl["VMM_02"]["AEB_Active"]) TODO find correct signal

    # self.acc_type                = ext_cp.vl["ACC_18"]["ACC_Typ"] if not (self.CP.flags & VolkswagenFlags.DISABLE_RADAR) else 2 # 2: acc stop and go
    self.travel_assist_available = bool(cam_cp.vl["TA_01"]["Travel_Assist_Available"])

    self.cruiseState_available = pt_cp.vl["Motor_51"]["TSK_Status"] in (2, 3, 4, 5)
    self.cruiseState_enabled   = pt_cp.vl["Motor_51"]["TSK_Status"] in (3, 4, 5)

    # if self.CP.pcmCruise:
      # Cruise Control mode; check for distance UI setting from the radar.
      # ECM does not manage this, so do not need to check for openpilot longitudinal
    # self.cruiseState.nonAdaptive = bool(ext_cp.vl["ACC_19"]["ACC_Limiter_Mode"])
    #else:
      # Speed limiter mode; ECM faults if we command ACC while not pcmCruise
    #  self.cruiseState.nonAdaptive = bool(pt_cp.vl["Motor_51"]["TSK_Limiter_ausgewaehlt"])

    self.accFaulted = pt_cp.vl["Motor_51"]["TSK_Status"] in (6, 7)
    # self.accFaulted = self.update_acc_fault(accFaulted, parking_brake=self.parkingBrake, drive_mode=drive_mode)

    # ret.radarDisableFailed = True if RADAR_DISABLE_STATE["error"] == True and self.CP.flags & VolkswagenFlags.DISABLE_RADAR else False

    # for hold detection: VMM_02 ESP_Hold Signal is off timing and probably wrong
    # use a motion state signal instead for now
    # self.esp_hold_confirmation = pt_cp.vl["ESC_50"]["Motion_State"] == 3 # full stop

    # self.cruiseState.standstill = self.CP.pcmCruise and self.esp_hold_confirmation

    # Update ACC setpoint. When the setpoint is zero or there's an error, the
    # radar sends a set-speed of ~90.69 m/s / 203mph.
    # if self.CP.pcmCruise:
    #   self.cruiseState.speed = int(round(ext_cp.vl["ACC_19"]["ACC_Wunschgeschw_02"])) * CV.KPH_TO_MS
    #   if self.cruiseState.speed > 90:
    #     self.cruiseState.speed = 0

    # Update button states for turn signals and ACC controls, capture all ACC button state/config for passthrough
    # turn signal effect
    self.left_blinker_active  = bool(pt_cp.vl["Blinkmodi_02"]["BM_links"])
    self.right_blinker_active = bool(pt_cp.vl["Blinkmodi_02"]["BM_rechts"])
    # turn signal cause (see door logic same schema ["Gateway_72"]["SMLS_01_alt"] is not neccessary -> SMLS_01 seems to always work)
    # self.leftBlinker, self.rightBlinker = self.update_blinker_from_stalk(240, pt_cp.vl["SMLS_01"]["BH_Blinker_li"],
    #                                                                         pt_cp.vl["SMLS_01"]["BH_Blinker_re"])

    # Additional safety checks performed in CarInterface.
    self.espDisabled = bool(pt_cp.vl["ESP_21"]["ESP_Tastung_passiv"]) # this is also true for ESC Sport mode
    self.espActive   = bool(pt_cp.vl["ESP_21"]["ESP_Eingriff"])

    self.ea_hud_stock_values = cam_cp.vl["EA_02"]
    self.ea_control_stock_values = cam_cp.vl["EA_01"]

    self.fuelGauge = pt_cp.vl["Motor_16"]["MO_Energieinhalt_BMS"]

    # EV battery details
    self.charge = pt_cp.vl["Motor_16"]["MO_Energieinhalt_BMS"] # battery charge WattHours
    if True: # self.CP.networkLocation == NetworkLocation.gateway:
        self.heaterActive = bool(alt_cp.vl["MEB_HVEM_03"]["PTC_ON"]) # battery heater active
        self.voltage      = alt_cp.vl["MEB_HVEM_01"]["Battery_Voltage"] # battery voltage
        self.capacity     = alt_cp.vl["BMS_04"]["BMS_Kapazitaet_02"] * self.voltage # EV battery capacity WattHours
        self.soc          = self.charge / self.capacity * 100 if self.capacity > 0 else 0 # battery SoC in percent
        self.power        = alt_cp.vl["MEB_HVEM_01"]["Engine_Power"] # engine power output
        self.temperature  = alt_cp.vl["DCDC_03"]["DC_Temperatur"] # dcdc converter temperature

    # MadsCarState.update_mads(self, ret, pt_cp, hca_status)

    # self.frame += 1
    # return ret, ret_sp
