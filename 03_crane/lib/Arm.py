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

        self.length = LENGTH


        ### resources ###

        _loader = avango.gua.nodes.TriMeshLoader() # get trimesh loader to load external tri-meshes
        
        ## ToDo: init arm node(s)
        # ...
        self.arm_geometry = _loader.create_geometry_from_file("arm_geometry", "data/objects/cylinder.obj", avango.gua.LoaderFlags.DEFAULTS)
        self.arm_geometry.Transform.value = avango.gua.make_trans_mat(0.0, LENGTH / 2, 0.0) * ROT_OFFSET_MAT * avango.gua.make_scale_mat(DIAMETER, LENGTH, DIAMETER)
        self.arm_geometry.Material.value.set_uniform("Color", avango.gua.Vec4(0.0, 0.0, 125.0, 1.0))
        # self.arm_geometry.Material.value.set_uniform("Emissivity", 1.0) # no shading --> render color
        # self.arm_geometry.Material.value.EnableBackfaceCulling.value = False

        PARENT_NODE.Children.value.append(self.arm_geometry)

    def get_arm_node(self):
        return self.arm_geometry
