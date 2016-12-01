#!/usr/bin/python

### import guacamole libraries
import avango
import avango.gua
import avango.script
from avango.script import field_has_changed
import avango.daemon

### import python libraries
import math


class OrbitVisualization:

    ### constructor
    def __init__(self, PARENT_NODE = None , ORBIT_RADIUS = 1.0):

        if PARENT_NODE is None: # guard
            print("ERROR: missing parameters")            
            return

        ### parameters ###
        self.number_of_segments = 10
        self.thickness = 0.001  
        self.color = avango.gua.Color(1.0,1.0,1.0)
        
        ### resources ###
        
        ## init geometry
        _loader = avango.gua.nodes.TriMeshLoader() # init trimesh loader

        for _i in range(self.number_of_segments):
            _segment_angle  = 360.0 / self.number_of_segments
            _segment_length = (math.pi * 2.0 * ORBIT_RADIUS) / self.number_of_segments
     
            _geometry = _loader.create_geometry_from_file("orbit_segment_{0}".format(str(_i)), "data/objects/cube.obj", avango.gua.LoaderFlags.DEFAULTS)
            _geometry.Transform.value = \
                avango.gua.make_rot_mat(_i * _segment_angle, 0.0, 1.0, 0.0) * \
                avango.gua.make_trans_mat(ORBIT_RADIUS, 0.0, 0.0) * \
                avango.gua.make_scale_mat(self.thickness, self.thickness, _segment_length)
            _geometry.Material.value.set_uniform("Color", avango.gua.Vec4(self.color.r, self.color.g, self.color.b, 1.0))
            _geometry.Material.value.set_uniform("Emissivity", 0.5)
            _geometry.ShadowMode.value = avango.gua.ShadowMode.OFF # geometry does not cast shadows
    
            PARENT_NODE.Children.value.append(_geometry)
    


