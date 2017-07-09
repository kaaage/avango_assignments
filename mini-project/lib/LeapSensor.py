#!/usr/bin/python

### import guacamole libraries
import avango
import avango.gua
import avango.script
from avango.script import field_has_changed
import avango.daemon
import math

### import application libraries

# sys.path.append("/usr/lib/Leap")
# sys.path.append("/path/to/lib/x86")
# sys.path.append("/path/to/lib")

# import lib.Leap as Leap
import leap.Leap, sys, _thread, time
from leap.Leap import CircleGesture, KeyTapGesture, ScreenTapGesture, SwipeGesture, Finger, Bone
import time


class LeapSensor(avango.script.Script):

    sf_mat = avango.gua.SFMatrix4()

    pinch_threshold = 0.7

    handright_pinch_strength = 0
    handleft_pinch_strength = 0

    # handright_pos = avango.gua.SFMatrix4()
    # handright_index_pos = avango.gua.SFMatrix4()
    # handright_thumb_pos = avango.gua.SFMatrix4()

    # handleft_pos = avango.gua.SFMatrix4()
    # handleft_index_pos = avango.gua.SFMatrix4()
    # handleft_thumb_pos = avango.gua.SFMatrix4()

    cube_picked = None

    def __init__(self):
        self.super(LeapSensor).__init__()

    def my_constructor(self,
        # SCENE = None,
        SCENEGRAPH = None,
        BASENODE = None,
        # NAVIGATION_NODE = None,
        TRACKING_TRANSMITTER_OFFSET = avango.gua.make_identity_mat(),
        TARGET_LIST = [],
        ):
        self.SCENEGRAPH = SCENEGRAPH
        self.BASENODE = BASENODE
        # self.SCENE = SCENE
        self.TARGET_LIST = TARGET_LIST

        ### Dragging 
        self.dragged_node = None
        self.dragging_offset_mat = avango.gua.make_identity_mat()

        ### Init Leap Motion ###
        # Create a sample listener and controller
        self.listener = SampleListener()
        self.controller = leap.Leap.Controller()
        # Have the sample listener receive events from the controller
        self.controller.add_listener(self.listener)

        self.leap_node = avango.gua.nodes.TransformNode(Name="leap_node")
        # self.leap_node.Transform.value = avango.gua.make_trans_mat(0.0, 0.06, 0.44) * avango.gua.make_rot_mat(-77.0, 1, 0, 0)
        self.leap_node.Transform.value = avango.gua.make_trans_mat(0.0, 0.0, 0.0)
        self.BASENODE.Children.value.append(self.leap_node)

        # self.leap_node_rot = avango.gua.nodes.TransformNode(Name="leap_node")
        # self.leap_node.Children.value.append(self.leap_node_rot)

        # Finger tips visualization
        _loader = avango.gua.nodes.TriMeshLoader() # get trimesh loader to load external meshes
        # self.thumb_sphere = avango.gua.nodes.TransformNode(Name="thumb_sphere")
        # self.thumb_sphere.Transform.value = self.handright_thumb_pos.value
        # self.thumb_sphere_geometry = _loader.create_geometry_from_file("thumb_sphere", "data/objects/sphere.obj", avango.gua.LoaderFlags.DEFAULTS)
        # self.thumb_sphere_geometry.Material.value.set_uniform("Color", avango.gua.Vec4(1.0, 0.0, 0.0, 1.0))
        # self.thumb_sphere_geometry.Transform.value = avango.gua.make_scale_mat(0.01,0.01,0.01)
        # self.thumb_sphere.Children.value.append(self.thumb_sphere_geometry)
        # self.leap_node.Children.value.append(self.thumb_sphere)

        # self.index_sphere = avango.gua.nodes.TransformNode(Name="index_sphere")
        # self.index_sphere.Transform.value = self.handright_index_pos.value
        # self.index_sphere_geometry = _loader.create_geometry_from_file("index_sphere", "data/objects/sphere.obj", avango.gua.LoaderFlags.DEFAULTS)
        # self.index_sphere_geometry.Material.value.set_uniform("Color", avango.gua.Vec4(1.0, 0.0, 0.0, 1.0))
        # self.index_sphere_geometry.Transform.value = avango.gua.make_scale_mat(0.01,0.01,0.01)
        # self.index_sphere.Children.value.append(self.index_sphere_geometry)
        # self.leap_node.Children.value.append(self.index_sphere)

        self.hands = [[], []]
        # self.hands.append([])
        # self.hands.append([])

        right_hand_color = avango.gua.Vec4(1.0, 0.0, 0.0, 1.0)
        self.rpalm_node = avango.gua.nodes.TransformNode(Name="right_palm_node")
        self.rpalm_geometry = _loader.create_geometry_from_file("right_palm_geometry", "data/objects/cube.obj", avango.gua.LoaderFlags.DEFAULTS | avango.gua.LoaderFlags.MAKE_PICKABLE)
        self.rpalm_geometry.Material.value.set_uniform("Color", right_hand_color)
        self.rpalm_geometry.Transform.value = avango.gua.make_scale_mat(0.06,0.01,0.10)
        self.rpalm_node.Children.value.append(self.rpalm_geometry)
        self.leap_node.Children.value.append(self.rpalm_node)
        for f in range(5):
            self.hands[0].append([])
            for b in range(3):
                length = 0.03
                bone_node = avango.gua.nodes.TransformNode(Name="bone" + str(f) + "-" + str(b) + "_node")
                if b == 0:
                    if f == 0:
                        bone_node.Transform.value = avango.gua.make_trans_mat(-0.045,0.0,0.03) #* avango.gua.make_rot_mat(90.0, 0.0, 1.0, 0.0)
                    elif f == 1:
                        bone_node.Transform.value = avango.gua.make_trans_mat(-0.03,0.0,-0.075-length/2*b)
                    elif f == 2:
                        bone_node.Transform.value = avango.gua.make_trans_mat(-0.01,0.0,-0.075-length/2*b)
                    elif f == 3:
                        bone_node.Transform.value = avango.gua.make_trans_mat(0.01,0.0,-0.075-length/2*b)
                    elif f == 4:
                        bone_node.Transform.value = avango.gua.make_trans_mat(0.03,0.0,-0.075-length/2*b)
                else:
                    if f == 0:
                        bone_node.Transform.value = avango.gua.make_trans_mat(0.0,0.0,-length/2*b)
                    elif f == 1:
                        bone_node.Transform.value = avango.gua.make_trans_mat(0.0,0.0,-length/2*b)
                    elif f == 2:
                        bone_node.Transform.value = avango.gua.make_trans_mat(0.0,0.0,-length/2*b)
                    elif f == 3:
                        bone_node.Transform.value = avango.gua.make_trans_mat(0.0,0.0,-length/2*b)
                    elif f == 4:
                        bone_node.Transform.value = avango.gua.make_trans_mat(0.0,0.0,-length/2*b)

                bone_geometry = _loader.create_geometry_from_file("bone" + str(f) + "-" + str(b) + "_geometry", "data/objects/cube.obj", avango.gua.LoaderFlags.DEFAULTS | avango.gua.LoaderFlags.MAKE_PICKABLE)
                bone_geometry.Material.value.set_uniform("Color", right_hand_color)
                bone_geometry.Transform.value = avango.gua.make_scale_mat(0.01,0.01,0.01) #* avango.gua.make_rot_mat(90.0,1.0,0.0,0.0) # todo: different length for bones
                bone_node.Children.value.append(bone_geometry)
                self.hands[0][f].append(bone_node)
                if b == 0:
                    self.rpalm_node.Children.value.append(bone_node)
                else:
                    self.hands[0][f][b-1].Children.value.append(bone_node)

        # print(self.hands)


        # left_hand_color = avango.gua.Vec4(0.0, 0.0, 1.0, 1.0)
        # self.lpalm_node = avango.gua.nodes.TransformNode(Name="left_palm_node")
        # self.lpalm_geometry = _loader.create_geometry_from_file("left_palm_geometry", "data/objects/cube.obj", avango.gua.LoaderFlags.DEFAULTS | avango.gua.LoaderFlags.MAKE_PICKABLE)
        # self.lpalm_geometry.Material.value.set_uniform("Color", left_hand_color)
        # self.lpalm_geometry.Transform.value = avango.gua.make_scale_mat(0.06,0.01,0.10)
        # self.lpalm_node.Children.value.append(self.lpalm_geometry)
        # self.leap_node.Children.value.append(self.lpalm_node)
        # for f in range(5):
        #     self.hands[1].append([])
        #     for b in range(3):
        #         bone_node = avango.gua.nodes.TransformNode(Name="bone" + f + "-" + b + "_node")
        #         bone_geometry = _loader.create_geometry_from_file("bone" + f + "-" + b + "_geometry", "data/objects/cube.obj", avango.gua.LoaderFlags.DEFAULTS | avango.gua.LoaderFlags.MAKE_PICKABLE)
        #         bone_geometry.Material.value.set_uniform("Color", right_hand_color)
        #         bone_geometry.Transform.value = avango.gua.make_scale_mat(0.01,0.01,0.03)
        #         bone_node.Children.value.append(bone_geometry)
        #         self.lpalm_node.Children.value.append(bone_node)
        #         self.hands[1][f].append(bone_node)


        self.always_evaluate(True) # change global evaluation policy

    def evaluate(self):
        frame = self.controller.frame()

        # self.handright_index_pos.value = self.get_leap_trans_mat(frame.hands.rightmost.fingers.finger_type(Finger.TYPE_INDEX)[0].tip_position)
        # self.handright_thumb_pos.value = self.get_leap_trans_mat(frame.hands.rightmost.fingers.finger_type(Finger.TYPE_THUMB)[0].tip_position)

        # self.handleft_index_pos.value = self.get_leap_trans_mat(frame.hands.leftmost.fingers.finger_type(Finger.TYPE_INDEX)[0].tip_position)
        # self.handleft_thumb_pos.value = self.get_leap_trans_mat(frame.hands.leftmost.fingers.finger_type(Finger.TYPE_THUMB)[0].tip_position)

        ### right hand palm position and rotation
        self.hand_right = frame.hands.rightmost
        self.rot_x = math.degrees(self.hand_right.direction.pitch)
        self.rot_y = - math.degrees(self.hand_right.direction.yaw)
        self.rot_z = math.degrees(self.hand_right.palm_normal.roll)
        handright_rot = avango.gua.make_rot_mat(self.rot_x, 1.0, 0.0, 0.0) *  avango.gua.make_rot_mat(self.rot_y, 0.0, 1.0, 0.0) * avango.gua.make_rot_mat(self.rot_z, 0.0, 0.0, 1.0)
        handright_pos = self.get_leap_trans_mat(frame.hands.rightmost.palm_position)
        self.rpalm_node.Transform.value = handright_pos * handright_rot

        ### left hand palm position and rotation
        # self.hand_left = frame.hands.leftmost
        # self.rot_x = math.degrees(self.hand_left.direction.pitch)
        # self.rot_y = - math.degrees(self.hand_left.direction.yaw)
        # self.rot_z = math.degrees(self.hand_left.palm_normal.roll)
        # handleft_rot = avango.gua.make_rot_mat(self.rot_x, 1.0, 0.0, 0.0) *  avango.gua.make_rot_mat(self.rot_y, 0.0, 1.0, 0.0) * avango.gua.make_rot_mat(self.rot_z, 0.0, 0.0, 1.0)
        # handleft_pos = self.get_leap_trans_mat(frame.hands.leftmost.palm_position)
        # self.lpalm_node.Transform.value = handleft_pos * handleft_rot

        ### get right hand bones
        for i, f in enumerate(self.hands[0]):
            finger = None
            if i == 0:
                finger = frame.hands.rightmost.fingers.finger_type(Finger.TYPE_THUMB)[0]
            elif i == 1:
                finger = frame.hands.rightmost.fingers.finger_type(Finger.TYPE_INDEX)[0]
            elif i == 2:
                finger = frame.hands.rightmost.fingers.finger_type(Finger.TYPE_MIDDLE)[0]
            elif i == 3:
                finger = frame.hands.rightmost.fingers.finger_type(Finger.TYPE_RING)[0]
            elif i == 4:
                finger = frame.hands.rightmost.fingers.finger_type(Finger.TYPE_PINKY)[0]

            if finger is not None:
                for j, b in enumerate(f):
                    bone = finger.bone(j)
                    length = bone.length
                    bone_node = self.hands[0][i][j]

                    # rot_x = math.degrees(bone.direction.pitch)
                    # rot_y = - math.degrees(bone.direction.yaw)

                    # trans = self.hands[0][i][j].Transform.value.get_translate()
                    # trans = avango.gua.make_trans_mat(bone.center.x, bone.center.y, bone.center.x)
                    trans = self.get_leap_trans_mat(bone.center)
                    # rot = avango.gua.make_rot_mat(rot_x, 1.0, 0.0, 0.0) *  avango.gua.make_rot_mat(rot_y, 0.0, 1.0, 0.0)
                    # _new_mat = avango.gua.make_trans_mat(trans) #* rot
                    _new_mat = trans
                    # if j == 0:
                    #     _new_mat = avango.gua.make_inverse_mat(bone_node.Parent.value.Transform.value) * \
                    #         avango.gua.make_inverse_mat(bone_node.Parent.value.Parent.value.Transform.value) * \
                    #         avango.gua.make_inverse_mat(bone_node.Parent.value.Parent.value.Parent.value.Transform.value) * \
                    #          _new_mat
                    # if j == 1:
                    #     _new_mat = avango.gua.make_inverse_mat(bone_node.Parent.value.Transform.value) * \
                    #         avango.gua.make_inverse_mat(bone_node.Parent.value.Parent.value.Transform.value) * \
                    #         avango.gua.make_inverse_mat(bone_node.Parent.value.Parent.value.Parent.value.Transform.value) * \
                    #         avango.gua.make_inverse_mat(bone_node.Parent.value.Parent.value.Parent.value.Parent.value.Transform.value) * \
                    #          _new_mat
                    # if j == 2:
                    #     if bone.center.x != 0.0:
                    #         print(str(bone.center.x), str(bone.center.y), str(bone.center.z))
                    #     _new_mat = avango.gua.make_inverse_mat(bone_node.Parent.value.Transform.value) * \
                    #         avango.gua.make_inverse_mat(bone_node.Parent.value.Parent.value.Transform.value) * \
                    #         avango.gua.make_inverse_mat(bone_node.Parent.value.Parent.value.Parent.value.Transform.value) * \
                    #         avango.gua.make_inverse_mat(bone_node.Parent.value.Parent.value.Parent.value.Parent.value.Transform.value) * \
                    #         avango.gua.make_inverse_mat(bone_node.Parent.value.Parent.value.Parent.value.Parent.value.Parent.value.Transform.value) * \
                    #          _new_mat

                    # bone_node.Transform.value = avango.gua.make_trans_mat(trans) * rot
                    bone_node.Transform.value = _new_mat

                    # if bone.center.x != 0.0:
                    #     print("bone", str(bone.center.x), str(bone.center.y), str(bone.center.z))

                    t = bone_node.Transform.value.get_translate()
                    if t.x != 0.0:
                        print("Transform", str(t.x), str(t.y), str(t.z))

                    # t = bone_node.WorldTransform.value.get_translate()
                    # # if t.x != -2.0:
                    # print("World", str(t.x), str(t.y), str(t.z))


        self.handright_pinch_strength = frame.hands.rightmost.pinch_strength
        self.handleft_pinch_strength = frame.hands.leftmost.pinch_strength

        # self.leap_node_rot.Transform.value = handright_rot
        # self.thumb_sphere.Transform.value = self.handright_thumb_pos.value * avango.gua.make_rot_mat(self.leap_node.Transform.value.get_rotate_scale_corrected())
        # self.index_sphere.Transform.value = self.handright_index_pos.value

        #check if to drag
        # _pos = self.thumb_sphere.WorldTransform.value.get_translate() # world position of thumb_sphere
        # for _node in self.TARGET_LIST: # iterate over all target nodes
        #     _bb = _node.BoundingBox.value # get bounding box of a node
        #     _rigid_body = _node.Parent.value.Parent.value

        #     print(_rigid_body.IsKinematic.value)

        #     if _bb.contains(_pos) == True: # hook inside bounding box of this node
        #         _node.Material.value.set_uniform("Color", avango.gua.Vec4(0.0,1.0,0.0,0.85)) # highlight color
        #         self.start_dragging(_rigid_body)
        #     else:
        #         _node.Material.value.set_uniform("Color", avango.gua.Vec4(1.0,0.0,0.0,1.0)) # default color

        # if self.handright_pinch_strength < self.pinch_threshold and self.dragged_node is not None:
        #     self.stop_dragging()

        # ## possibly update object dragging
        # self.dragging()

    def get_leap_trans_mat(self, pos):
        transmat = avango.gua.make_trans_mat(avango.gua.Vec3(pos.x / 1000, (pos.y / 1000), (pos.z / 1000)))
        return transmat


    # def start_dragging(self, NODE):
    #     self.dragged_node = NODE        
    #     # self.dragged_node.IsKinematic.value = False
    #     self.dragging_offset_mat = avango.gua.make_inverse_mat(self.thumb_sphere.WorldTransform.value) * self.dragged_node.WorldTransform.value # object transformation in pointer coordinate system

  
    # def stop_dragging(self): 
    #     # self.dragged_node.IsKinematic.value = True
    #     self.dragged_node = None
    #     self.dragging_offset_mat = avango.gua.make_identity_mat()


    # def dragging(self):
    #     if self.dragged_node is not None: # object to drag
    #         _new_mat = self.thumb_sphere.WorldTransform.value * self.dragging_offset_mat # new object position in world coodinates
    #         _new_mat = avango.gua.make_inverse_mat(self.dragged_node.Parent.value.WorldTransform.value) * _new_mat # transform new object matrix from global to local space
        
    #         self.dragged_node.Transform.value = _new_mat


class SampleListener(leap.Leap.Listener):
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

