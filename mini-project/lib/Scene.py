#!/usr/bin/python

### import guacamole libraries
import avango
import avango.gua
import avango.script
import random

from avango.script import field_has_changed

### import application libraries
from lib.LeapSensor import LeapSensor

class Scene:
    ## constructor
    def __init__(self,
        SCENEGRAPH = None,
        PARENT_NODE = None,
        ):

        ### external reference ###
        self.PARENT_NODE = PARENT_NODE
        self.SCENEGRAPH = SCENEGRAPH

        ### resources ###                
        self.cube_list = []
        self.target_list = []

       

        ## init scene geometries
        _loader = avango.gua.nodes.TriMeshLoader() # get trimesh loader to load external meshes

        ## init base node (this is the leap coordinate center)
        self.base_node = avango.gua.nodes.TransformNode(Name="base_node")
        # self.base_node.Transform.value = avango.gua.make_trans_mat(-2.1, 0.96, 0.705) * avango.gua.make_rot_mat(90.0, 0, 1, 0) * \
        #     avango.gua.make_rot_mat(90.0, 1, 0, 0) * avango.gua.make_rot_mat(90.0, -1, 0, 0)
        self.base_node.Transform.value = avango.gua.make_trans_mat(-2.1, 0.96, 0.705) * avango.gua.make_rot_mat(90.0, 0, 1, 0)
        
        PARENT_NODE.Children.value.append(self.base_node)


        ## init scene light
        self.scene_light = avango.gua.nodes.LightNode(Name = "scene_light")
        self.scene_light.Type.value = avango.gua.LightType.SPOT
        self.scene_light.Color.value = avango.gua.Color(1.0,1.0,0.8)
        self.scene_light.Brightness.value = 20.0
        self.scene_light.Falloff.value = 0.01 # exponent
        self.scene_light.EnableShadows.value = True
        self.scene_light.ShadowMapSize.value = 2048
        self.scene_light.ShadowOffset.value = 0.001
        self.scene_light.ShadowNearClippingInSunDirection.value = 0.1 * (1.0/4.0)
        self.scene_light.ShadowMaxDistance.value = 10.0 # maximal distance, the shadow is visible
        self.scene_light.ShadowNearClippingInSunDirection.value = 0.05
        self.scene_light.Transform.value = avango.gua.make_trans_mat(0.0,1.0,0.0) * \
            avango.gua.make_rot_mat(90.0,-1,0,0) * \
            avango.gua.make_scale_mat(2.0)
        self.base_node.Children.value.append(self.scene_light)


        # init ground plane
        self.ground_geometry = _loader.create_geometry_from_file("ground", "data/objects/plane.obj", avango.gua.LoaderFlags.DEFAULTS)
        self.ground_geometry.Transform.value = avango.gua.make_trans_mat(0.0, -0.4, 0.0) * avango.gua.make_rot_mat(90.0, 0, 1, 0) *  avango.gua.make_scale_mat(2.0)
        #self.ground_geometry.Material.value.set_uniform("Color", avango.gua.Vec4(0.0, 0.5, 0.0, 1.0))
        self.ground_geometry.Material.value.set_uniform("ColorMap", "data/textures/ground/bunker_albedo.tif")
        self.ground_geometry.Material.value.set_uniform("NormalMap", "data/textures/ground/bunker_normal.tif")
        self.base_node.Children.value.append(self.ground_geometry)

        # init side planes
        self.back_geometry = _loader.create_geometry_from_file("ground", "data/objects/plane.obj", avango.gua.LoaderFlags.DEFAULTS)
        self.back_geometry.Transform.value = avango.gua.make_trans_mat(0.0, 0.0, -0.425) * avango.gua.make_rot_mat(90.0, 1, 0, 0) *  avango.gua.make_scale_mat(2.0)
        self.back_geometry.Material.value.set_uniform("ColorMap", "data/textures/ground/bunkerdirty_albedo.tif")
        self.back_geometry.Material.value.set_uniform("NormalMap", "data/textures/ground/bunkerdirty_normal.tif")
        self.base_node.Children.value.append(self.back_geometry)
        
        self.left_geometry = _loader.create_geometry_from_file("ground", "data/objects/plane.obj", avango.gua.LoaderFlags.DEFAULTS)
        self.left_geometry.Transform.value = avango.gua.make_trans_mat(-0.555, 0.0, 0.0) * avango.gua.make_rot_mat(-90.0, 0, 0, 1)* avango.gua.make_rot_mat(90.0, 0, 1, 0)  *  avango.gua.make_scale_mat(2.0)
        self.left_geometry.Material.value.set_uniform("ColorMap", "data/textures/ground/bunkerdirty_albedo.tif")
        self.left_geometry.Material.value.set_uniform("NormalMap", "data/textures/ground/bunkerdirty_normal.tif")
        self.base_node.Children.value.append(self.left_geometry)

        self.right_geometry = _loader.create_geometry_from_file("ground", "data/objects/plane.obj", avango.gua.LoaderFlags.DEFAULTS)
        self.right_geometry.Transform.value = avango.gua.make_trans_mat(0.555, 0.0, 0.0) * avango.gua.make_rot_mat(90.0, 0, 0, 1)* avango.gua.make_rot_mat(90.0, 0, 1, 0)  *  avango.gua.make_scale_mat(2.0)
        self.right_geometry.Material.value.set_uniform("ColorMap", "data/textures/ground/bunkerdirty_albedo.tif")
        self.right_geometry.Material.value.set_uniform("NormalMap", "data/textures/ground/bunkerdirty_normal.tif")
        self.base_node.Children.value.append(self.right_geometry)

        self.front_geometry = _loader.create_geometry_from_file("ground", "data/objects/plane.obj", avango.gua.LoaderFlags.DEFAULTS)
        self.front_geometry.Transform.value = avango.gua.make_trans_mat(0.0, 0.0, 0.425)  * avango.gua.make_rot_mat(-90, 1, 0, 0) *  avango.gua.make_scale_mat(2.0)
        self.front_geometry.Material.value.set_uniform("ColorMap", "data/textures/ground/bunkerdirty_albedo.tif")
        self.front_geometry.Material.value.set_uniform("NormalMap", "data/textures/ground/bunkerdirty_normal.tif")
        self.base_node.Children.value.append(self.front_geometry)


        # init manipulation geometries
        _number = 15

        for _i in range(_number):
            _x_range = 570 # in mm
            _y_range = 400 # in mm
            _z_range = 425 

            _rand_pos_x = random.randrange(-_x_range, _x_range) * 0.001
            _rand_pos_y = random.randrange(-_y_range, _y_range) * 0.001
            _rand_pos_z = random.randrange(-_z_range, _z_range) * 0.001

            _rand_angle = random.randrange(-180,180)
            _rand_axis_x = random.randrange(0,100) * 0.01
            _rand_axis_y = random.randrange(0,100) * 0.01
            _rand_axis_z = random.randrange(0,100) * 0.01
               
            _geometry = _loader.create_geometry_from_file("cube" + str(_i), "data/objects/cube.obj", avango.gua.LoaderFlags.DEFAULTS)
            _geometry.Material.value.set_uniform("ColorMap", "data/textures/box1/Mossy_A_albedo.tif")
            _geometry.Material.value.set_uniform("NormalMap", "data/textures/box1/Mossy_A_normal.tif")

            _geometry.Transform.value = \
                avango.gua.make_trans_mat(_rand_pos_x, -0.4, _rand_pos_z) * \
                avango.gua.make_rot_mat(_rand_angle,_rand_axis_x,-0.4,_rand_axis_z) * \
                avango.gua.make_scale_mat(0.1)

            _geometry.add_field(avango.gua.SFMatrix4(), "DraggingOffsetMatrix")
            #_geometry.add_field(avango.gua.SFVec4(), "CurrentColor")
            #_geometry.CurrentColor.value = avango.gua.Vec4(1.0, 1.0, 1.0, 1.0)
            #_geometry.Material.value.set_uniform("Color", _geometry.CurrentColor.value)
            self.base_node.Children.value.append(_geometry)

            self.target_list.append(_geometry) # append the cubes to target list

        # self.cube_node_static = avango.gua.nodes.TransformNode(Name="cube_node_static")
        # self.cube_node_static.Transform.value = avango.gua.make_trans_mat(0.0, 0.0, 0.0) * avango.gua.make_scale_mat(0.05,0.05,0.05)
        # self.cube_static = _loader.create_geometry_from_file("cube", "data/objects/cube.obj", avango.gua.LoaderFlags.DEFAULTS)
        # self.cube.Material.value.set_uniform("Color", avango.gua.Vec4(1.0, 0.0, 0.0, 1.0))
        # self.cube_node_static.Children.value.append(self.cube_static)
        # self.base_node.Children.value.append(self.cube_node_static)

        # self.cube_node = avango.gua.nodes.TransformNode(Name="cube_node")
        # self.cube_node.Transform.value = avango.gua.make_trans_mat(0.0, 0.1, 0.0)

        # self.cube_geometry = _loader.create_geometry_from_file("cube_geometry", "data/objects/cube.obj", avango.gua.LoaderFlags.DEFAULTS | avango.gua.LoaderFlags.MAKE_PICKABLE)
        # self.cube_geometry.Material.value.set_uniform("Color", avango.gua.Vec4(1.0, 0.0, 0.0, 1.0))
        # self.cube_geometry.Transform.value = avango.gua.make_trans_mat(0.0, 0.0, 0.0) * avango.gua.make_scale_mat(0.05,0.05,0.05)
        # self.cube_node.Children.value.append(self.cube_geometry)

        # self.cube_list.append(self.cube_geometry)

        # self.base_node.Children.value.append(self.cube_node)

        # self.cube1_node = avango.gua.nodes.TransformNode(Name="cube1_node")
        # self.cube1_node.Transform.value = avango.gua.make_trans_mat(0.0, 0.5, 0.0) * avango.gua.make_scale_mat(0.01,0.01,0.01)
        # self.cube1_geometry = _loader.create_geometry_from_file("cube1_geometry", "data/objects/cube.obj", avango.gua.LoaderFlags.DEFAULTS)
        # self.cube1_geometry.Material.value.set_uniform("Color", avango.gua.Vec4(1.0, 0.0, 0.0, 1.0))

        #self.cube2_node = avango.gua.nodes.TransformNode(Name="cube2_node")
        #self.cube2_node.Transform.value = avango.gua.make_trans_mat(0.0, 0.5, 0.0) * avango.gua.make_scale_mat(0.01,0.01,0.01)
        #self.cube2_geometry = _loader.create_geometry_from_file("cube2_geometry", "data/objects/cube.obj", avango.gua.LoaderFlags.DEFAULTS)
        #self.cube2_geometry.Material.value.set_uniform("Color", avango.gua.Vec4(1.0, 0.0, 0.0, 1.0))


        # self.cube1_node.Transform.connect_from(leap.handright_index_pos)
        #self.cube2_node.Transform.connect_from(leap.handright_thumb_pos)


        # # ground_table table
        # self.ground_table = _loader.create_geometry_from_file("ground_table", "data/objects/cube.obj", avango.gua.LoaderFlags.DEFAULTS | avango.gua.LoaderFlags.LOAD_MATERIALS)
        # self.ground_table.Transform.value = avango.gua.make_trans_mat(0.0,0.1,0.0) * \
        #     avango.gua.make_scale_mat(1.0, 0.05, 0.7)
        # self.ground_table.Material.value.set_uniform("Color", avango.gua.Vec4(211,211,211,1.0))
        # # self.ground_table.Material.value.set_uniform("Emissivity", 0.5)
        # # self.ground_table.Material.value.set_uniform("Metalness", 0.1)
        # # self.ground_table.add_and_init_field(avango.gua.SFMatrix4(), "HomeMatrix", self.ground_table.Transform.value)
        # self.base_node.Children.value.append(self.ground_table)

    ### functions ###
    def reset(self):
        print("reset")
        for _node in self.PARENT_NODE.Children.value:
            if _node.has_field("HomeMatrix") == True:
                _node.Transform.value = _node.HomeMatrix.value