class SolarSystem(avango.script.Script):

    ### fields ###

    ## input fields
    sf_key0 = avango.SFFloat()
    sf_key1 = avango.SFFloat()
  
    ## output_fields
    sf_time_scale_factor = avango.SFFloat()
    sf_time_scale_factor.value = 1.0


    ### constructor
    def __init__(self):
        self.super(SolarSystem).__init__() # call base-class constructor
        
        
        ### resources ###

        ## init device sensors
        self.keyboard_sensor = avango.daemon.nodes.DeviceSensor(DeviceService = avango.daemon.DeviceService())
        self.keyboard_sensor.Station.value = "gua-device-keyboard0"

        self.sf_key0.connect_from(self.keyboard_sensor.Button12)
        self.sf_key1.connect_from(self.keyboard_sensor.Button13)


    def my_constructor(self, PARENT_NODE):

        ### init further resources ###

        ## init Sun
        self.sun = SolarObject(
            NAME = "sun",
            TEXTURE_PATH = "data/textures/planets/Sun.jpg",
            PARENT_NODE = PARENT_NODE,
            SF_TIME_SCALE = self.sf_time_scale_factor,
            DIAMETER = 1392000.0 * 0.05, # downscale sun geometry relative to planet sizes
            ORBIT_RADIUS = 0.0, # in km
            ORBIT_INCLINATION = 0.0, # in degrees
            ORBIT_DURATION = 0.0, # in days
            ROTATION_INCLINATION = 7.0, # in degrees
            ROTATION_DURATION = 0.0, # in days
            )
                                                                            
        # init lightsource (only for sun)
        self.sun_light = avango.gua.nodes.LightNode(Name = "sun_light", Type = avango.gua.LightType.POINT)
        self.sun_light.Color.value = avango.gua.Color(1.0, 1.0, 1.0)
        self.sun_light.Brightness.value = 25.0
        self.sun_light.Falloff.value = 0.2
        self.sun_light.EnableShadows.value = True
        self.sun_light.ShadowMapSize.value = 2048
        #self.sun_light.ShadowOffset.value = 0.01
        #self.sun_light.EnableGodrays.value = True
        self.sun_light.Transform.value = avango.gua.make_scale_mat(50.0) # light volume defined by scale
        self.sun_light.ShadowNearClippingInSunDirection.value = 0.1 / 50.0


        _node = self.sun.get_orbit_node()
        _node.Children.value.append(self.sun_light)

        ## init Mercury
        self.mercury = SolarObject(
            NAME = "mercury",
            TEXTURE_PATH = "data/textures/planets/mercury_rgb_cyl_www.jpg",
            PARENT_NODE = PARENT_NODE,
            SF_TIME_SCALE = self.sf_time_scale_factor,
            DIAMETER = 4878, # downscale sun geometry relative to planet sizes
            ORBIT_RADIUS = 58000000, # in km
            ORBIT_INCLINATION = 7, # in degrees
            ORBIT_DURATION = 87, # in days
            ROTATION_INCLINATION = 0.0, # in degrees
            ROTATION_DURATION = 58, # in days
            )
        ## init Venus                             
        self.venus = SolarObject(
            NAME = "venus",
            TEXTURE_PATH = "data/textures/planets/venus4_rgb_cyl_www.jpg",
            PARENT_NODE = PARENT_NODE,
            SF_TIME_SCALE = self.sf_time_scale_factor,
            DIAMETER = 12104, # downscale sun geometry relative to planet sizes
            ORBIT_RADIUS = 108000000, # in km
            ORBIT_INCLINATION = 4, # in degrees
            ORBIT_DURATION = 20, # in days
            ROTATION_INCLINATION = 3, # in degrees
            ROTATION_DURATION = 243, # in days
            )
        ## init Earth
        self.earth = SolarObject(
            NAME = "earth",
            TEXTURE_PATH = "data/textures/planets/Earth.jpg",
            PARENT_NODE = PARENT_NODE,
            SF_TIME_SCALE = self.sf_time_scale_factor,
            DIAMETER = 6371, # downscale sun geometry relative to planet sizes
            ORBIT_RADIUS = 149000000, # in km
            ORBIT_INCLINATION = 0, # in degrees
            ORBIT_DURATION = 365, # in days
            ROTATION_INCLINATION = 24, # in degrees
            ROTATION_DURATION = 1, # in days
            )
        ## init Earth-Moon
        self.earthmoon = SolarObject(
            NAME = "earthmoon",
            TEXTURE_PATH = "data/textures/planets/Moon.jpg",
            PARENT_NODE = self.earth.get_orbit_node(),
            SF_TIME_SCALE = self.sf_time_scale_factor,
            DIAMETER = 3476, # downscale sun geometry relative to planet sizes
            ORBIT_RADIUS = 8500000, # in km
            ORBIT_INCLINATION = 7, # in degrees
            ORBIT_DURATION = 10, # in days
            ROTATION_INCLINATION = 0.0, # in degrees
            ROTATION_DURATION = 58, # in days
            )
        ## init Mars
        # self.mars = SolarObject(
        #     NAME = "mars",
        #     TEXTURE_PATH = "data/textures/planets/Mars.jpg",
        #     PARENT_NODE = PARENT_NODE,
        #     SF_TIME_SCALE = self.sf_time_scale_factor,
        #     DIAMETER = 12756, # downscale sun geometry relative to planet sizes
        #     ORBIT_RADIUS = 199000000, # in km
        #     ORBIT_INCLINATION = 0, # in degrees
        #     ORBIT_DURATION = 365, # in days
        #     ROTATION_INCLINATION = 24, # in degrees
        #     ROTATION_DURATION = 1, # in days
        #     )
        # ## init Jupiter
        # self.jupiter = SolarObject(
        #     NAME = "jupiter",
        #     TEXTURE_PATH = "data/textures/planets/jupiter_rgb_cyl_www.jpg",
        #     PARENT_NODE = PARENT_NODE,
        #     SF_TIME_SCALE = self.sf_time_scale_factor,
        #     DIAMETER = 69911, # downscale sun geometry relative to planet sizes
        #     ORBIT_RADIUS = 239000000, # in km
        #     ORBIT_INCLINATION = 20, # in degrees
        #     ORBIT_DURATION = 4, # in days
        #     ROTATION_INCLINATION = 40, # in degrees
        #     ROTATION_DURATION = 5, # in days
        #     )
        # ## init Jupiter-Moons
        # self.jupitermoon = SolarObject(
        #     NAME = "jupitermoon",
        #     TEXTURE_PATH = "data/textures/planets/ganymede.jpg",
        #     PARENT_NODE = self.jupiter.get_orbit_node(),
        #     SF_TIME_SCALE = self.sf_time_scale_factor,
        #     DIAMETER = 3476, # downscale sun geometry relative to planet sizes
        #     ORBIT_RADIUS = 58000000, # in km
        #     ORBIT_INCLINATION = 7, # in degrees
        #     ORBIT_DURATION = 87, # in days
        #     ROTATION_INCLINATION = 0.0, # in degrees
        #     ROTATION_DURATION = 58, # in days
        #     )
        ## init ...


    ### callback functions ###

    ## Evaluated when value changes.
    @field_has_changed(sf_key0)
    def sf_key0_changed(self):
        if self.sf_key0.value == True: # button pressed
            _new_factor = self.sf_time_scale_factor.value * 1.5 # increase factor about 50% 

            self.set_time_scale_factor(_new_factor)
      

    ## Evaluated when value changes.
    @field_has_changed(sf_key1)
    def sf_key1_changed(self): 
        if self.sf_key1.value == True: # button pressed
            _new_factor = self.sf_time_scale_factor.value * 0.5 # decrease factor about 50% 

            self.set_time_scale_factor(_new_factor)
      


    ### functions ###
    def set_time_scale_factor(self, FLOAT): 
        self.sf_time_scale_factor.value = min(10000.0, max(1.0, FLOAT)) # clamp value to reasonable intervall



