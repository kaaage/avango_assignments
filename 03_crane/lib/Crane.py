#!/usr/bin/python

# import guacamole libraries
import avango
import avango.gua


### import application libraries
from lib.KeyboardInput import KeyboardInput
from lib.Hinge import Hinge
from lib.Arm import Arm
from lib.Hook import Hook


class Crane:
  
    # constructor
    def __init__(self,
        PARENT_NODE = None,
        TARGET_LIST = [],
        ):

        
        ### resources ###

        ## init base node for whole crane
        self.base_node = avango.gua.nodes.TransformNode(Name = "base_node")
        self.base_node.Transform.value = avango.gua.make_trans_mat(0.0,-0.1,0.0)
        PARENT_NODE.Children.value.append(self.base_node)


        ## init internal sub-classes
        self.input = KeyboardInput()


        ## ToDo: init first hinge && connect rotation input 
        self.hinge1 = Hinge()
        self.hinge1.my_constructor(PARENT_NODE = self.base_node, DIAMETER = 0.1, HEIGHT = 0.01, \
            ROT_OFFSET_MAT = avango.gua.make_identity_mat(), ROT_AXIS = avango.gua.Vec3(0,1,0), \
            ROT_CONSTRAINT = [-180.0, 180.0])
        self.hinge1.sf_rot_value.connect_from(self.input.sf_rot_value0)

        #self.hinge1.connect_from(self.KeyboardInput.Button1) 


        ## ToDo: init first arm-segment
        # ...
        self.arm1 = Arm(PARENT_NODE = self.hinge1.get_hinge_transform_node(), DIAMETER = 0.01, LENGTH = 0.1, ROT_OFFSET_MAT = avango.gua.make_identity_mat())


        ## ToDo: init second hinge && connect rotation input 
        # ...
        self.hinge2 = Hinge()
        self.hinge2.my_constructor(PARENT_NODE = self.hinge1.get_hinge_transform_node(), DIAMETER = 0.02, HEIGHT = 0.01, \
            ROT_OFFSET_MAT = avango.gua.make_rot_mat(90, 1, 0, 0), ROT_AXIS = avango.gua.Vec3(0,0,1), \
            ROT_CONSTRAINT = [0.0, 90.0], TRANS_OFFSET = self.arm1.length)
        self.hinge2.sf_rot_value.connect_from(self.input.sf_rot_value1)


        # # ## ToDo: init second arm-segment
        # # # ...
        self.arm2 = Arm(PARENT_NODE = self.hinge2.get_hinge_transform_node(), DIAMETER = 0.01, LENGTH = 0.1, ROT_OFFSET_MAT = avango.gua.make_identity_mat())
        

        # # ## ToDo: init third hinge && connect rotation input 
        # # # ...
        self.hinge3 = Hinge()
        self.hinge3.my_constructor(PARENT_NODE = self.hinge2.get_hinge_transform_node(), DIAMETER = 0.02, HEIGHT = 0.01, \
            ROT_OFFSET_MAT = avango.gua.make_rot_mat(90, 1, 0, 0), ROT_AXIS = avango.gua.Vec3(0,0,1), \
            ROT_CONSTRAINT = [-90.0, 90.0], TRANS_OFFSET = self.arm2.length)
        self.hinge3.sf_rot_value.connect_from(self.input.sf_rot_value2)


        # # ## ToDo: init third arm-segment
        # # # ...
        self.arm3 = Arm(PARENT_NODE = self.hinge3.get_hinge_transform_node(), DIAMETER = 0.01, LENGTH = 0.1, ROT_OFFSET_MAT = avango.gua.make_identity_mat())


        # # ## ToDo: init hook
        # # # ...
        self.hook = Hook()
        self.hook.my_constructor(PARENT_NODE = self.hinge3.get_hinge_transform_node(), SIZE = 0.025, TARGET_LIST = TARGET_LIST, OFFSET = self.arm3.length)
        self.hook.sf_mat.connect_from(self.hook.hook_geometry.WorldTransform)
 
