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
        TRANS_OFFSET = 0.0
        ):


        ### variables ###
        ## ToDo: evtl. init further variables


        ### parameters ###        
        self.rot_axis = ROT_AXIS
        self.rot_angle = 0.0
        
        self.rot_constraint = ROT_CONSTRAINT


        ### resources ###

        _loader = avango.gua.nodes.TriMeshLoader() # get trimesh loader to load external tri-meshes

        ## ToDo: init hinge node(s)
        # ...
        self.hinge_transform = avango.gua.nodes.TransformNode(Name = "hinge_transform")
        # self.hinge_transform.Transform.connect_from(self.input.sf_rot_value0)

        self.hinge_geometry = _loader.create_geometry_from_file("hinge_geometry", "data/objects/cylinder.obj", avango.gua.LoaderFlags.DEFAULTS)
        # self.hinge_geometry.Transform.value = avango.gua.make_trans_mat(0.0, TRANS_OFFSET, 0.0) * ROT_OFFSET_MAT * avango.gua.make_scale_mat(DIAMETER, HEIGHT, DIAMETER)
        self.hinge_geometry.Transform.value = ROT_OFFSET_MAT * avango.gua.make_scale_mat(DIAMETER, HEIGHT, DIAMETER)
        # print(avango.gua.make_trans_mat(0.0, TRANS_OFFSET / 2, 0.0), ROT_OFFSET_MAT, avango.gua.make_scale_mat(DIAMETER, HEIGHT, DIAMETER))
        self.hinge_geometry.Material.value.set_uniform("Color", avango.gua.Vec4(1.0, 0.0, 0.0, 1.0))
        # self.hinge_geometry.Material.value.EnableBackfaceCulling.value = False
        # self.hinge_geometry.Material.value.set_uniform("Emissivity", 1.0) # no shading --> render color
        self.hinge_transform.Transform.value = avango.gua.make_trans_mat(0.0, TRANS_OFFSET, 0.0)
        self.hinge_transform.Children.value.append(self.hinge_geometry)

        PARENT_NODE.Children.value.append(self.hinge_transform)
        # _node = PARENT_NODE.get_arm_node()
        # _node.Children.value.append(self.hinge_transform)


    def get_hinge_transform_node(self):
        return self.hinge_transform
        
    ### callback functions ###
    
    @field_has_changed(sf_rot_value)
    def sf_rot_value_changed(self):
        pass
        ## ToDo: accumulate input to hinge node && consider rotation contraints of this hinge
        if  self.rot_constraint[0] <= self.rot_angle + self.sf_rot_value.value <= self.rot_constraint[1]:
            self.rot_angle += self.sf_rot_value.value
            self.hinge_transform.Transform.value = self.hinge_transform.Transform.value * avango.gua.make_rot_mat(self.sf_rot_value.value, self.rot_axis)