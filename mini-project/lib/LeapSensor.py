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
from leap.Leap import CircleGesture, KeyTapGesture, ScreenTapGesture, SwipeGesture, Finger, Vector
import time

# import numpy as np
import math

class LeapSensor(avango.script.Script):

    sf_mat = avango.gua.SFMatrix4()

    pinch_threshold = 0.7

    handright_pinch_strength = 0
    handleft_pinch_strength = 0

    handright_pos = avango.gua.SFMatrix4()
    handright_rot = avango.gua.SFMatrix4()
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
        BASENODE = None,
        # NAVIGATION_NODE = None,
        TRACKING_TRANSMITTER_OFFSET = avango.gua.make_identity_mat(),
        ):
        self.SCENEGRAPH = SCENEGRAPH
        self.BASENODE = BASENODE
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

        self.leap_node = avango.gua.nodes.TransformNode(Name="leap_node")
        self.leap_node.Transform.value = avango.gua.make_trans_mat(0.0, 0.06, 0.425) * avango.gua.make_rot_mat(-77.0, 1, 0, 0)

        self.BASENODE.Children.value.append(self.leap_node)

        # Keep this process running until Enter is pressed
        # print("Press Enter to quit...")
        # try:
        #     sys.stdin.readline()
        # except KeyboardInterrupt:
        #     pass
        # finally:
        #     # Remove the sample listener when done
        #     controller.remove_listener(listener)

        #tip visualization
        _loader = avango.gua.nodes.TriMeshLoader() # get trimesh loader to load external meshes
        self.thumb_sphere = avango.gua.nodes.TransformNode(Name="thumb_sphere")
        self.thumb_sphere.Transform.value = self.handright_thumb_pos.value
        self.thumb_sphere_geometry = _loader.create_geometry_from_file("thumb_sphere", "data/objects/sphere.obj", avango.gua.LoaderFlags.DEFAULTS)
        self.thumb_sphere_geometry.Material.value.set_uniform("Color", avango.gua.Vec4(1.0, 0.0, 0.0, 1.0))
        self.thumb_sphere_geometry.Transform.value = avango.gua.make_scale_mat(0.02,0.02,0.02)
        self.thumb_sphere.Children.value.append(self.thumb_sphere_geometry)
        self.leap_node.Children.value.append(self.thumb_sphere)

        self.index_sphere = avango.gua.nodes.TransformNode(Name="index_sphere")
        self.index_sphere.Transform.value = self.handright_index_pos.value
        self.index_sphere_geometry = _loader.create_geometry_from_file("index_sphere", "data/objects/sphere.obj", avango.gua.LoaderFlags.DEFAULTS)
        self.index_sphere_geometry.Material.value.set_uniform("Color", avango.gua.Vec4(1.0, 0.0, 0.0, 1.0))
        self.index_sphere_geometry.Transform.value = avango.gua.make_scale_mat(0.02,0.02,0.02)
        self.index_sphere.Children.value.append(self.index_sphere_geometry)
        self.leap_node.Children.value.append(self.index_sphere)

        #visualization of pick ray
        self.ray_trans = avango.gua.nodes.TransformNode(Name="ray_trans")
        self.ray_geometry = _loader.create_geometry_from_file("ray_geometry", "data/objects/cylinder.obj", avango.gua.LoaderFlags.DEFAULTS)
        self.ray_geometry.Material.value.set_uniform("Color", avango.gua.Vec4(1.0,0.0,0.0,1.0))
        self.ray_geometry.Transform.value = \
             avango.gua.make_trans_mat(0.0,0.0,0.0) * \
             avango.gua.make_scale_mat(0.005, 0.1, 0.005)
        self.ray_trans.Children.value.append(self.ray_geometry)

        self.always_evaluate(True) # change global evaluation policy

    def evaluate(self):
        frame = self.controller.frame()

        self.handright_index_pos.value = self.get_leap_trans_mat(frame.hands.rightmost.fingers.finger_type(Finger.TYPE_INDEX)[0].tip_position)
        self.handright_thumb_pos.value = self.get_leap_trans_mat(frame.hands.rightmost.fingers.finger_type(Finger.TYPE_THUMB)[0].tip_position)

        self.handleft_index_pos.value = self.get_leap_trans_mat(frame.hands.leftmost.fingers.finger_type(Finger.TYPE_INDEX)[0].tip_position)
        self.handleft_thumb_pos.value = self.get_leap_trans_mat(frame.hands.leftmost.fingers.finger_type(Finger.TYPE_THUMB)[0].tip_position)


        self.hand_right = frame.hands.rightmost
        self.rot_x = math.degrees(self.hand_right.direction.pitch)
        self.rot_y = math.degrees(self.hand_right.direction.yaw)
        self.rot_z = math.degrees(self.hand_right.palm_normal.roll)
       
        handright_rot = avango.gua.make_rot_mat(self.rot_x, 1.0, 0.0, 0.0) *  avango.gua.make_rot_mat(self.rot_y, 0.0, 1.0, 0.0) * avango.gua.make_rot_mat(self.rot_z, 0.0, 0.0, 1.0)


        print("x " +str(self.rot_x) +"\ty " +str(self.rot_y) +"\tz " + str(self.rot_z))

        self.handright_pinch_strength = frame.hands.rightmost.pinch_strength
        self.handleft_pinch_strength = frame.hands.leftmost.pinch_strength

        # print("Frame id: %d, timestamp: %d, hands: %d, fingers: %d, tools: %d, gestures: %d" % (
        #       frame.id, frame.timestamp, len(frame.hands), len(frame.fingers), len(frame.tools), len(frame.gestures())))

        # hand_left = frame.hands.leftmost
        # hand_right = frame.hands.rightmost
        # index_finger_list = hand_right.fingers.finger_type(Finger.TYPE_INDEX)
        # index_finger = index_finger_list[0]

        # self.cur_frame = self.thumb_sphere.Transform.value * avango.gua.make_inverse_mat(self.last_frame)
        # _trans = self.cur_frame.get_translate()
        # rot_x = frame.hands.rightmost.rotation_angle(self.controller.frame(1), Vector.x_axis) * 180 / math.pi
        # rot_y = frame.hands.rightmost.rotation_angle(self.controller.frame(1), Vector.y_axis) * 180 / math.pi
        # rot_z = frame.hands.rightmost.rotation_angle(self.controller.frame(1), Vector.z_axis) * 180 / math.pi
        #print(frame.hands.rightmost.rotation_angle(self.controller.frame(1)))

        # _rot = avango.gua.make_rot_mat(rot_x, 1.0, 0.0, 0.0) * _rot = avango.gua.make_rot_mat(rot_y, 0.0, 1.0, 0.0) * _rot = avango.gua.make_rot_mat(rot_z, 0.0, 0.0, 1.0)

        self.thumb_sphere.Transform.value = self.handright_thumb_pos.value #* avango.gua.make_rot_mat(_rot)
        self.index_sphere.Transform.value = self.handright_index_pos.value

        # _rot = frame.hands.rightmost.rotation_matrix(self.controller.frame(0))
        # self.thumb_sphere.Transform.value = self.thumb_sphere.Transform.value * avango.gua.make_rot_mat(_rot)
        # self.thumb_sphere.Transform.value = self.thumb_sphere.Transform.value * avango.gua.make_trans_mat(_trans.x, _trans.y, _trans.z) \
        #     * _rot

        # self.last_frame = self.thumb_sphere.Transform.value




        ## calc intersections - picked cubes
        # if (self.handright_pinch_strength > 0.8):
        _mf_handright_pick_result = self.calc_pick_result(thumb = self.thumb_sphere.WorldTransform.value, index = self.handright_index_pos.value, PICK_LENGTH = 0.1)
        # if _mf_handright_pick_result != None:
        # if len(_mf_handright_pick_result.value) > 0:
        #     print(len(_mf_handright_pick_result.value))

        if len(_mf_handright_pick_result.value) > 0: # intersection found
            self.pick_result = _mf_handright_pick_result.value[0] # get first pick result
            _node = self.pick_result.Object.value
            #print(_node)
            _pick_world_pos = self.pick_result.WorldPosition.value # pick position in world coordinate system
        else: # nothing hit
            self.pick_result = None

                # _mf_handright_pick_result.Transform.value = self.handright_index_pos.value
                # if self.pick_result is not None: # something was hit
                #     _node = self.pick_result.Object.value # get intersected geometry node
                #     _node = _node.Parent.value # take the parent node of the geomtry node (the whole object)

                #     self.start_dragging(_node)
        
        # if (self.handleft_pinch_strength > 0.8):
        #     _mf_handleft_pick_result = self.calc_pick_result(thumb = self.handleft_thumb_pos.value, PICK_LENGTH = 0.05)
        #     if _mf_handleft_pick_result != None:
        #         # _mf_handleft_pick_result.Transform.value = self.handleft_index_pos.value
        #         print(_mf_handleft_pick_result)

        ## calc intersections - picked cubes
        # _mf_handright_pick_result = self.calc_pick_result(thumb = self.handright_thumb_pos.value, index = self.handright_index_pos.value, PICK_LENGTH = 0.05)
        # _mf_handleft_pick_result = self.calc_pick_result(thumb = self.handleft_thumb_pos.value, index = self.handleft_index_pos.value, PICK_LENGTH = 0.05)

        ### todo: calculate cube position offset
        # offset_mat = avango.gua.make_trans_mat(0.0,0.0,0.425)


        # self.ray_trans.Transform.value = avango.gua.make_rot_mat(-90,0,1,0)

        # if len(_mf_handright_pick_result.value) > 0:
        #     print("Gotcha!!!!")

        # rot = index_finger.direction
        # This should be the quaternion rotation of -45 euler around x ( avango.gua.make_rot_mat( 0.92388,-0.38268,0,0) )
        # mat = avango.gua.make_trans_mat(avango.gua.Vec3(pos.x / 1000 , (-pos.z / 1000)-0.425, (pos.y / 1000))) * avango.gua.make_scale_mat(0.05,0.05,0.05)
        # print("x "+ str(pos.x) +"\ty "+ str(pos.y) +"\tz "+ str(pos.z))
        # self.sf_mat.value = mat

    def calc_pick_result(self, thumb = avango.gua.make_identity_mat(), index = avango.gua.make_identity_mat(), PICK_LENGTH = 0.1):
    # def calc_pick_result(self, thumb = avango.gua.make_identity_mat(), PICK_LENGTH = 0.1):
        # update ray parameters
        thumb_pos = thumb.get_translate()
        # index_pos = index.get_translate()

        # ray_vector = index_pos - thumb_pos
        # ray_length = ray_vector.length()

        # if (ray_length > 0):
        #     print(ray_vector)
        #     print(ray_length)

        self.ray.Origin.value = thumb_pos

        _vec = avango.gua.make_rot_mat(thumb.get_rotate_scale_corrected()) * avango.gua.Vec3(0.0,0.0,-1.0)
        _vec = avango.gua.Vec3(_vec.x,_vec.y,_vec.z)
      
        # _vec = avango.gua.make_rot_mat(thumb.get_rotate_scale_corrected()) * ray_vector
        # _vec = avango.gua.Vec3(_vec.x,_vec.y,_vec.z)

        # _vec = index.get_translate() - thumb.get_translate()

        self.ray.Direction.value = _vec * PICK_LENGTH
        # self.ray.Direction.value = _vec * ray_length

        # intersect
        _mf_pick_result = self.SCENEGRAPH.ray_test(self.ray, self.pick_options, self.white_list, self.black_list)
        # _mf_pick_result = None

        #VISUALIZE RAY
        self.ray_trans.Transform.value = avango.gua.make_trans_mat(self.ray.Origin.value) 
        #print(self.ray.Origin.value)
        # self.thumb_sphere.Children.value.append(self.ray_trans)

        return _mf_pick_result

    def get_leap_trans_mat(self, pos):
        transmat = avango.gua.make_trans_mat(avango.gua.Vec3(pos.x / 1000, (pos.y / 1000), (pos.z / 1000)))

        # if (pos.x != 0 and pos.z != 0):
        #     # print(pos)
        #     print(transmat)
        #     print(self.leap_node.Transform.value)

        return transmat


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

