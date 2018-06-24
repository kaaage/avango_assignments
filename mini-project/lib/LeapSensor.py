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
        print("Target list len: " + str(len(self.TARGET_LIST)))

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

        self.index_tip = avango.gua.nodes.TransformNode(Name="index_tip")
        # self.index_tip_geometry = _loader.create_geometry_from_file("index_tip", "data/objects/sphere.obj", avango.gua.LoaderFlags.DEFAULTS)
        # self.index_tip_geometry.Material.value.set_uniform("Color", avango.gua.Vec4(0.0, 1.0, 1.0, 1.0))
        # self.index_tip_geometry.Transform.value = avango.gua.make_scale_mat(1)
        # self. .Children.value.append(self.index_tip_geometry)
        ##self.leap_node.Children.value.append(self.index_tip)

        self.righthand = [[], []]
        self.lefthand = [[], []]
        # self.hands.append([])
        # self.hands.append([])

        hand_color = avango.gua.Vec4(0.6, 0.6, 0.64, 0.6)
        palm_color = avango.gua.Vec4(1.0, 0.0, 0.0, 0.5)

        self.rpalm_node = avango.gua.nodes.TransformNode(Name="right_palm_node")
        self.rpalm_geometry = _loader.create_geometry_from_file("right_palm_geometry", "data/objects/cube.obj", avango.gua.LoaderFlags.DEFAULTS | avango.gua.LoaderFlags.MAKE_PICKABLE)
        self.rpalm_geometry.Material.value.set_uniform("Color", palm_color)
        self.rpalm_geometry.Transform.value = avango.gua.make_scale_mat(0.04,0.01,0.05)
        self.rpalm_node.Children.value.append(self.rpalm_geometry)
        self.leap_node.Children.value.append(self.rpalm_node)


        #TODO: draw for physical hand position just the finger tips or the outline
        #TODO: connect physical hand position visually with virtual hand position
        for f in range(5):
            self.righthand[0].append([])
            for b in range(4):
                length = 0.03
                bone_node = avango.gua.nodes.TransformNode(Name="bone" + str(f) + "-" + str(b) + "_node")
               
                bone_geometry = _loader.create_geometry_from_file("bone" + str(f) + "-" + str(b) + "_geometry", "data/objects/cube.obj", avango.gua.LoaderFlags.DEFAULTS | avango.gua.LoaderFlags.MAKE_PICKABLE)
                bone_geometry.Material.value.set_uniform("Color", hand_color)
                if f == 1 and b == 3:   
                    bone_node.Children.value.append(self.index_tip)
                    bone_geometry.Material.value.set_uniform("Color", avango.gua.Vec4(0.0, 1.0, 1.0, 1.0))
                if f == 0 and b == 3:   
                    bone_geometry.Material.value.set_uniform("Color", avango.gua.Vec4(0.0, 1.0, 1.0, 1.0))

                # TODO: different length for bones from bone.length property
                bone_geometry.Transform.value = avango.gua.make_scale_mat(0.01,0.01,0.02) #* avango.gua.make_rot_mat(90.0,1.0,0.0,0.0) 
                bone_node.Children.value.append(bone_geometry)
                self.righthand[0][f].append(bone_node)
                
                self.leap_node.Children.value.append(bone_node)

        self.lpalm_node = avango.gua.nodes.TransformNode(Name="left_palm_node")
        self.lpalm_geometry = _loader.create_geometry_from_file("left_palm_geometry", "data/objects/cube.obj", avango.gua.LoaderFlags.DEFAULTS | avango.gua.LoaderFlags.MAKE_PICKABLE)
        self.lpalm_geometry.Material.value.set_uniform("Color", palm_color)
        self.lpalm_geometry.Transform.value = avango.gua.make_scale_mat(0.04,0.01,0.05)
        self.lpalm_node.Children.value.append(self.lpalm_geometry)
        self.leap_node.Children.value.append(self.lpalm_node)
        for f in range(5):
            self.lefthand[0].append([])
            for b in range(4):
                length = 0.03
                bone_node = avango.gua.nodes.TransformNode(Name="bone" + str(f) + "-" + str(b) + "_node")
               
                bone_geometry = _loader.create_geometry_from_file("bone" + str(f) + "-" + str(b) + "_geometry", "data/objects/cube.obj", avango.gua.LoaderFlags.DEFAULTS | avango.gua.LoaderFlags.MAKE_PICKABLE)
                bone_geometry.Material.value.set_uniform("Color", hand_color)
                # TODO: different length for bones from bone.length property
                bone_geometry.Transform.value = avango.gua.make_scale_mat(0.01,0.01,0.02) #* avango.gua.make_rot_mat(90.0,1.0,0.0,0.0)
                bone_node.Children.value.append(bone_geometry)
                self.lefthand[0][f].append(bone_node)
                
                self.leap_node.Children.value.append(bone_node)





        self.always_evaluate(True) # change global evaluation policy

    def evaluate(self):
        frame = self.controller.frame()

        # self.handright_index_pos.value = self.get_leap_trans_mat(frame.hands.rightmost.fingers.finger_type(Finger.TYPE_INDEX)[0].tip_position)
        # self.handright_thumb_pos.value = self.get_leap_trans_mat(frame.hands.rightmost.fingers.finger_type(Finger.TYPE_THUMB)[0].tip_position)

        # self.handleft_index_pos.value = self.get_leap_trans_mat(frame.hands.leftmost.fingers.finger_type(Finger.TYPE_INDEX)[0].tip_position)
        # self.handleft_thumb_pos.value = self.get_leap_trans_mat(frame.hands.leftmost.fingers.finger_type(Finger.TYPE_THUMB)[0].tip_position)

        #TODO: Show hand.confidence 

        ### right hand palm position and rotation
        self.hand_right = frame.hands.rightmost
        self.rot_x = math.degrees(self.hand_right.direction.pitch)
        self.rot_y = - math.degrees(self.hand_right.direction.yaw)
        self.rot_z = math.degrees(self.hand_right.palm_normal.roll)
        handright_rot = avango.gua.make_rot_mat(self.rot_x, 1.0, 0.0, 0.0) *  avango.gua.make_rot_mat(self.rot_y, 0.0, 1.0, 0.0) * avango.gua.make_rot_mat(self.rot_z, 0.0, 0.0, 1.0)
        handright_pos = self.get_leap_trans_mat(frame.hands.rightmost.palm_position)
        #TODO something is still wrong with the palm position transpation
        self.rpalm_node.Transform.value = handright_pos * handright_rot

        ### left hand palm position and rotation
        self.hand_left = frame.hands.leftmost
        self.rot_x = math.degrees(self.hand_left.direction.pitch)
        self.rot_y = - math.degrees(self.hand_left.direction.yaw)
        self.rot_z = math.degrees(self.hand_left.palm_normal.roll)
        handleft_rot = avango.gua.make_rot_mat(self.rot_x, 1.0, 0.0, 0.0) *  avango.gua.make_rot_mat(self.rot_y, 0.0, 1.0, 0.0) * avango.gua.make_rot_mat(self.rot_z, 0.0, 0.0, 1.0)
        handleft_pos = self.get_leap_trans_mat(frame.hands.leftmost.palm_position)
        self.lpalm_node.Transform.value = handleft_pos * handleft_rot

        self.handright_pinch_strength = frame.hands.rightmost.pinch_strength
        self.handleft_pinch_strength = frame.hands.leftmost.pinch_strength

        ### get right hand bones
        for i, f in enumerate(self.righthand[0]):
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
                    bone_node = self.righthand[0][i][j]

                    bone_node.Children.value[0].Transform.value = avango.gua.make_scale_mat(0.01,0.01, length * 0.001)

                    trans = self.get_leap_trans_mat(bone.center)
                    rot = self.get_bone_rotation(bone)

                    bone_node.Transform.value = trans * rot
                    

                    #TODO: Higlight finger when pinching
                    # if self.handright_pinch_strength > self.pinch_threshold:
                    #     bone_node.Material.value.set_uniform("Color", avango.gua.Vec4(0.0, 0.8, 0.8, 1.0))
                    # else:
                    #     bone_node.Children.value[0].Material.value.set_uniform("Color", avango.gua.Vec4(0.0, 1.0, 1.0, 1.0))
              

                    # if bone.center.x != 0:
                    #     print(rot)


                    # if bone.center.x != 0.0:
                    #     print("bone", str(bone.center.x), str(bone.center.y), str(bone.center.z))

                    t = bone_node.Transform.value.get_translate()
                    #if t.x != 0.0:
                     #   print("Transform", str(t.x), str(t.y), str(t.z))

                    # t = bone_node.WorldTransform.value.get_translate()
                    # if t.x != -2.0:
                    #     print("World", str(t.x), str(t.y), str(t.z))

        ### get left hand bones
        for i, f in enumerate(self.lefthand[0]):
            #TODO: if there is one hand left hand and right hand get rendered at same position
            #TODO: Hide all bones that are not tracked (no hand visible no bones in center)
            finger = None
            if i == 0:
                finger = frame.hands.leftmost.fingers.finger_type(Finger.TYPE_THUMB)[0]
            elif i == 1:
                finger = frame.hands.leftmost.fingers.finger_type(Finger.TYPE_INDEX)[0]
            elif i == 2:
                finger = frame.hands.leftmost.fingers.finger_type(Finger.TYPE_MIDDLE)[0]
            elif i == 3:
                finger = frame.hands.leftmost.fingers.finger_type(Finger.TYPE_RING)[0]
            elif i == 4:
                finger = frame.hands.leftmost.fingers.finger_type(Finger.TYPE_PINKY)[0]

            if finger is not None:
                for j, b in enumerate(f):
                    bone = finger.bone(j)
                    length = bone.length
                    bone_node = self.lefthand[0][i][j]

                    bone_node.Children.value[0].Transform.value = avango.gua.make_scale_mat(0.01,0.01, length * 0.001)

                    # together with rotation
                    trans = self.get_leap_trans_mat(bone.center)
                    rot = self.get_bone_rotation(bone)

                    bone_node.Transform.value = trans * rot
                 



        # self.leap_node_rot.Transform.value = handright_rot
        # self.thumb_sphere.Transform.value = self.handright_thumb_pos.value * avango.gua.make_rot_mat(self.leap_node.Transform.value.get_rotate_scale_corrected())
        # self.index_tip.Transform.value = self.handright_index_pos.value

        ## drag and drop
        # check if to drag
        _pos = self.index_tip.WorldTransform.value.get_translate() # world position of thumb_sphere
        for _node in self.TARGET_LIST: # iterate over all target nodes
            # print(_node)
            _bb = _node.BoundingBox.value # get bounding box of a node
            _transform = _node.Parent.value

            # print(_rigid_body.IsKinematic.value)

            if _bb.contains(_pos) == True: # hook inside bounding box of this node
                _node.Material.value.set_uniform("Color", avango.gua.Vec4(0.0,1.0,0.0,1.0)) # highlight color
                if self.handright_pinch_strength > self.pinch_threshold:
                    self.start_dragging(_node)
            else:
                _node.Material.value.set_uniform("Color", avango.gua.Vec4(1.0,1.0,1.0,1.0)) # default color

        if self.handright_pinch_strength < self.pinch_threshold and self.dragged_node is not None:
            self.stop_dragging()

        ## possibly update object dragging
        self.dragging()

    def get_leap_trans_mat(self, pos):
        transmat = avango.gua.make_trans_mat(avango.gua.Vec3(pos.x / 1000, (pos.y / 1000), (pos.z / 1000)))
        return transmat

    def get_bone_rotation(self, bone):
        # can be used to get a 3x3 or 4x4 rotation matrix

        local_rotation = bone.basis.rigid_inverse().to_array_4x4()
        avango_mat = avango.gua.make_identity_mat()
        for row in range(0, 4):
            for col in range(0, 4):
                pos = col + (4 * row)
                avango_mat.set_element(row, col, local_rotation[pos])
        #print (local_rotation)
        #print (avango_mat)

        return avango_mat

    def start_dragging(self, NODE):
        self.dragged_node = NODE        
        # self.dragged_node.IsKinematic.value = False
        self.dragging_offset_mat = avango.gua.make_inverse_mat(self.index_tip.WorldTransform.value) * self.dragged_node.WorldTransform.value # object transformation in pointer coordinate system
        print("Start dragging")

  
    def stop_dragging(self): 
        # self.dragged_node.IsKinematic.value = True
        self.dragged_node = None
        self.dragging_offset_mat = avango.gua.make_identity_mat()
        print("Stopped dragging")



    def dragging(self):
        if self.dragged_node is not None: # object to drag
            _new_mat = self.index_tip.WorldTransform.value * self.dragging_offset_mat # new object position in world coodinates
            _new_mat = avango.gua.make_inverse_mat(self.dragged_node.Parent.value.WorldTransform.value) * _new_mat # transform new object matrix from global to local space
        
            self.dragged_node.Transform.value = _new_mat
            print(self.dragged_node.Transform.value)


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

