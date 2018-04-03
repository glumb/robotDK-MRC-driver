# This file is a sample POST PROCESSOR script to generate programs
# for a generic robot with RoboDK
#
# To edit/test this POST PROCESSOR script file:
# Select "Program"->"Add/Edit Post Processor", then select your post or create a new one.
# You can edit this file using any text editor or Python editor. Using a Python editor allows to quickly evaluate a sample program at the end of this file.
# Python should be automatically installed with RoboDK
#
# You can also edit the POST PROCESSOR manually:
#    1- Open the *.py file with Python IDLE (right click -> Edit with IDLE)
#    2- Make the necessary changes
#    3- Run the file to open Python Shell: Run -> Run module (F5 by default)
#    4- The "test_post()" function is called automatically
# Alternatively, you can edit this file using a text editor and run it with Python
#
# To use a POST PROCESSOR file you must place the *.py file in "C:/RoboDK/Posts/"
# To select a specific POST PROCESSOR for your robot in RoboDK you must follow these steps:
#    1- Open the robot panel (double click a robot)
#    2- Select "Parameters"
#    3- Select "Unlock advanced options"
#    4- Select your post as the file name in the "Robot brand" box
#
# To delete an existing POST PROCESSOR script, simply delete this file (.py file)
#
# ----------------------------------------------------
# More information about RoboDK Post Processors and Offline Programming here:
#      http://www.robodk.com/help#PostProcessor
#      http://www.robodk.com/doc/PythonAPI/postprocessor.html
# ----------------------------------------------------

# ----------------------------------------------------
# Import RoboDK tools
from robodk import *

# ----------------------------------------------------
import serial

MRCP_END_FRAME = '\r'
MRCP_START_FRAME = ':'

MRCP_COMMAND_QUEUE_IN = 'Q'
MRCP_COMMAND_EXECUTE = 'E'
MRCP_COMMAND_WRITE = 'W'


def pose_2_str(pose):
    """Prints a pose target"""
    [x, y, z, r, p, w] = Pose_2_Staubli(pose)
    return ('X%.3f Y%.3f Z%.3f A%.3f B%.3f C%.3f' % (x / 10, y / 10, z / 10, r, p, w))


def joints_2_str(joints):
    """Prints a joint target"""
    str = ''
    data = ['R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7', 'R8', 'R9']
    for i in range(len(joints)):
        str = str + ('%s%.3f ' % (data[i], joints[i]))
    str = str[:-1]
    return str

# ----------------------------------------------------
# Object class that handles the robot instructions/syntax


