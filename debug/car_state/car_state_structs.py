
from dataclasses import dataclass


class Doors:
  pass

class Wheels:
  def __init__(self, wheel_speeds, wheel_brakes):
    self.wheel_speeds = wheel_speeds
    self.wheel_brakes = wheel_brakes

class GasPedal:
  def __init__(self, pressure, kickdown):
    self.pressure = pressure
    self.kickdown = kickdown

class SteeringWheel:
  pass

class GraButtons:
  def __init__(self, gra_hauptschalter, gra_abbrechen):
    self.hauptschalter = 0
    self.abbrechen = 0
    self.limiter = 0
    self.setzen = 0
    self.tip_hoch = 0
    self.tip_runter = 0
    self.wiederaufnahme = 0
    self.verstellung_zeitlücke = 0

class Transmission:
  # Gear and Parking brake
  pass

class Seatbelt:
  # Seatbelt status ? Heater ?
  pass

class StalkControls:
  pass

if __name__ == "__main__":
  pass