def dotproduct(v1, v2):
  return sum((a*b) for a, b in zip(v1, v2))

def length(v):
  return math.sqrt(dotproduct(v, v))

def angle(v1, v2):
  return math.acos(dotproduct(v1, v2) / (length(v1) * length(v2)))

def rotation_matrix(axis, theta):
    """
    Return the rotation matrix associated with counterclockwise rotation about
    the given axis by theta radians.
    """
    axis = np.asarray(axis)
    axis = axis/math.sqrt(np.dot(axis, axis))
    a = math.cos(theta/2.0)
    b, c, d = -axis*math.sin(theta/2.0)
    aa, bb, cc, dd = a*a, b*b, c*c, d*d
    bc, ad, ac, ab, bd, cd = b*c, a*d, a*c, a*b, b*d, c*d
    return np.array([[aa+bb-cc-dd, 2*(bc+ad), 2*(bd-ac)],
                     [2*(bc-ad), aa+cc-bb-dd, 2*(cd+ab)],
                     [2*(bd+ac), 2*(cd-ab), aa+dd-bb-cc]])

v = [3, 5, 0]
axis = [4, 4, 1]
theta = 1.2 

# print(np.dot(rotation_matrix(axis,theta), v)) 
# [ 2.74911638  4.77180932  1.91629719]