class RobotPost(object):
    """Robot post object"""
    PROG_EXT = 'mril'        # set the program extension

    # other variables
    ROBOT_POST = ''
    ROBOT_NAME = ''
    PROG_FILES = []

    PROG = ''
    LOG = ''
    nAxes = 6

    def __init__(self, robotpost=None, robotname=None, robot_axes=6, **kwargs):
        self.ROBOT_POST = robotpost
        self.ROBOT_NAME = robotname
        self.PROG = ''
        self.LOG = ''
        self.nAxes = robot_axes
        self.LINE_NUMBER = 0

    def ProgStart(self, progname):
        """self.addline('PROC %s()' % progname)"""

    def ProgFinish(self, progname):
        """self.addline('ENDPROC')"""

    def ProgSave(self, folder, progname, ask_user=False, show_result=False):
        progname = progname + '.' + self.PROG_EXT
        if ask_user or not DirExists(folder):
            filesave = getSaveFile(folder, progname, 'Save program as...')
            if filesave is not None:
                filesave = filesave.name
            else:
                return
        else:
            filesave = folder + '/' + progname
        fid = open(filesave, "w")
        fid.write(self.PROG)
        fid.close()
        print('SAVED: %s\n' % filesave)
        #---------------------- show result
        if show_result:
            if type(show_result) is str and False:
                # Open file with provided application
                import subprocess
                p = subprocess.Popen([show_result, filesave])
            else:
                # open file with default application
                import os, sys, subprocess
                opener ="open" if sys.platform == "darwin" else "xdg-open"
                subprocess.call([opener, filesave])

            if len(self.LOG) > 0:
                mbox('Program generation LOG:\n\n' + self.LOG)

    def ProgSendRobot(self, robot_ip, remote_path, ftp_user, ftp_pass):
        """Send a program to the robot using the provided parameters. This method is executed right after ProgSave if we selected the option "Send Program to Robot".
        The connection parameters must be provided in the robot connection menu of RoboDK"""
        ser = serial.Serial(robot_ip, baudrate=9600, timeout=1)
        self.addlog('sending over serial to port: ' + str(robot_ip))

        if len(self.PROG.replace(" ", "")) > 2000:
            self.addlog('program to long: ' +
                        str(len(self.PROG.replace(" ", ""))) + ' max 2000 Bytes')
            return

        # send only W to clear the current memory
        ser.write(bytes(MRCP_START_FRAME +
                        MRCP_COMMAND_WRITE + MRCP_END_FRAME, 'utf-8'))

        for line in self.PROG.strip().split('\n'):
            self.addlog(MRCP_START_FRAME + MRCP_COMMAND_WRITE +
                        line.replace(" ", "") + MRCP_END_FRAME)
            ser.write(bytes(MRCP_START_FRAME + MRCP_COMMAND_WRITE +
                            line.replace(" ", "") + MRCP_END_FRAME, 'utf-8'))
        mbox('Program generation LOG:\n\n' + self.LOG)

    def MoveJ(self, pose, joints, conf_RLF=None):
        """Add a joint movement"""
        self.addline('M00 ' + joints_2_str(joints))

    def MoveL(self, pose, joints, conf_RLF=None):
        """Add a linear movement"""
        self.addline('M01 ' + pose_2_str(pose))

    def MoveC(self, pose1, joints1, pose2, joints2, conf_RLF_1=None, conf_RLF_2=None):
        """Add a circular movement"""
        self.addline('MOVC ' + pose_2_str(pose1) + ' ' + pose_2_str(pose2))

    def setFrame(self, pose, frame_id=None, frame_name=None):
        """Change the robot reference frame"""
        # self.addline('BASE_FRAME ' + pose_2_str(pose))

    def setTool(self, pose, tool_id=None, tool_name=None):
        """Change the robot TCP"""
        self.addline('TOOL_FRAME ' + pose_2_str(pose))

    def Pause(self, time_ms):
        """Pause the robot program"""
        if time_ms < 0:
            self.addline('PAUSE')
        else:
            self.addline('D %.3i' % (time_ms))

    def setSpeed(self, speed_mms):
        """Changes the robot speed (in mm/s)"""
        self.addline('V %.2f' % speed_mms)

    def setAcceleration(self, accel_mmss):
        """Changes the robot acceleration (in mm/s2)"""
        self.addlog('setAcceleration not defined')

    def setSpeedJoints(self, speed_degs):
        """Changes the robot joint speed (in deg/s)"""
        self.addlog('setSpeedJoints not defined')

    def setAccelerationJoints(self, accel_degss):
        """Changes the robot joint acceleration (in deg/s2)"""
        self.addlog('setAccelerationJoints not defined')

    def setZoneData(self, zone_mm):
        """Changes the rounding radius (aka CNT, APO or zone data) to make the movement smoother"""
        self.addlog('setZoneData not defined (%.1f mm)' % zone_mm)

    def setDO(self, io_var, io_value):
        """Sets a variable (digital output) to a given value"""
        if type(io_var) != str:  # set default variable name if io_var is a number
            io_var = '%s' % str(io_var)
        if type(io_value) != str:  # set default variable value if io_value is a number
            if io_value > 0:
                io_value = '1'
            else:
                io_value = '0'

        # at this point, io_var and io_value must be string values
        self.addline('O%s %s' % (io_var, io_value))

    def waitDI(self, io_var, io_value, timeout_ms=-1):
        """Waits for a variable (digital input) io_var to attain a given value io_value. Optionally, a timeout can be provided."""
        if type(io_var) != str:  # set default variable name if io_var is a number
            io_var = '%s' % str(io_var)
        if type(io_value) != str:  # set default variable value if io_value is a number
            if io_value > 0:
                io_value = '1'
            else:
                io_value = '0'

        # at this point, io_var and io_value must be string values
        # if timeout_ms < 0:
        #     self.addline('WAIT FOR %s==%s' % (io_var, io_value))
        # else:
            self.addline('I%s %s' % (io_var, io_value))

    def RunCode(self, code, is_function_call=False):
        """Adds code or a function call"""
        if is_function_call:
            code.replace(' ', '_')
            if not code.endswith(')'):
                code = code + '()'
            self.addline(code)
        else:
            self.addline(code)

    def RunMessage(self, message, iscomment=False):
        """Display a message in the robot controller screen (teach pendant)"""
        if iscomment:
            self.addline('# ' + message)
        else:
            self.addlog(
                'Show message on teach pendant not implemented (%s)' % message)

