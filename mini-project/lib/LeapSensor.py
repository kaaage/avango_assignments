#!/usr/bin/python

### import guacamole libraries
import avango
import avango.gua
import avango.script
from avango.script import field_has_changed
import avango.daemon

### import application libraries

# sys.path.append("/usr/lib/Leap")
# sys.path.append("/path/to/lib/x86")
# sys.path.append("/path/to/lib")

# import lib.Leap as Leap
import leap.Leap, sys, _thread, time
from leap.Leap import CircleGesture, KeyTapGesture, ScreenTapGesture, SwipeGesture, Finger
import time


class LeapSensor(avango.script.Script):

    sf_mat = avango.gua.SFMatrix4()

    pinch_threshold = 0.7

    handright_pinch_strength = 0
    handleft_pinch_strength = 0

    handright_pos = avango.gua.SFMatrix4()
    handright_index_pos = avango.gua.SFMatrix4()
    handright_thumb_pos = avango.gua.SFMatrix4()

    handleft_pos = avango.gua.SFMatrix4()
    handleft_index_pos = avango.gua.SFMatrix4()
    handleft_thumb_pos = avango.gua.SFMatrix4()

    cube_picked = None

    def __init__(self):
        self.super(LeapSensor).__init__()

    def my_constructor(self,
        # SCENE = None,
        SCENEGRAPH = None,
        # NAVIGATION_NODE = None,
        TRACKING_TRANSMITTER_OFFSET = avango.gua.make_identity_mat(),
        ):
        self.SCENEGRAPH = SCENEGRAPH
        # self.SCENE = SCENE

        ### Picking ###

        self.pick_result = None
        self.picked_object = None

        self.white_list = []
        self.black_list = ["invisible"]

        self.pick_options = avango.gua.PickingOptions.PICK_ONLY_FIRST_OBJECT \
                            | avango.gua.PickingOptions.GET_POSITIONS \
                            | avango.gua.PickingOptions.GET_NORMALS \
                            | avango.gua.PickingOptions.GET_WORLD_POSITIONS \
                            | avango.gua.PickingOptions.GET_WORLD_NORMALS

        self.ray = avango.gua.nodes.Ray() # required for trimesh intersection

        ### Init Leap Motion ###

        # Create a sample listener and controller
        self.listener = SampleListener()
        self.controller = leap.Leap.Controller()
        # Have the sample listener receive events from the controller
        self.controller.add_listener(self.listener)

        # Keep this process running until Enter is pressed
        # print("Press Enter to quit...")
        # try:
        #     sys.stdin.readline()
        # except KeyboardInterrupt:
        #     pass
        # finally:
        #     # Remove the sample listener when done
        #     controller.remove_listener(listener)

        self.always_evaluate(True) # change global evaluation policy

    def evaluate(self):
        frame = self.controller.frame()
        # print("Frame id: %d, timestamp: %d, hands: %d, fingers: %d, tools: %d, gestures: %d" % (
        #       frame.id, frame.timestamp, len(frame.hands), len(frame.fingers), len(frame.tools), len(frame.gestures())))

        # hand_left = frame.hands.leftmost
        # hand_right = frame.hands.rightmost
        # index_finger_list = hand_right.fingers.finger_type(Finger.TYPE_INDEX)
        # index_finger = index_finger_list[0]

        self.handright_index_pos.value = get_leap_trans_mat(frame.hands.rightmost.fingers.finger_type(Finger.TYPE_INDEX)[0].tip_position)
        self.handright_thumb_pos.value = get_leap_trans_mat(frame.hands.rightmost.fingers.finger_type(Finger.TYPE_THUMB)[0].tip_position)

        self.handleft_index_pos.value = get_leap_trans_mat(frame.hands.leftmost.fingers.finger_type(Finger.TYPE_INDEX)[0].tip_position)
        self.handleft_thumb_pos.value = get_leap_trans_mat(frame.hands.leftmost.fingers.finger_type(Finger.TYPE_THUMB)[0].tip_position)

        self.handright_pinch_strength = frame.hands.rightmost.pinch_strength
        self.handleft_pinch_strength = frame.hands.leftmost.pinch_strength

        ## calc intersections - picked cubes
        _mf_handright_pick_result = self.calc_pick_result(thumb = self.handright_thumb_pos.value, index = self.handright_index_pos.value, PICK_LENGTH = 0.05)
        # _mf_handleft_pick_result = self.calc_pick_result(thumb = self.handleft_thumb_pos.value, index = self.handleft_index_pos.value, PICK_LENGTH = 0.05)

        ### todo: calculate cube position offset
        offset_mat = avango.gua.make_trans_mat(0.0,0.0,0.425)

        if len(_mf_handright_pick_result.value) > 0:
            print("Gotcha!!!!")

        # rot = index_finger.direction
        # This should be the quaternion rotation of -45 euler around x ( avango.gua.make_rot_mat( 0.92388,-0.38268,0,0) )
        # mat = avango.gua.make_trans_mat(avango.gua.Vec3(pos.x / 1000 , (-pos.z / 1000)-0.425, (pos.y / 1000))) * avango.gua.make_scale_mat(0.05,0.05,0.05)
        # print("x "+ str(pos.x) +"\ty "+ str(pos.y) +"\tz "+ str(pos.z))
        # self.sf_mat.value = mat

    def calc_pick_result(self, thumb = avango.gua.make_identity_mat(), index = avango.gua.make_identity_mat(), PICK_LENGTH = 1.0):
        # update ray parameters
        self.ray.Origin.value = thumb.get_translate()

        # _vec = avango.gua.make_rot_mat(PICK_MAT.get_rotate_scale_corrected()) * avango.gua.Vec3(0.0,0.0,-1.0)
        # _vec = avango.gua.Vec3(_vec.x,_vec.y,_vec.z)

        _vec = index.get_translate() - thumb.get_translate()

        self.ray.Direction.value = _vec * PICK_LENGTH

        # intersect
        _mf_pick_result = self.SCENEGRAPH.ray_test(self.ray, self.pick_options, self.white_list, self.black_list)
        # _mf_pick_result = None

        return _mf_pick_result

