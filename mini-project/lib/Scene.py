#!/usr/bin/python

### import guacamole libraries
import avango
import avango.gua
import avango.script
from avango.script import field_has_changed
#import math


### import application libraries
from lib.LeapSensor import LeapSensor

class SceneScript(avango.script.Script):

    #Physics = avango.gua.SFPhysics()

    ## input fields
    sf_reset_button = avango.SFBool()

    ## Default constructor.
    def __init__(self):
        self.super(SceneScript).__init__()

        ### external references ###
        self.CLASS = None # is set later
        

        ### resources ###
        self.keyboard_device_sensor = avango.daemon.nodes.DeviceSensor(DeviceService = avango.daemon.DeviceService())
        self.keyboard_device_sensor.Station.value = "gua-device-keyboard0"

        self.sf_reset_button.connect_from(self.keyboard_device_sensor.Button14) # spacebar key


    def my_constructor(self, CLASS):
        self.CLASS = CLASS
        self.always_evaluate(True) # change global evaluation policy


    ### callbacks ###  
    @field_has_changed(sf_reset_button)
    def sf_reset_button_changed(self):
        if self.sf_reset_button.value == True and self.CLASS is not None: # button pressed
            self.CLASS.reset()
            


class Scene:

    ## constructor
    def __init__(self,
        PARENT_NODE = None,
        ):

        Physics = avango.gua.SFPhysics()
        physics = avango.gua.nodes.Physics()

        ### external reference ###
        self.PARENT_NODE = PARENT_NODE

        ### resources ###                
        self.script = SceneScript()
        self.script.my_constructor(self)


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
        self.base_node.Transform.value = avango.gua.make_trans_mat(-2.1, 0.96, 0.705) * avango.gua.make_rot_mat(90.0, 0, 1, 0) * avango.gua.make_rot_mat(90.0, -1, 0, 0)
        PARENT_NODE.Children.value.append(self.base_node)

        floor = self.create_floor(_loader)
        self.base_node.Children.value.append(floor)
        physics.add_rigid_body(floor)

        Physics.value = physics

        body = avango.gua.nodes.RigidBodyNode(
            Name="body",
            Mass=2.0,
            Friction=0.6,
            RollingFriction=0.03,
            Restitution=0.3,
            Transform=avango.gua.make_trans_mat(0,0,1)
            #Transform=avango.gua.make_trans_mat(math.sin(3 * current_time), 7.0, math.cos(3 * current_time))
            )

        cube_geometry = _loader.create_geometry_from_file("cube", "data/objects/cube.obj", avango.gua.LoaderFlags.DEFAULTS)

        cube_geometry.Transform.value = avango.gua.make_scale_mat(
            0.2, 0.2, 0.2)
        
        cube_geometry.Material.value.set_uniform(
            "Color",
            avango.gua.Vec4(0.9, 0.266, 0.136, 1.0))
        cube_geometry.Material.value.set_uniform("Roughness", 0.75)
        cube_geometry.Material.value.set_uniform("Metalness", 0.0)

        collision_shape_node = avango.gua.nodes.CollisionShapeNode(
            Name="collision_shape_node",
            ShapeName="cube")

        collision_shape_node.Children.value.append(cube_geometry)
        body.Children.value.append(collision_shape_node)
        self.base_node.Children.value.append(body)
        Physics.value.add_rigid_body(body)

        leap = LeapSensor()
        leap.my_constructor(SCENEGRAPH = PARENT_NODE, BASENODE = self.base_node)

        # viewer = avango.gua.nodes.Viewer()
        # viewer.Physics.value = physics
        # viewer.SceneGraphs.value = [graph]
        # viewer.Windows.value = [window]    

        # self.cube_node.Transform.connect_from(leap.sf_mat)


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
    def evaluate(self):
        current_time = self.TimeIn.value


    def reset(self):
        print("reset")
        for _node in self.PARENT_NODE.Children.value:
            if _node.has_field("HomeMatrix") == True:
                _node.Transform.value = _node.HomeMatrix.value
                

    def create_floor(self, loader):
        floor_geometry = loader.create_geometry_from_file(
            "floor_geometry", "data/objects/plane.obj",
            avango.gua.LoaderFlags.NORMALIZE_SCALE | avango.gua.LoaderFlags.NORMALIZE_POSITION)

        floor_geometry.Transform.value = avango.gua.make_trans_mat(0, 0, -0.5) * avango.gua.make_scale_mat(1.0, 1.0, 1.0) * avango.gua.make_rot_mat(90,1,0,0)
        floor_geometry.Material.value.set_uniform("Metalness", 0.0)
        floor_geometry.Material.value.set_uniform(
            "RoughnessMap", "data/textures/oakfloor2_roughness.png")
        floor_geometry.Material.value.set_uniform(
            "ColorMap", "data/textures/oakfloor2_basecolor.png")
        floor_geometry.Material.value.set_uniform(
            "NormalMap", "data/textures/oakfloor2_normal.png")

        avango.gua.create_box_shape("box", avango.gua.Vec3(10, 10, 1))
        floor_collision_shape = avango.gua.nodes.CollisionShapeNode(
            Name="floor_shape",
            ShapeName="box",
            Children=[floor_geometry])
        floor_body = avango.gua.nodes.RigidBodyNode(Name="floor_body",
                                            Mass=0,
                                            Friction=0.5,
                                            Restitution=0.7,
                                            Children=[floor_collision_shape])
        return floor_body

        