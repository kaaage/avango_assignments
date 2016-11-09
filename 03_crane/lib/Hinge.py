#!/usr/bin/python

# import guacamole libraries
import avango
import avango.gua
import avango.script
from avango.script import field_has_changed


class Hinge(avango.script.Script):

    ## input fields
    sf_rot_value = avango.SFFloat()

    ### class variables ###

    # Number of Hinge instances that have already been created.
    number_of_instances = 0
   
    # constructor
    def __init__(self):
        self.super(Hinge).__init__()

        ## get unique id for this instance
        self.id = Hinge.number_of_instances
        Hinge.number_of_instances += 1



    def my_constructor(self,
        PARENT_NODE = None,
        DIAMETER = 0.1, # in meter
        HEIGHT = 0.1, # in meter
        ROT_OFFSET_MAT = avango.gua.make_identity_mat(), # the rotation offset relative to the parent coordinate system
        ROT_AXIS = avango.gua.Vec3(0,1,0), # the axis to rotate arround with the rotation input (default is head axis)
        ROT_CONSTRAINT = [-45.0, 45.0], # intervall with min and max rotation of this hinge
        ):


        ### variables ###
        ## ToDo: evtl. init further variables


        ### parameters ###        
        self.rot_axis = ROT_AXIS
        
        self.rot_constraint = ROT_CONSTRAINT


        ### resources ###

        _loader = avango.gua.nodes.TriMeshLoader() # get trimesh loader to load external tri-meshes

        ## ToDo: init hinge node(s)
        # ...

        
    ### callback functions ###
    
    @field_has_changed(sf_rot_value)
    def sf_rot_value_changed(self):
        pass
        ## ToDo: accumulate input to hinge node && consider rotation contraints of this hinge
        # ...
        
        
