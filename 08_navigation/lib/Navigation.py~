#!/usr/bin/python

### import guacamole libraries
import avango
import avango.gua
import avango.script
from avango.script import field_has_changed


# import application libraries
from lib.Device import NewSpacemouseInput

### import python libraries
import math
import time


class NavigationManager(avango.script.Script):

    ## input fields
    sf_key_1 = avango.SFBool()
    sf_key_2 = avango.SFBool()
    sf_key_3 = avango.SFBool()


    ## output fields
    sf_nav_mat = avango.gua.SFMatrix4()
    sf_nav_mat.value = avango.gua.make_identity_mat()


    ## constructor
    def __init__(self):
        self.super(NavigationManager).__init__()    
    
    
    def my_constructor(self,
        SCENEGRAPH = None,
        NAVIGATION_NODE = None,
        POINTER_TRACKING_STATION = "",
        TRACKING_TRANSMITTER_OFFSET = avango.gua.make_identity_mat(),
        POINTER_DEVICE_STATION = "",
        ):


        ### external references ###
        self.SCENEGRAPH = SCENEGRAPH
        
        ### parameters ###
        self.ray_length = 15.0 # in meter
        self.ray_thickness = 0.015 # in meter
        self.intersection_point_size = 0.02 # in meter


        ### variables ###
        self.active_navigation_technique = None

        ## picking stuff
        self.pick_result = None
        
        self.white_list = []   
        self.black_list = ["invisible"]

        self.pick_options = avango.gua.PickingOptions.PICK_ONLY_FIRST_OBJECT \
                            | avango.gua.PickingOptions.GET_POSITIONS \
                            | avango.gua.PickingOptions.GET_NORMALS \
                            | avango.gua.PickingOptions.GET_WORLD_POSITIONS \
                            | avango.gua.PickingOptions.GET_WORLD_NORMALS


        ### resources ###

        ## init sensors
        self.keyboard_sensor = avango.daemon.nodes.DeviceSensor(DeviceService = avango.daemon.DeviceService())
        self.keyboard_sensor.Station.value = "gua-device-keyboard0"

        self.sf_key_1.connect_from(self.keyboard_sensor.Button16) # key 1
        self.sf_key_2.connect_from(self.keyboard_sensor.Button17) # key 2
        self.sf_key_3.connect_from(self.keyboard_sensor.Button18) # key 3


        self.pointer_tracking_sensor = avango.daemon.nodes.DeviceSensor(DeviceService = avango.daemon.DeviceService())
        self.pointer_tracking_sensor.Station.value = POINTER_TRACKING_STATION
        self.pointer_tracking_sensor.TransmitterOffset.value = TRACKING_TRANSMITTER_OFFSET
            
        self.pointer_device_sensor = avango.daemon.nodes.DeviceSensor(DeviceService = avango.daemon.DeviceService())
        self.pointer_device_sensor.Station.value = POINTER_DEVICE_STATION


        self.spacemouseInput = NewSpacemouseInput()
        self.spacemouseInput.my_constructor("gua-device-spacemouse")


        ## init nodes
        self.pointer_node = avango.gua.nodes.TransformNode(Name = "pointer_node")
        self.pointer_node.Transform.connect_from(self.pointer_tracking_sensor.Matrix)
        NAVIGATION_NODE.Children.value.append(self.pointer_node)

        _loader = avango.gua.nodes.TriMeshLoader()

        self.ray_geometry = _loader.create_geometry_from_file("ray_geometry", "data/objects/cylinder.obj", avango.gua.LoaderFlags.DEFAULTS)
        self.ray_geometry.Material.value.set_uniform("Color", avango.gua.Vec4(1.0,0.0,0.0,1.0))
        self.ray_geometry.Tags.value = ["invisible"]
        self.pointer_node.Children.value.append(self.ray_geometry)

        self.intersection_geometry = _loader.create_geometry_from_file("intersection_geometry", "data/objects/sphere.obj", avango.gua.LoaderFlags.DEFAULTS)
        self.intersection_geometry.Material.value.set_uniform("Color", avango.gua.Vec4(1.0,0.0,0.0,1.0))
        self.intersection_geometry.Tags.value = ["invisible"]
        SCENEGRAPH.Root.value.Children.value.append(self.intersection_geometry)

        
        ## init manipulation techniques
        self.steeringNavigation = SteeringNavigation()
        self.steeringNavigation.my_constructor(self, self.spacemouseInput.mf_dof)
      
        self.cameraInHandNavigation = CameraInHandNavigation()
        self.cameraInHandNavigation.my_constructor(self)

        self.navidgetNavigation = NavidgetNavigation()
        self.navidgetNavigation.my_constructor(self, SCENEGRAPH)


        self.ray = avango.gua.nodes.Ray() # required for trimesh intersection

    
        NAVIGATION_NODE.Transform.connect_from(self.sf_nav_mat)       
    
    
        ### set initial states ###
        self.set_navigation_technique(0)
        self.set_navigation_matrix(avango.gua.make_trans_mat(0.0,1.2,0.0))



    ### functions ###
    def set_navigation_technique(self, INT):
        # possibly disable prior technique
        if self.active_navigation_technique is not None:
            self.active_navigation_technique.enable(False)
    
        # enable new technique
        if INT == 0: # Steering Navigation
            self.active_navigation_technique = self.steeringNavigation
            print("Switch to Steering Navigation")

        elif INT == 1: # Camera-in-Hand Navigation
            self.active_navigation_technique = self.cameraInHandNavigation
            print("Switch to Camera-In-Hand Navigation")

        elif INT == 2: # Navidget Navigation
            self.active_navigation_technique = self.navidgetNavigation            
            print("Switch to Navidget Navigation")
            
            
        self.active_navigation_technique.enable(True)


    def set_navigation_matrix(self, MAT4):
        self.sf_nav_mat.value = MAT4


    def get_navigation_matrix(self):
        return self.sf_nav_mat.value



    def calc_pick_result(self):
        # update ray parameters
        self.ray.Origin.value = self.pointer_node.WorldTransform.value.get_translate()

        _vec = avango.gua.make_rot_mat(self.pointer_node.WorldTransform.value.get_rotate()) * avango.gua.Vec3(0.0,0.0,-1.0)
        _vec = avango.gua.Vec3(_vec.x,_vec.y,_vec.z)

        self.ray.Direction.value = _vec * self.ray_length

        # intersect
        _mf_pick_result = self.SCENEGRAPH.ray_test(self.ray, self.pick_options, self.white_list, self.black_list)

        if len(_mf_pick_result.value) > 0: # intersection found
            self.pick_result = _mf_pick_result.value[0] # get first pick result
        else: # nothing hit
            self.pick_result = None


    def update_ray_visualization(self):
        if self.pick_result is not None: # something hit            
            _pick_world_pos = self.pick_result.WorldPosition.value # pick position in world coordinate system    
            _distance = self.pick_result.Distance.value * self.ray_length # pick distance in ray coordinate system        
        
            self.ray_geometry.Transform.value = \
                avango.gua.make_trans_mat(0.0,0.0,_distance * -0.5) * \
                avango.gua.make_rot_mat(-90.0,1,0,0) * \
                avango.gua.make_scale_mat(self.ray_thickness, _distance, self.ray_thickness)

            self.intersection_geometry.Tags.value = [] # set intersection point visible
            self.intersection_geometry.Transform.value = avango.gua.make_trans_mat(_pick_world_pos) * avango.gua.make_scale_mat(self.intersection_point_size)

        else:  # nothing hit --> apply default ray visualization
            self.ray_geometry.Transform.value = \
                avango.gua.make_trans_mat(0.0,0.0,self.ray_length * -0.5) * \
                avango.gua.make_rot_mat(-90.0,1,0,0) * \
                avango.gua.make_scale_mat(self.ray_thickness, self.ray_length, self.ray_thickness)
        
            self.intersection_geometry.Tags.value = ["invisible"] # set intersection point invisible


    ### callback functions ###
    @field_has_changed(sf_key_1)
    def sf_key_1_changed(self):
        if self.sf_key_1.value == True: # key is pressed
            self.set_navigation_technique(0)
            

    @field_has_changed(sf_key_2)
    def sf_key_2_changed(self):
        if self.sf_key_2.value == True: # key is pressed
            self.set_navigation_technique(1)


    @field_has_changed(sf_key_3)
    def sf_key_3_changed(self):
        if self.sf_key_3.value == True: # key is pressed
            self.set_navigation_technique(2)




