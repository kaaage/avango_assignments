#!/usr/bin/python

### import guacamole libraries
import avango
import avango.gua
import avango.script
from avango.script import field_has_changed

### import python libraries


class SceneManager(avango.script.Script):

    ## input fields
    sf_button1 = avango.SFBool()
    sf_button2 = avango.SFBool()


    ## Default constructor.
    def __init__(self):
        self.super(SceneManager).__init__()
        
        ### resources ###
        self.keyboard_device_sensor = avango.daemon.nodes.DeviceSensor(DeviceService = avango.daemon.DeviceService())
        self.keyboard_device_sensor.Station.value = "gua-device-keyboard0"

        ## init field connections
        self.sf_button1.connect_from(self.keyboard_device_sensor.Button12) # key 1
        self.sf_button2.connect_from(self.keyboard_device_sensor.Button13) # key 2


    def my_constructor(self,
        PARENT_NODE = None,
        ):

        ## init scenes
        self.scene1 = Scene1(PARENT_NODE)        
        #self.scene2 = Scene2(PARENT_NODE)
        
        self.scene1.enable(True)



    ### callback functions ###
    @field_has_changed(sf_button1)
    def sf_button1_changed(self):
        if self.sf_button1.value == True: # button pressed
            self.scene1.enable(True)
            #self.scene2.enable(False)


    @field_has_changed(sf_button2)
    def sf_button2_changed(self):
        if self.sf_button2.value == True: # button pressed
            self.scene1.enable(False)
            #self.scene2.enable(True)


class Scene:

    ## constructor
    def __init__(self,
        NAME = "",
        PARENT_NODE = None,
        ):

        ### resources ###
        self.scene_root = avango.gua.nodes.TransformNode(Name = NAME)
        PARENT_NODE.Children.value.append(self.scene_root)        

        ### set initial states ###
        self.enable(False)
        
        
    ### functions ###
    def enable(self, BOOL):
        if BOOL == True:
            self.scene_root.Tags.value = [] # visible
        else:
            self.scene_root.Tags.value = ["invisible"] # invisible



class Scene1(Scene):

    ## constructor
    def __init__(self,
                PARENT_NODE = None,
                ):


        # call base class constructor
        Scene.__init__(self, NAME = "town", PARENT_NODE = PARENT_NODE)

        
        ## init scene geometries        
        _loader = avango.gua.nodes.TriMeshLoader() # get trimesh loader to load external meshes

        # water
        self.water_geometry = _loader.create_geometry_from_file("water_geometry", "data/objects/plane.obj", avango.gua.LoaderFlags.DEFAULTS | avango.gua.LoaderFlags.LOAD_MATERIALS)
        self.water_geometry.Transform.value = avango.gua.make_trans_mat(0.0,-0.35,0.0) * avango.gua.make_scale_mat(200.0)
        self.water_geometry.Material.value.set_uniform("Roughness", 0.4)
        self.scene_root.Children.value.append(self.water_geometry)

        # town
        self.town = _loader.create_geometry_from_file("town", "/opt/3d_models/architecture/medieval_harbour/town.obj", avango.gua.LoaderFlags.DEFAULTS | avango.gua.LoaderFlags.LOAD_MATERIALS | avango.gua.LoaderFlags.MAKE_PICKABLE)
        self.town.Transform.value = avango.gua.make_scale_mat(7.5)
        self.scene_root.Children.value.append(self.town)

        for _node in self.town.Children.value:
            _node.Material.value.EnableBackfaceCulling.value = False
            _node.Material.value.set_uniform("Emissivity", 0.25)
            _node.Material.value.set_uniform("Metalness", 0.1)
            _node.Material.value.set_uniform("Roughness", 0.8)


        ## init scene light
        self.scene_light = avango.gua.nodes.LightNode(Name = "scene_light", Type = avango.gua.LightType.SPOT)
        self.scene_light.Color.value = avango.gua.Color(1.0, 1.0, 0.8)
        self.scene_light.Brightness.value = 40.0
        self.scene_light.Softness.value = 0.5 # exponent
        self.scene_light.Falloff.value = 0.1 # exponent
        self.scene_light.EnableShadows.value = True
        self.scene_light.ShadowMapSize.value = 2048
        #self.scene_light.ShadowOffset.value = 0.01
        self.scene_light.ShadowMaxDistance.value = 150.0
        self.scene_light.ShadowNearClippingInSunDirection.value = 0.1
        self.scene_light.Transform.value = avango.gua.make_trans_mat(0.0, 120.0, 40.0) * \
            avango.gua.make_rot_mat(-70.0,1,0,0) * \
            avango.gua.make_scale_mat(170)
        self.scene_root.Children.value.append(self.scene_light)
        
                