# ------------------ private ----------------------
    def addline(self, newline):
        """Add a program line"""
        self.LINE_NUMBER += 1
        self.PROG = self.PROG + 'N' + \
            str(self.LINE_NUMBER) + \
            '   '[0:3-len(str(self.LINE_NUMBER))] + newline + '\n'

    def addlog(self, newline):
        """Add a log message"""
        self.LOG = self.LOG + newline + '\n'

# -------------------------------------------------
# ------------ For testing purposes ---------------


def Pose(xyzrpw):
    [x, y, z, r, p, w] = xyzrpw
    a = r * math.pi / 180
    b = p * math.pi / 180
    c = w * math.pi / 180
    ca = math.cos(a)
    sa = math.sin(a)
    cb = math.cos(b)
    sb = math.sin(b)
    cc = math.cos(c)
    sc = math.sin(c)
    return Mat([[cb * ca, ca * sc * sb - cc * sa, sc * sa + cc * ca * sb, x], [cb * sa, cc * ca + sc * sb * sa, cc * sb * sa - ca * sc, y], [-sb, cb * sc, cc * cb, z], [0, 0, 0, 1]])


def test_post():
    """Test the post with a basic program"""

    robot = RobotPost()

    robot.ProgStart("Program")
    robot.RunMessage(
        "Program generated by RoboDK using a custom post processor", True)
    robot.setFrame(Pose([807.766544, -963.699898, 41.478944, 0, 0, 0]))
    robot.setTool(Pose([62.5, -108.253175, 100, -60, 90, 0]))
    robot.MoveJ(Pose([200, 200, 500, 180, 0, 180]), [-46.18419, -
                                                     6.77518, -20.54925, 71.38674, 49.58727, -302.54752])
    robot.MoveL(Pose([200, 250, 348.734575, 180, 0, -150]),
                [-41.62707, -8.89064, -30.01809, 60.62329, 49.66749, -258.98418])
    robot.MoveL(Pose([200, 200, 262.132034, 180, 0, -150]),
                [-43.73892, -3.91728, -35.77935, 58.57566, 54.11615, -253.81122])
    robot.RunMessage("Setting air valve 1 on")
    robot.RunCode("TCP_On", True)
    robot.Pause(1000)
    robot.MoveL(Pose([200, 250, 348.734575, 180, 0, -150]),
                [-41.62707, -8.89064, -30.01809, 60.62329, 49.66749, -258.98418])
    robot.MoveL(Pose([250, 300, 278.023897, 180, 0, -150]),
                [-37.52588, -6.32628, -34.59693, 53.52525, 49.24426, -251.44677])
    robot.MoveL(Pose([250, 250, 191.421356, 180, 0, -150]),
                [-39.75778, -1.04537, -40.37883, 52.09118, 54.15317, -246.94403])
    robot.RunMessage("Setting air valve off")
    robot.RunCode("TCP_Off", True)
    robot.Pause(1000)
    robot.MoveL(Pose([250, 300, 278.023897, 180, 0, -150]),
                [-37.52588, -6.32628, -34.59693, 53.52525, 49.24426, -251.44677])
    robot.MoveL(Pose([250, 200, 278.023897, 180, 0, -150]),
                [-41.85389, -1.95619, -34.89154, 57.43912, 52.34162, -253.73403])
    robot.MoveL(Pose([250, 150, 191.421356, 180, 0, -150]),
                [-43.82111, 3.29703, -40.29493, 56.02402, 56.61169, -249.23532])
    robot.MoveJ(None, [-46.18419, -6.77518, -20.54925,
                       71.38674, 49.58727, -302.54752])
    robot.ProgFinish("Program")
    # robot.ProgSave(".","Program",True)
    print(robot.PROG)
    if len(robot.LOG) > 0:
        mbox('Program generation LOG:\n\n' + robot.LOG)

    input("Press Enter to close...")


if __name__ == "__main__":
    """Function to call when the module is executed by itself: test"""
    test_post()
