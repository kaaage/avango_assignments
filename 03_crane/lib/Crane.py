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
        # ...
        

        ## ToDo: init first arm-segment
        # ...



        ## ToDo: init second hinge && connect rotation input 
        # ...


        ## ToDo: init second arm-segment
        # ...
        

        ## ToDo: init third hinge && connect rotation input 
        # ...


        ## ToDo: init third arm-segment
        # ...


        ## ToDo: init hook
        # ...

 