class NavigationTechnique(avango.script.Script):


    ## constructor
    def __init__(self):
        self.super(NavigationTechnique).__init__()

        ### variables ###
        self.enable_flag = False
                          

    ### functions ###
    def enable(self, BOOL):
        self.enable_flag = BOOL


    ### calback functions ###
    def evaluate(self): # evaluated every frame
        raise NotImplementedError("To be implemented by a subclass.")


   
class SteeringNavigation(NavigationTechnique):

    ### fields ###

    ## input fields
    mf_dof = avango.MFFloat()
    mf_dof.value = [0.0,0.0,0.0,0.0,0.0,0.0,0.0] # init 7 channels

    sf_button = avango.SFBool()
    
    ### constructor
    def __init__(self):
        NavigationTechnique.__init__(self) # call base class constructor


    def my_constructor(self, NAVIGATION_MANAGER, MF_DOF):

        ### external references ###
        self.NAVIGATION_MANAGER = NAVIGATION_MANAGER

        self.mf_dof.connect_from(MF_DOF)


        ### additional parameters ###
        self.translation_factor = 0.3
        self.rotation_factor = 1.0
       

        self.sf_button.connect_from(self.NAVIGATION_MANAGER.pointer_device_sensor.Button0)



    ### functions ###
    def enable(self, BOOL): # extend respective base-class function
        NavigationTechnique.enable(self, BOOL) # call base-class function

        if self.enable_flag == True:
            self.NAVIGATION_MANAGER.ray_geometry.Tags.value = [] # set ray visible
        else:
            self.NAVIGATION_MANAGER.intersection_geometry.Tags.value = ["invisible"]
            self.NAVIGATION_MANAGER.ray_geometry.Tags.value = ["invisible"]

    
    ### callback functions ###
    def evaluate(self): # implement respective base-class function
        if self.enable_flag == False:
            return

        ## handle translation input
        _x = self.mf_dof.value[0]
        _y = self.mf_dof.value[1]
        _z = self.mf_dof.value[2]
        
        _trans_vec = avango.gua.Vec3(_x, _y, _z) * self.translation_factor
        _trans_input = _trans_vec.length()
        #print(_trans_input)
        
        if _trans_input > 0.0: # guard
            # transfer-function for translation
            _factor = pow(min(_trans_input,1.0), 2)

            _trans_vec.normalize()
            _trans_vec *= _factor

        ## handle rotation input
        _rx = self.mf_dof.value[3]
        _ry = self.mf_dof.value[4]
        _rz = self.mf_dof.value[5]

        _rot_vec = avango.gua.Vec3(_rx, _ry, _rz) * self.rotation_factor
        _rot_input = _rot_vec.length()

        if _rot_input > 0.0: # guard
            # transfer-function for rotation
            _factor = pow(_rot_input, 2)

            _rot_vec.normalize()
            _rot_vec *= _factor


        ## accumulate input
        _new_mat = self.NAVIGATION_MANAGER.get_navigation_matrix() * \
            avango.gua.make_trans_mat(_trans_vec) * \
            avango.gua.make_rot_mat(_rot_vec.y,0,1,0) * \
            avango.gua.make_rot_mat(_rot_vec.x,1,0,0) * \
            avango.gua.make_rot_mat(_rot_vec.z,0,0,1)

        self.NAVIGATION_MANAGER.set_navigation_matrix(_new_mat)
        self.NAVIGATION_MANAGER.calc_pick_result()
        self.NAVIGATION_MANAGER.update_ray_visualization()


    @field_has_changed(sf_button)
    def sf_button_changed(self):
        if self.enable_flag == False:
            return

        ## ToDo: enable/disable maneuvering here
        # ...
                

