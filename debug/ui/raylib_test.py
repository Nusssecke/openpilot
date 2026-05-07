import pyray as rl

from debug import car_state_test

# Incorporate the whole gui stack from openpilot

# car_state = car_state_test.create_active_car_state()

# Initialization
screenWidth = 800
screenHeight = 450
rl.init_window(screenWidth, screenHeight, "Q4 - Car State / Control")

# wait for key press
while not rl.window_should_close():
    rl.begin_drawing()
    rl.clear_background(rl.RAYWHITE)

    rl.draw_text("Q4 car_state.doorOpens", 190, 200, 20, rl.LIGHTGRAY)

    rl.end_drawing()