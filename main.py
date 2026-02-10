from vex import *

# Brain and Controller
brain = Brain()
controller = Controller()

# Motor Setup: 4-Motor Drive (1:1 Ratio / 18:1 Green Cartridges)
left_motor_1 = Motor(Ports.PORT1, GearSetting.RATIO_18_1, False)
left_motor_2 = Motor(Ports.PORT2, GearSetting.RATIO_18_1, False)
right_motor_1 = Motor(Ports.PORT9, GearSetting.RATIO_18_1, True)
right_motor_2 = Motor(Ports.PORT10, GearSetting.RATIO_18_1, True)

intake_conv = Motor(Ports.PORT3, GearSetting.RATIO_18_1, False)
fly = Motor(Ports.PORT8, GearSetting.RATIO_6_1, True)

scoop = DigitalOut(brain.three_wire_port.a)
descore_wing = DigitalOut(brain.three_wire_port.d)

# Group motors 
left_drive = MotorGroup(left_motor_1, left_motor_2)
right_drive = MotorGroup(right_motor_1, right_motor_2)

wait(20, MSEC)

# ----------------------------------------------------
# COMPLETION WAITING UTILITIES
# ----------------------------------------------------

def wait_for_drive_complete(timeout_sec=5.0):
    timer = 0
    while timer < timeout_sec:
        if controller.buttonRight.pressing():
            stop_drive()
            return False
        
        # Check if motors are still spinning
        # NOT DONE means still moving (spinning)
        if not (left_motor_1.is_spinning() or left_motor_2.is_spinning() or 
                right_motor_1.is_spinning() or right_motor_2.is_spinning()):
            return True
        
        wait(20, MSEC)
        timer += 0.02
    
    stop_drive()
    return False

def wait_for_intake_complete(timeout_sec=2.0):
    timer = 0
    while timer < timeout_sec:
        if controller.buttonRight.pressing():
            stop_intake()
            return False
        if intake_conv.is_done() and fly.is_done():
            return True
        wait(20, MSEC)
        timer += 0.02
    return False

# ----------------------------------------------------
# DRIVE PRIMITIVES (Non-blocking start + wait wrapper)
# ----------------------------------------------------

def drive_distance(turns, velocity_percent=70, timeout_sec=5.0):
    # Set velocity first
    left_drive.set_velocity(velocity_percent, PERCENT)
    right_drive.set_velocity(velocity_percent, PERCENT)
    
    # Start non-blocking movement to relative position
    left_drive.spin_for(FORWARD, turns, TURNS, wait=False)
    right_drive.spin_for(FORWARD, turns, TURNS, wait=False)
    
    # Wait for completion
    return wait_for_drive_complete(timeout_sec)

def turn_in_place(turns, velocity_percent=50, timeout_sec=5.0):
    left_drive.set_velocity(velocity_percent, PERCENT)
    right_drive.set_velocity(velocity_percent, PERCENT)
    
    # Left forward, Right reverse for pivot turn
    left_drive.spin_for(FORWARD, turns, TURNS, wait=False)
    right_drive.spin_for(REVERSE, turns, TURNS, wait=False)
    
    return wait_for_drive_complete(timeout_sec)

def drive_to_absolute(left_pos, right_pos, velocity_percent=70, timeout_sec=3.0):
    left_drive.set_velocity(velocity_percent, PERCENT)
    right_drive.set_velocity(velocity_percent, PERCENT)
    
    left_drive.spin_to_position(left_pos, TURNS, wait=False)
    right_drive.spin_to_position(right_pos, TURNS, wait=False)
    
    return wait_for_drive_complete(timeout_sec)

# ----------------------------------------------------
# INTAKE PRIMITIVES
# ----------------------------------------------------

def intake_in(duration_sec=1.0, speed=100):
    intake_conv.spin(REVERSE, speed, PERCENT)
    fly.spin(REVERSE, speed, PERCENT)
    
    # Simple time-based wait (intake doesn't have position targets)
    timer = 0
    while timer < duration_sec:
        if controller.buttonRight.pressing():
            stop_intake()
            return False
        wait(20, MSEC)
        timer += 0.02
    
    stop_intake()
    return True

