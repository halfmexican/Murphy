from vex import *


# Brain and Controller
brain = Brain()
controller = Controller()
global moving

moving = False 

# Motor Setup: 4-Motor Drive (1:1 Ratio / 18:1 Green Cartridges)
left_motor_1 = Motor(Ports.PORT1, GearSetting.RATIO_18_1, False)
left_motor_2 = Motor(Ports.PORT2, GearSetting.RATIO_18_1, False)
right_motor_1 = Motor(Ports.PORT9, GearSetting.RATIO_18_1, True)
right_motor_2 = Motor(Ports.PORT10, GearSetting.RATIO_18_1, True)

intake_conv = Motor(Ports.PORT3, GearSetting.RATIO_18_1, False) 
fly = Motor(Ports.PORT8, GearSetting.RATIO_6_1, True)

scoop = DigitalOut(brain.three_wire_port.a)
descore_wing = DigitalOut(brain.three_wire_port.d)

wait(20, MSEC)

# ----------------------------------------------------
#  AUTONOMOUS HELPER FUNCTIONS
# ----------------------------------------------------

def stop_drive():
    left_motor_1.stop()
    left_motor_2.stop()
    right_motor_1.stop()
    right_motor_2.stop()

def set_drivetrain_vel (l_vel, r_vel):
    left_motor_1.set_velocity(l_vel)
    left_motor_2.set_velocity(l_vel)
    right_motor_1.set_velocity(r_vel)
    right_motor_2.set_velocity(r_vel)

def turn_drive(ldegree, rdegree):
    if not moving is True:
        moving = True
        left_motor_1.spin_to_position(ldegree, TURNS, False)
        left_motor_2.spin_to_position(ldegree, TURNS, False)
        right_motor_1.spin_to_position(rdegree, TURNS, False)
        right_motor_2.spin_to_position(rdegree, TURNS, False)
        moving = False
    else :
        brain.screen.print("already moving")


def l1_l2(u_speed):
    intake_conv.spin(REVERSE, u_speed, PERCENT)
    fly.spin(REVERSE, u_speed, PERCENT)

def l1(u_speed_iv, u_speed_f):
    intake_conv.spin(REVERSE, u_speed_iv, PERCENT)
    fly.spin(FORWARD, u_speed_f, PERCENT)

def l2(u_speed_iv, u_speed_f):
    intake_conv.spin(FORWARD, u_speed_iv, PERCENT)
    fly.spin(FORWARD, u_speed_f, PERCENT)

def stop_intake():
    intake_conv.stop()
    fly.stop()

# ----------------------------------------------------
#  EMERGENCY STOP & STEP LOGIC
# ----------------------------------------------------

def check_stop():
    if controller.buttonRight.pressing():
        stop_drive()
        stop_intake()
        return True 
    return False

def step_wait(duration):
    timer = 0
    while timer < duration:
        if check_stop():
            return True 
        wait(20, MSEC)
        timer += 0.02
    return False




# TEST CLIP: DRIVE FORWARD 1 FOOT
def run_autonomous_stupid():
    set_drivetrain_vel(70, 70)
    turn_drive(2,2)
    

    
    


def run_user_control():
    while True: 
        forward = controller.axis3.position()
        turn = controller.axis1.position()
        
        speed_mod = 1.0 if controller.buttonR2.pressing() else (0.3 if controller.buttonR1.pressing() else 0.6)

        left_motor_1.spin(FORWARD, (forward + turn) * speed_mod, PERCENT)
        left_motor_2.spin(FORWARD, (forward + turn) * speed_mod, PERCENT)
        right_motor_1.spin(FORWARD, (forward - turn) * speed_mod, PERCENT)
        right_motor_2.spin(FORWARD, (forward - turn) * speed_mod, PERCENT)

        fly_i_power = 40 if controller.buttonA.pressing() else 100
        if controller.buttonL1.pressing() and controller.buttonL2.pressing():
            l1_l2(fly_i_power)
        elif controller.buttonL1.pressing():
            l1(fly_i_power, fly_i_power)
        elif controller.buttonL2.pressing():
            l2(fly_i_power, fly_i_power)
        else:
            stop_intake()

        if controller.buttonX.pressing(): scoop.set(True)
        elif controller.buttonB.pressing(): scoop.set(False)
        if controller.buttonUp.pressing(): descore_wing.set(True)
        elif controller.buttonDown.pressing(): descore_wing.set(False)

        wait(20, MSEC)


# ----------------------------------------------------
#  COMPETITION REGISTRATION
# ----------------------------------------------------
# Field control signals will automatically pick the correct function
comp = Competition(run_user_control, run_autonomous_stupid)