class SolarObject:

    ### constructor ###
    def __init__(self,
        NAME = "",
        TEXTURE_PATH = "",
        PARENT_NODE = None,
        SF_TIME_SCALE = None,
        DIAMETER = 1.0,
        ORBIT_RADIUS = 1.0,
        ORBIT_INCLINATION = 0.0, # in degrees
        ORBIT_DURATION = 0.0,
        ROTATION_INCLINATION = 0.0, # in degrees
        ROTATION_DURATION = 0.0,
        ):

        if PARENT_NODE is None: # guard
            print("ERROR: missing parameters")            
            return


        ### parameters ###
        self.sf_time_scale_factor = SF_TIME_SCALE        

        self.diameter = DIAMETER * 0.000001
        self.orbit_radius = ORBIT_RADIUS * 0.000000002

        if ORBIT_DURATION > 0.0:
          self.orbit_velocity = 1.0 / ORBIT_DURATION
        else:
          self.orbit_velocity = 0.0

        if ROTATION_DURATION > 0.0:
            self.rotation_velocity = 1.0 / ROTATION_DURATION # get velocity
        else:
            self.rotation_velocity = 0.0

        self.rotation_inclination = ROTATION_INCLINATION


        ### resources ###

        # init geometries of solar object
        _loader = avango.gua.nodes.TriMeshLoader() # init trimesh loader to load external meshes

        self.object_geometry = _loader.create_geometry_from_file(NAME + "_geometry", "data/objects/sphere.obj", avango.gua.LoaderFlags.DEFAULTS)
        self.object_geometry.Transform.value = avango.gua.make_scale_mat(self.diameter)
        self.object_geometry.Material.value.set_uniform("ColorMap", TEXTURE_PATH)
        self.object_geometry.Material.value.set_uniform("Roughness", 0.2)
        #self.object_geometry.Material.value.set_uniform("Emissivity", 0.2)
        self.object_geometry.Material.value.EnableBackfaceCulling.value = False

        self.axis1_geometry = _loader.create_geometry_from_file("axis1", "data/objects/cylinder.obj", avango.gua.LoaderFlags.DEFAULTS)
        self.axis1_geometry.Transform.value = avango.gua.make_scale_mat(0.001,self.diameter*2.5,0.001)
        self.axis1_geometry.Material.value.set_uniform("Color", avango.gua.Vec4(1.0, 0.0, 0.0, 1.0))
        self.axis1_geometry.Material.value.set_uniform("Emissivity", 1.0) # no shading --> render color
        self.axis1_geometry.ShadowMode.value = avango.gua.ShadowMode.OFF # geometry does not cast shadows

        self.axis2_geometry = _loader.create_geometry_from_file("axis2", "data/objects/cylinder.obj", avango.gua.LoaderFlags.DEFAULTS)
        self.axis2_geometry.Transform.value = avango.gua.make_scale_mat(0.001,self.diameter*2.5,0.001)
        self.axis2_geometry.Material.value.set_uniform("Color", avango.gua.Vec4(0.0, 1.0, 0.0, 1.0))
        self.axis2_geometry.Material.value.set_uniform("Emissivity", 1.0) # no shading --> render color
        self.axis2_geometry.ShadowMode.value = avango.gua.ShadowMode.OFF # geometry does not cast shadows

           
        ## init transformation nodes for specific solar object aspects        
        self.orbit_radius_node = avango.gua.nodes.TransformNode(Name = NAME + "_orbit_radius_node")
        self.orbit_radius_node.Children.value = [self.orbit_inclination_node, self.axis1_geometry]       #What is this line doing? 
        self.orbit_radius_node.Transform.value = avango.gua.make_trans_mat(self.orbit_radius, 0.0, 0.0)
        PARENT_NODE.Children.value.append(self.orbit_radius_node)
        
        
        # evtl. init further transformation nodes here ...
        self.orbit_inclination_node = avango.gua.nodes.TransformNode(Name = NAME + '_orbit_inclination_node')
        self.orbit_inclination_node.Children.value = [self.object_geometry]
        self.orbit_inclination_node.Transform.value = avango.gua.make_rot_mat(ORBIT_INCLINATION, 0, 1, 0)
        #self.orbit_radius_node.Children.value.append(self.orbit_inclination_node)

        

        #self.rotation_inclination_node = avango.gua.nodes.TransformNode(Name = NAME + '_rotation_inclination_node')

        ## sub classes
        # init orbit visualization here ...
        self.orbit_visualization = OrbitVisualization(PARENT_NODE, self.orbit_radius)

        # Triggers framewise evaluation of respective callback method
        self.frame_trigger = avango.script.nodes.Update(Callback = self.frame_callback, Active = True)


    ### functions ###
    def get_orbit_node(self):
        return self.orbit_radius_node


    def update_orbit(self):
        self.orbit_radius_node.Transform.value = \
            avango.gua.make_rot_mat(self.orbit_velocity * self.sf_time_scale_factor.value, 0.0, 1.0, 0.0) * \
            self.orbit_radius_node.Transform.value


    def update_rotation(self):
        pass
        ## implement self-rotation behavior of a planet here ...    


    ### callback functions ###
    def frame_callback(self): # evaluated once per frame
        self.update_orbit()
        self.update_rotation()


