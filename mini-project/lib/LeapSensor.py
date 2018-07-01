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

    handright_grab_strength = 0
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
        self.dragging_mode = False
        self.dragged_node = None
        self.dragging_offset_mat = avango.gua.make_identity_mat()
        self.prev_pinch = 0.0

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


        # Finger tips visualization
        _loader = avango.gua.nodes.TriMeshLoader() # get trimesh loader to load external meshes
        

        self.index_tip = avango.gua.nodes.TransformNode(Name="index_tip")
        self.left_index_tip = avango.gua.nodes.TransformNode(Name="index_tip")


        self.righthand = [[], []]
        self.lefthand = [[], []]

        hand_color = avango.gua.Vec4(0.6, 0.6, 0.64, 0.6)
        palm_color = avango.gua.Vec4(0.6, 0.6, 0.64, 0.6)

        self.rpalm_node = avango.gua.nodes.TransformNode(Name="right_palm_node")
        self.rpalm_geometry = _loader.create_geometry_from_file("right_palm_geometry", "data/objects/cube.obj", avango.gua.LoaderFlags.DEFAULTS | avango.gua.LoaderFlags.MAKE_PICKABLE)
        self.rpalm_geometry.Material.value.set_uniform("Color", palm_color)
        self.rpalm_geometry.Transform.value = avango.gua.make_scale_mat(0.04,0.01,0.05)
        self.rpalm_node.Children.value.append(self.rpalm_geometry)
        self.leap_node.Children.value.append(self.rpalm_node)

        #TODO: draw for physical hand position just the finger tips or the outline
        for f in range(5):
            self.righthand[0].append([])
            for b in range(4):
                # if f == 0 and b == 0: # Disable the not existent fourth thumb bone
                #     continue
                length = 0.03
                bone_node = avango.gua.nodes.TransformNode(Name="bone" + str(f) + "-" + str(b) + "_node")
               
                bone_geometry = _loader.create_geometry_from_file("bone" + str(f) + "-" + str(b) + "_geometry", "data/objects/cube.obj", avango.gua.LoaderFlags.DEFAULTS | avango.gua.LoaderFlags.MAKE_PICKABLE)
                bone_geometry.Material.value.set_uniform("Color", hand_color)

                # color index and thumb tip differently
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
                # if f == 0 and b == 0:
                #     continue
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
        if frame.hands.rightmost.is_valid:

            self.leap_node.Transform.value = avango.gua.make_trans_mat(0.0, 0.0, 0.0) # easiest way to hide/unhide the undefined leap bones

            ### right hand palm position and rotation
            self.hand_right = frame.hands.rightmost
            handright_pos = self.get_leap_trans_mat(self.hand_right.palm_position)
            self.rpalm_node.Transform.value = handright_pos * self.get_bone_rotation(self.hand_right)

            ### left hand palm position and rotation
            self.hand_left = frame.hands.leftmost
            handleft_pos = self.get_leap_trans_mat(self.hand_left.palm_position)
            self.lpalm_node.Transform.value = handleft_pos *  self.get_bone_rotation(self.hand_left)

            self.handright_pinch_strength = self.hand_right.pinch_strength
            self.handleft_pinch_strength = self.hand_left.pinch_strength

            self.hand_right.grab_strength
                # #TODO: Show hand.confidence 
                # print ("Right Hand | Left Hand")
                # print (self.hand_right.confidence)
                # print (self.hand_right.confidence)


            ### get right hand bones
            for i, f in enumerate(self.righthand[0]):
                finger = None
                if i == 0:
                    finger = self.hand_right.fingers.finger_type(Finger.TYPE_THUMB)[0]
                elif i == 1:
                    finger = self.hand_right.fingers.finger_type(Finger.TYPE_INDEX)[0]
                elif i == 2:
                    finger = self.hand_right.fingers.finger_type(Finger.TYPE_MIDDLE)[0]
                elif i == 3:
                    finger = self.hand_right.fingers.finger_type(Finger.TYPE_RING)[0]
                elif i == 4:
                    finger = self.hand_right.fingers.finger_type(Finger.TYPE_PINKY)[0]

                if finger is not None:
                    for j, b in enumerate(f):
                        # if b == 0 and j == 0:
                        #     continue
                        bone = finger.bone(j)
                        length = bone.length
                        bone_node = self.righthand[0][i][j]

                        bone_node.Children.value[0].Transform.value = avango.gua.make_scale_mat(0.01,0.01, length * 0.001)

                        trans = self.get_leap_trans_mat(bone.center)
                        rot = self.get_bone_rotation(bone)

                        bone_node.Transform.value = trans * rot
                        
                        # bone_node.Tags.value = ["invisible"] # does not fully hide object (black transparent)
                        # bone_node.Children.value[0].Material.value.set_uniform("Color", avango.gua.Vec4(0.0,0.0,0.0,0.0)) #(some?) Field does not have material 


                        #TODO: Higlight finger when pinching
                        # if self.handright_pinch_strength > self.pinch_threshold:
                        #     bone_node.Material.value.set_uniform("Color", avango.gua.Vec4(0.0, 0.8, 0.8, 1.0))
                        # else:
                        #     bone_node.Children.value[0].Material.value.set_uniform("Color", avango.gua.Vec4(0.0, 1.0, 1.0, 1.0))
                  

            ### get left hand bones
            for i, f in enumerate(self.lefthand[0]):
                #TODO: if there is only one hand left hand or right hand they get rendered at same position
                #TODO: Left hand got a strange color 
                finger = None
                if i == 0:
                    finger = self.hand_left.fingers.finger_type(Finger.TYPE_THUMB)[0]
                elif i == 1:
                    finger = self.hand_left.fingers.finger_type(Finger.TYPE_INDEX)[0]
                elif i == 2:
                    finger = self.hand_left.fingers.finger_type(Finger.TYPE_MIDDLE)[0]
                elif i == 3:
                    finger = self.hand_left.fingers.finger_type(Finger.TYPE_RING)[0]
                elif i == 4:
                    finger = self.hand_left.fingers.finger_type(Finger.TYPE_PINKY)[0]

                if finger is not None:
                    for j, b in enumerate(f):
                        # if b == 0 and j == 0:
                        #     continue
                        bone = finger.bone(j)
                        length = bone.length
                        bone_node = self.lefthand[0][i][j]

                        bone_node.Children.value[0].Transform.value = avango.gua.make_scale_mat(0.01,0.01, length * 0.001)

                        # together with rotation
                        trans = self.get_leap_trans_mat(bone.center)
                        rot = self.get_bone_rotation(bone)

                        bone_node.Transform.value = trans * rot
                     

            ## drag and drop
            # check if to drag
            self.dragging()

            _index_pos = self.index_tip.WorldTransform.value.get_translate() # world position of thumb_sphere
            _left_index_pos = self.left_index_tip.WorldTransform.value.get_translate()
            _handright_pos = self.rpalm_geometry.WorldTransform.value.get_translate()

            for _node in self.TARGET_LIST: # iterate over all target nodes
                _bb = _node.BoundingBox.value # get bounding box of a node
                # _transform = _node.Parent.value

                # print(_rigid_body.IsKinematic.value) #TODO: We wanted to have physics :'(

                if _bb.contains(_index_pos) == True and _bb.contains(_left_index_pos) == False: # hook inside bounding box of this node
                    _node.Material.value.set_uniform("Color", avango.gua.Vec4(0.0,1.0,0.0,1.0)) # highlight color
                    # if self.handright_grab_strength > # TODO initialize scaling down of objects and delete if smaller than some threshold

                    if self.dragging_mode == False:
                        if self.handright_pinch_strength > self.pinch_threshold:
                        # if self.dragging_mode == True:
                            self.start_dragging(_node)
                    elif self.dragging_mode == True:
                        self.start_scaling(_node, self.handright_pinch_strength)

                if _bb.contains(_handright_pos) == True and self.hand_right.grab_strength >= 0.7:
                    _node.Material.value.set_uniform("Color", avango.gua.Vec4(1.0,0.0,0.0,1.0)) # highlight color

                    if self.hand_right.grab_strength > 0.9:
                        _node.Transform.value = avango.gua.make_scale_mat(0.0)
                        self.stop_dragging()



                if _bb.contains(_index_pos) == False and _bb.contains(_handright_pos) == False:
                    _node.Material.value.set_uniform("Color", avango.gua.Vec4(1.0,1.0,1.0,1.0)) # default color


            if self.handright_pinch_strength < self.pinch_threshold and self.dragged_node is not None:
                self.stop_dragging()

        else:
            self.leap_node.Transform.value = avango.gua.make_trans_mat(0.0, -2.0, 0.0) # hide undefined leap bones

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
        return avango_mat

    def start_dragging(self, NODE):
        self.dragged_node = NODE        
        # self.dragged_node.IsKinematic.value = False
        self.dragging_offset_mat = avango.gua.make_inverse_mat(self.index_tip.WorldTransform.value) * self.dragged_node.WorldTransform.value # object transformation in pointer coordinate system
        # print("Start dragging")

    def stop_dragging(self): 
        # self.dragged_node.IsKinematic.value = True
        self.dragged_node = None
        self.dragging_offset_mat = avango.gua.make_identity_mat()
        # print("Stopped dragging")

    def dragging(self):
        if self.dragged_node is not None: # object to drag
            _world_mat = self.index_tip.WorldTransform.value * self.dragging_offset_mat # new object position in world coodinates
            # _scale_node = _node.Parent.value
            # _trans_node = _scale_node.Parent.value
            # _parent = _trans_node.Parent.value
            _local_mat = avango.gua.make_inverse_mat(self.dragged_node.Parent.value.WorldTransform.value) * _world_mat # transform new object matrix from global to local space
            # _local_mat = avango.gua.make_inverse_mat(_parent) * avango.gua.make_inverse_mat(_trans_node) * avango.gua.make_inverse_mat(_scale_node) * _world_mat # transform new object matrix from global to local space
        
            self.dragged_node.Transform.value = _local_mat
    
    def start_scaling(self, NODE, pinch_strength): 
        #TODO: add two handed scaling functionality
        #This all can be used to calculate distance between two positions
        #This distance is used than as the scaling factor
        # self.eye_to_object = self.hit_position * avango.osg.make_inverse_mat(self.HeadTransform.value)
        # self.object_distance = self.eye_to_object.length()
        # self.eye_to_object_normalized = self.eye_to_object / self.object_distance

        # right = self.hand_right.fingers.finger_type(Finger.TYPE_INDEX)[0].bone(3)
        # left = self.hand_leftt.fingers.finger_type(Finger.TYPE_INDEX)[0].bone(3)
        # distance = left.distance_to(right)
        # print(distance)

        factor = self.prev_pinch - pinch_strength
        print(factor)

        trans_mat = avango.gua.make_trans_mat(NODE.Transform.value.get_translate())
        rot_mat = avango.gua.make_rot_mat(NODE.Transform.value.get_rotate_scale_corrected())
        _new_scale = NODE.Transform.value.get_scale().x * (1.0 + factor)
        _new_scale = min(max(_new_scale, 0.05),0.5)
        scale_mat = avango.gua.make_scale_mat(_new_scale)

        NODE.Transform.value = trans_mat * rot_mat * scale_mat

        self.prev_pinch = pinch_strength

class SampleListener(leap.Leap.Listener):
    def on_init(self, controller):
        print("Initialized")

    def on_connect(self, controller):
        print("Connected")

    def on_disconnect(self, controller):
        # Note: not dispatched when running in a debugger.
        print("Disconnected")

    def on_exit(self, controller):
        print("Exited")