def get_leap_trans_mat(pos):
    return avango.gua.make_trans_mat(avango.gua.Vec3(pos.x / 1000 , (-pos.z / 1000)-0.425, (pos.y / 1000))) * avango.gua.make_scale_mat(0.05,0.05,0.05)


class SampleListener(leap.Leap.Listener):
    # finger_names = ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky']
    # bone_names = ['Metacarpal', 'Proximal', 'Intermediate', 'Distal']
    # state_names = ['STATE_INVALID', 'STATE_START', 'STATE_UPDATE', 'STATE_END']

    def on_init(self, controller):
        print("Initialized")

    def on_connect(self, controller):
        print("Connected")

        # # Enable gestures
        # controller.enable_gesture(Leap.Gesture.TYPE_CIRCLE);
        # controller.enable_gesture(Leap.Gesture.TYPE_KEY_TAP);
        # controller.enable_gesture(Leap.Gesture.TYPE_SCREEN_TAP);
        # controller.enable_gesture(Leap.Gesture.TYPE_SWIPE);

    def on_disconnect(self, controller):
        # Note: not dispatched when running in a debugger.
        print("Disconnected")

    def on_exit(self, controller):
        print("Exited")

    # def on_frame(self, controller):
    #     # Get the most recent frame and report some basic information
    #     frame = controller.frame()

    #     print("Frame id: %d, timestamp: %d, hands: %d, fingers: %d, tools: %d, gestures: %d" % (
    #           frame.id, frame.timestamp, len(frame.hands), len(frame.fingers), len(frame.tools), len(frame.gestures())))

    #     # Get hands
    #     for hand in frame.hands:

    #         handType = "Left hand" if hand.is_left else "Right hand"

    #         print("  %s, id %d, position: %s" % (
    #             handType, hand.id, hand.palm_position))

    #         # Get the hand's normal vector and direction
    #         normal = hand.palm_normal
    #         direction = hand.direction

    #         # Calculate the hand's pitch, roll, and yaw angles
    #         print("  pitch: %f degrees, roll: %f degrees, yaw: %f degrees" % (
    #             direction.pitch * Leap.RAD_TO_DEG,
    #             normal.roll * Leap.RAD_TO_DEG,
    #             direction.yaw * Leap.RAD_TO_DEG))

    #         # Get arm bone
    #         arm = hand.arm
    #         print("  Arm direction: %s, wrist position: %s, elbow position: %s" % (
    #             arm.direction,
    #             arm.wrist_position,
    #             arm.elbow_position))

    #         # Get fingers
    #         for finger in hand.fingers:

    #             print("    %s finger, id: %d, length: %fmm, width: %fmm" % (
    #                 self.finger_names[finger.type],
    #                 finger.id,
    #                 finger.length,
    #                 finger.width))

    #             # Get bones
    #             for b in range(0, 4):
    #                 bone = finger.bone(b)
    #                 print("      Bone: %s, start: %s, end: %s, direction: %s" % (
    #                     self.bone_names[bone.type],
    #                     bone.prev_joint,
    #                     bone.next_joint,
    #                     bone.direction))

    #     # Get tools
    #     for tool in frame.tools:

    #         print("  Tool id: %d, position: %s, direction: %s" % (
    #             tool.id, tool.tip_position, tool.direction))

    #     # Get gestures
    #     for gesture in frame.gestures():
    #         if gesture.type == Leap.Gesture.TYPE_CIRCLE:
    #             circle = CircleGesture(gesture)

    #             # Determine clock direction using the angle between the pointable and the circle normal
    #             if circle.pointable.direction.angle_to(circle.normal) <= Leap.PI/2:
    #                 clockwiseness = "clockwise"
    #             else:
    #                 clockwiseness = "counterclockwise"

    #             # Calculate the angle swept since the last frame
    #             swept_angle = 0
    #             if circle.state != Leap.Gesture.STATE_START:
    #                 previous_update = CircleGesture(controller.frame(1).gesture(circle.id))
    #                 swept_angle =  (circle.progress - previous_update.progress) * 2 * Leap.PI

    #             print("  Circle id: %d, %s, progress: %f, radius: %f, angle: %f degrees, %s" % (
    #                     gesture.id, self.state_names[gesture.state],
    #                     circle.progress, circle.radius, swept_angle * Leap.RAD_TO_DEG, clockwiseness))

    #         if gesture.type == Leap.Gesture.TYPE_SWIPE:
    #             swipe = SwipeGesture(gesture)
    #             print("  Swipe id: %d, state: %s, position: %s, direction: %s, speed: %f" % (
    #                     gesture.id, self.state_names[gesture.state],
    #                     swipe.position, swipe.direction, swipe.speed))

    #         if gesture.type == Leap.Gesture.TYPE_KEY_TAP:
    #             keytap = KeyTapGesture(gesture)
    #             print("  Key Tap id: %d, %s, position: %s, direction: %s" % (
    #                     gesture.id, self.state_names[gesture.state],
    #                     keytap.position, keytap.direction ))

    #         if gesture.type == Leap.Gesture.TYPE_SCREEN_TAP:
    #             screentap = ScreenTapGesture(gesture)
    #             print("  Screen Tap id: %d, %s, position: %s, direction: %s" % (
    #                     gesture.id, self.state_names[gesture.state],
    #                     screentap.position, screentap.direction ))

    #     if not (frame.hands.is_empty and frame.gestures().is_empty):
    #         print("")

    # def state_string(self, state):
    #     if state == Leap.Gesture.STATE_START:
    #         return "STATE_START"

    #     if state == Leap.Gesture.STATE_UPDATE:
    #         return "STATE_UPDATE"

    #     if state == Leap.Gesture.STATE_STOP:
    #         return "STATE_STOP"

    #     if state == Leap.Gesture.STATE_INVALID:
    #         return "STATE_INVALID"
