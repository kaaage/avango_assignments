#!/usr/bin/python

### import guacamole libraries
import avango
import avango.gua
import avango.script
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

        ## init scene light
        self.scene_light = avango.gua.nodes.LightNode(Name = "scene_light")
        self.scene_light.Type.value = avango.gua.LightType.SPOT
        self.scene_light.Color.value = avango.gua.Color(1.0,1.0,0.8)
        self.scene_light.Brightness.value = 20.0
        self.scene_light.Falloff.value = 0.1 # exponent
        self.scene_light.EnableShadows.value = True
        self.scene_light.ShadowMapSize.value = 2048
        self.scene_light.ShadowOffset.value = 0.001
        self.scene_light.ShadowNearClippingInSunDirection.value = 0.1 * (1.0/4.0)
        self.scene_light.ShadowMaxDistance.value = 10.0 # maximal distance, the shadow is visible
        self.scene_light.ShadowNearClippingInSunDirection.value = 0.05
        self.scene_light.Transform.value = avango.gua.make_trans_mat(0.0,1.2,0.5) * \
            avango.gua.make_rot_mat(80.0,-1,0,0) * \
            avango.gua.make_scale_mat(3.0)
        PARENT_NODE.Children.value.append(self.scene_light)

        ## init scene geometries
        _loader = avango.gua.nodes.TriMeshLoader() # get trimesh loader to load external meshes

        self.base_node = avango.gua.nodes.TransformNode(Name="base_node")
        # self.base_node.Transform.value = avango.gua.make_trans_mat(-2.1, 0.96, 0.705) * avango.gua.make_rot_mat(90.0, 0, 1, 0) * \
        #     avango.gua.make_rot_mat(90.0, 1, 0, 0) * avango.gua.make_rot_mat(90.0, -1, 0, 0)
        self.base_node.Transform.value = avango.gua.make_trans_mat(-2.1, 0.96, 0.705) * avango.gua.make_rot_mat(90.0, 0, 1, 0)
        PARENT_NODE.Children.value.append(self.base_node)

        self.cube_list = []

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