def fire_flywheel(duration_sec=1.0, speed=100):
    fly.spin(FORWARD, speed, PERCENT)
    
    timer = 0
    while timer < duration_sec:
        if controller.buttonRight.pressing():
            stop_intake()
            return False
        wait(20, MSEC)
        timer += 0.02
    
    fly.stop()
    return True

# ----------------------------------------------------
# PNEUMATIC CONTROLS
# ----------------------------------------------------

def set_scoop(state):
    scoop.set(state)
    wait(200, MSEC)  # Allow pneumatic actuation time

def set_wing(state):
    descore_wing.set(state)
    wait(200, MSEC)

# ----------------------------------------------------
# STOP FUNCTIONS
# ----------------------------------------------------

def stop_drive():
    left_drive.stop()
    right_drive.stop()

def stop_intake():
    intake_conv.stop()
    fly.stop()


# ----------------------------------------------------
# AUTO ############################################### 
# ----------------------------------------------------

def run_autonomous_stupid():
    brain.screen.clear_screen()
    brain.screen.print("Auto Started")
    
    # Step 1: Drive forward 2 turns
    brain.screen.set_cursor(2, 1)
    brain.screen.print("Step 1: Forward")
    if not drive_distance(2, velocity_percent=70):
        return  # Emergency stopped
    
    # Step 2: Turn 90 degrees 
    brain.screen.set_cursor(3, 1)
    brain.screen.print("Step 2: Turn")
    if not turn_in_place(0.3, velocity_percent=50):
        return
    
    brain.screen.set_cursor(6, 1)
    brain.screen.print("Auto Complete!")
    
    # ================================================
    # HOW TO ADD MORE STEPS:
    # ================================================
    # brain.screen.print("Step 3: Intake")
    # if not intake_in(1.5, speed=80):  # Try step 3
    #     return  # Stop if fails
    #
    # brain.screen.set_cursor(5, 1)
    # brain.screen.print("Step 4: Shoot")
    # if not fire_flywheel(2.0):  # Try step 4
    #     return  # Stop if fails
    # ================================================

# ----------------------------------------------------
# USER CONTROL 
# ----------------------------------------------------

def run_user_control():
    while True:
        forward = controller.axis3.position()
        turn = controller.axis1.position()
        
        speed_mod = 1.0 if controller.buttonR2.pressing() else (0.3 if controller.buttonR1.pressing() else 0.6)
        
        left_speed = (forward + turn) * speed_mod
        right_speed = (forward - turn) * speed_mod
        
        left_drive.spin(FORWARD, left_speed, PERCENT)
        right_drive.spin(FORWARD, right_speed, PERCENT)
        
        # Intake controls
        fly_i_power = 40 if controller.buttonA.pressing() else 100
        if controller.buttonL1.pressing() and controller.buttonL2.pressing():
            l1_l2(fly_i_power)
        elif controller.buttonL1.pressing():
            l1(fly_i_power, fly_i_power)
        elif controller.buttonL2.pressing():
            l2(fly_i_power, fly_i_power)
        else:
            stop_intake()
        
        # Pneumatics
        if controller.buttonX.pressing():
            scoop.set(True)
        elif controller.buttonB.pressing():
            scoop.set(False)
        if controller.buttonUp.pressing():
            descore_wing.set(True)
        elif controller.buttonDown.pressing():
            descore_wing.set(False)
        
        wait(20, MSEC)

# Helper functions for user control (unchanged signatures)
def l1_l2(u_speed):
    intake_conv.spin(REVERSE, u_speed, PERCENT)
    fly.spin(REVERSE, u_speed, PERCENT)

def l1(u_speed_iv, u_speed_f):
    intake_conv.spin(REVERSE, u_speed_iv, PERCENT)
    fly.spin(FORWARD, u_speed_f, PERCENT)

def l2(u_speed_iv, u_speed_f):
    intake_conv.spin(FORWARD, u_speed_iv, PERCENT)
    fly.spin(FORWARD, u_speed_f, PERCENT)

# ----------------------------------------------------
# COMPETITION REGISTRATION
# ----------------------------------------------------
comp = Competition(run_user_control, run_autonomous_stupid)