class CameraInHandNavigation(NavigationTechnique):
    
    
    ### constructor
    def __init__(self):
        NavigationTechnique.__init__(self) # call base class constructor


    def my_constructor(self, NAVIGATION_MANAGER):

        ### external references ###
        self.NAVIGATION_MANAGER = NAVIGATION_MANAGER


        self.always_evaluate(True) # change global evaluation policy


    ### callback functions ###
    def evaluate(self): # implement respective base-class function
        if self.enable_flag == False:
            return

        ## ToDo: realize camera in hand behavior here
        # ...



class NavidgetNavigation(NavigationTechnique):

    ### fields ###

    ## input fields
    sf_button = avango.SFBool()
    
    ### constructor
    def __init__(self):
        NavigationTechnique.__init__(self) # call base class constructor


    def my_constructor(self, NAVIGATION_MANAGER, SCENEGRAPH):

        ### external references ###
        self.NAVIGATION_MANAGER = NAVIGATION_MANAGER


        ### additional parameters ###
        self.navidget_duration = 3.0 # in seconds
        self.navidget_sphere_size = 0.5 # in meters


        ### additional variables ###
        self.mode = 0 # 0 = passiv mode; 1 = target-defintion mode; 2 = animation mode

        self.navidget_start_pos = avango.gua.Vec3()
        self.navidget_target_pos = avango.gua.Vec3()        

        self.navidget_start_quat = avango.gua.Quat()
        self.navidget_target_quat = avango.gua.Quat()


        ### additional resources ###

        ## ToDo: init Navidget nodes here
        # ...
        

        self.sf_button.connect_from(self.NAVIGATION_MANAGER.pointer_device_sensor.Button0)

        self.always_evaluate(True) # change global evaluation policy


      


    ### functions ###
    def get_rotation_matrix_between_vectors(self, VEC1, VEC2): # helper function to calculate rotation matrix to rotate one vector on another one
        VEC1.normalize()
        VEC2.normalize()

        _angle = math.degrees(math.acos(VEC1.dot(VEC2)))
        _axis = VEC1.cross(VEC2)

        return avango.gua.make_rot_mat(_angle, _axis)
        


    ### callback functions ###
    def evaluate(self): # implement respective base-class function
        if self.enable_flag == False:
            return

        ## ToDo: init Navidget behavior here
        # ...


    @field_has_changed(sf_button)
    def sf_button_changed(self):
        if self.enable_flag == False:
            return

        ## ToDo: init Navidget behavior here
        # ...


                                      
