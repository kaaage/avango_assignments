#!/usr/bin/python

# import guacamole libraries
import avango
import avango.gua


class Arm:

    ### class variables ###

    # Number of Hinge instances that have already been created.
    number_of_instances = 0
    
  
    # constructor
    def __init__(self,
        PARENT_NODE = None,
        DIAMETER = 0.1, # in meter
        LENGTH = 0.1, # in meter
        ROT_OFFSET_MAT = avango.gua.make_identity_mat(), # the rotation offset relative to the parent coordinate system
        ):

        ## get unique id for this instance
        self.id = Arm.number_of_instances
        Arm.number_of_instances += 1


        ### resources ###

        _loader = avango.gua.nodes.TriMeshLoader() # get trimesh loader to load external tri-meshes
        
        ## ToDo: init arm node(s)
        # ...
                                
