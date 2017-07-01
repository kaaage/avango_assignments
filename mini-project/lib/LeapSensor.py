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
        self.leap_node.Transform.value = avango.gua.make_trans_mat(0.0, 0.06, 0.44) * avango.gua.make_rot_mat(-77.0, 1, 0, 0)
        self.BASENODE.Children.value.append(self.leap_node)

        self.leap_node_rot = avango.gua.nodes.TransformNode(Name="leap_node")
        self.leap_node.Children.value.append(self.leap_node_rot)

        # Finger tips visualization
        _loader = avango.gua.nodes.TriMeshLoader() # get trimesh loader to load external meshes
        self.thumb_sphere = avango.gua.nodes.TransformNode(Name="thumb_sphere")
        self.thumb_sphere.Transform.value = self.handright_thumb_pos.value
        self.thumb_sphere_geometry = _loader.create_geometry_from_file("thumb_sphere", "data/objects/sphere.obj", avango.gua.LoaderFlags.DEFAULTS)
        self.thumb_sphere_geometry.Material.value.set_uniform("Color", avango.gua.Vec4(1.0, 0.0, 0.0, 1.0))
        self.thumb_sphere_geometry.Transform.value = avango.gua.make_scale_mat(0.01,0.01,0.01)
        self.thumb_sphere.Children.value.append(self.thumb_sphere_geometry)
        self.leap_node.Children.value.append(self.thumb_sphere)

        self.index_sphere = avango.gua.nodes.TransformNode(Name="index_sphere")
        self.index_sphere.Transform.value = self.handright_index_pos.value
        self.index_sphere_geometry = _loader.create_geometry_from_file("index_sphere", "data/objects/sphere.obj", avango.gua.LoaderFlags.DEFAULTS)
        self.index_sphere_geometry.Material.value.set_uniform("Color", avango.gua.Vec4(1.0, 0.0, 0.0, 1.0))
        self.index_sphere_geometry.Transform.value = avango.gua.make_scale_mat(0.01,0.01,0.01)
        self.index_sphere.Children.value.append(self.index_sphere_geometry)
        self.leap_node.Children.value.append(self.index_sphere)

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

        self.handright_pinch_strength = frame.hands.rightmost.pinch_strength
        self.handleft_pinch_strength = frame.hands.leftmost.pinch_strength

        self.leap_node_rot.Transform.value = handright_rot
        self.thumb_sphere.Transform.value = self.handright_thumb_pos.value * avango.gua.make_rot_mat(self.leap_node.Transform.value.get_rotate_scale_corrected())
        self.index_sphere.Transform.value = self.handright_index_pos.value

        #check if to drag
        _pos = self.thumb_sphere.WorldTransform.value.get_translate() # world position of thumb_sphere
        for _node in self.TARGET_LIST: # iterate over all target nodes
            _bb = _node.BoundingBox.value # get bounding box of a node
            _rigid_body = _node.Parent.value.Parent.value

            print(_rigid_body.IsKinematic.value)

            if _bb.contains(_pos) == True: # hook inside bounding box of this node
                _node.Material.value.set_uniform("Color", avango.gua.Vec4(0.0,1.0,0.0,0.85)) # highlight color
                self.start_dragging(_rigid_body)
            else:
                _node.Material.value.set_uniform("Color", avango.gua.Vec4(1.0,0.0,0.0,1.0)) # default color

        if self.handright_pinch_strength < self.pinch_threshold and self.dragged_node is not None:
            self.stop_dragging()

        ## possibly update object dragging
        self.dragging()

    def get_leap_trans_mat(self, pos):
        transmat = avango.gua.make_trans_mat(avango.gua.Vec3(pos.x / 1000, (pos.y / 1000), (pos.z / 1000)))
        return transmat


    def start_dragging(self, NODE):
        self.dragged_node = NODE        
        # self.dragged_node.IsKinematic.value = False
        self.dragging_offset_mat = avango.gua.make_inverse_mat(self.thumb_sphere.WorldTransform.value) * self.dragged_node.WorldTransform.value # object transformation in pointer coordinate system

  
    def stop_dragging(self): 
        # self.dragged_node.IsKinematic.value = True
        self.dragged_node = None
        self.dragging_offset_mat = avango.gua.make_identity_mat()


    def dragging(self):
        if self.dragged_node is not None: # object to drag
            _new_mat = self.thumb_sphere.WorldTransform.value * self.dragging_offset_mat # new object position in world coodinates
            _new_mat = avango.gua.make_inverse_mat(self.dragged_node.Parent.value.WorldTransform.value) * _new_mat # transform new object matrix from global to local space
        
            self.dragged_node.Transform.value = _new_mat


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

