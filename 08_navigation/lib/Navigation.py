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
        self.NAVIGATION_NODE = NAVIGATION_NODE
        
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
        self.white_list = []
        _mf_pick_result = self.SCENEGRAPH.ray_test(self.ray, self.pick_options, self.white_list, self.black_list)

        if len(_mf_pick_result.value) > 0: # intersection found
            # print("smth picked")
            self.pick_result = _mf_pick_result.value[0] # get first pick result
        else: # nothing hit
            # print("nothing picked")
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
    maneuvering = False

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

        self.point_node = avango.gua.nodes.TransformNode(Name = "point_node")
        self.offset_node = avango.gua.nodes.TransformNode(Name = "offset_node")
        self.rot_node = avango.gua.nodes.TransformNode(Name = "rot_node")
        self.point_node.Children.value.append(self.offset_node)
        self.offset_node.Children.value.append(self.rot_node)
        self.NAVIGATION_MANAGER.SCENEGRAPH.Root.value.Children.value.append(self.point_node)

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

        if not self.maneuvering:
            ## accumulate input
            _new_mat = self.NAVIGATION_MANAGER.NAVIGATION_NODE.Transform.value * \
                avango.gua.make_trans_mat(_trans_vec) * \
                avango.gua.make_rot_mat(_rot_vec.y,0,1,0) * \
                avango.gua.make_rot_mat(_rot_vec.x,1,0,0) * \
                avango.gua.make_rot_mat(_rot_vec.z,0,0,1)

            self.NAVIGATION_MANAGER.set_navigation_matrix(_new_mat)
            self.NAVIGATION_MANAGER.calc_pick_result()
            self.NAVIGATION_MANAGER.update_ray_visualization()
        elif self.maneuvering:
            ## accumulate input
            _new_mat = self.point_node.Transform.value * \
                avango.gua.make_rot_mat(_rot_vec.y,0,1,0) * \
                avango.gua.make_rot_mat(_rot_vec.x,1,0,0) * \
                avango.gua.make_rot_mat(_rot_vec.z,0,0,1)
            self.point_node.Transform.value = _new_mat
            _offset_node_transvec = self.offset_node.Transform.value.get_translate()
            _new_trans_vec = _offset_node_transvec * _trans_vec.z * self.translation_factor

            self.offset_node.Transform.value = avango.gua.make_trans_mat(_new_trans_vec) * self.offset_node.Transform.value
            self.NAVIGATION_MANAGER.NAVIGATION_NODE.Transform.value = self.point_node.Transform.value \
                * self.offset_node.Transform.value * self.rot_node.Transform.value

    @field_has_changed(sf_button)
    def sf_button_changed(self):
        if self.enable_flag == False:
            return

        ## ToDo: enable/disable maneuvering here
        if self.sf_button.value:
            self.maneuvering = True
            
            self.point_node.Transform.value = avango.gua.make_trans_mat(self.NAVIGATION_MANAGER.intersection_geometry.WorldTransform.value.get_translate()) \
                * avango.gua.make_rot_mat(self.NAVIGATION_MANAGER.pointer_node.WorldTransform.value.get_rotate())
            self.offset_node.Transform.value = avango.gua.make_inverse_mat(self.point_node.Transform.value) \
                * self.NAVIGATION_MANAGER.NAVIGATION_NODE.WorldTransform.value
            self.rot_node.Transform.value = avango.gua.make_inverse_mat(avango.gua.make_rot_mat(self.offset_node.Transform.value.get_rotate())) \
                * avango.gua.make_inverse_mat(avango.gua.make_rot_mat(self.point_node.Transform.value.get_rotate())) \
                * avango.gua.make_rot_mat(self.NAVIGATION_MANAGER.NAVIGATION_NODE.WorldTransform.value.get_rotate())
            print(self.rot_node.WorldTransform.value)
            print(self.NAVIGATION_MANAGER.NAVIGATION_NODE.WorldTransform.value)
        else:
            self.maneuvering = False


class CameraInHandNavigation(NavigationTechnique):

    sf_button = avango.SFBool()
    camerainhand = False

    ### constructor
    def __init__(self):
        NavigationTechnique.__init__(self) # call base class constructor

    def my_constructor(self, NAVIGATION_MANAGER):

        ### external references ###
        self.pointer_node = NAVIGATION_MANAGER.pointer_node
        self.NAVIGATION_NODE = NAVIGATION_MANAGER.NAVIGATION_NODE
        self.sf_button.connect_from(NAVIGATION_MANAGER.pointer_device_sensor.Button0)
        self.always_evaluate(True) # change global evaluation policy
        self.last_frame = avango.gua.make_identity_mat()

    ### callback functions ###
    def evaluate(self): # implement respective base-class function
        ## ToDo: realize camera in hand behavior here
        if self.camerainhand:
            self.cur_frame = self.pointer_node.Transform.value * avango.gua.make_inverse_mat(self.last_frame)
            _trans = self.cur_frame.get_translate()
            _rot = self.cur_frame.get_rotate()
            self.NAVIGATION_NODE.Transform.value = self.NAVIGATION_NODE.Transform.value * avango.gua.make_trans_mat(_trans.x*5, _trans.y*5, _trans.z*5) \
                * avango.gua.make_rot_mat(_rot)

        self.last_frame = self.pointer_node.Transform.value

    @field_has_changed(sf_button)
    def sf_button_changed(self):
        if self.enable_flag == False:
            return

        ## ToDo: enable/disable maneuvering here
        print(self.sf_button.value)
        if self.sf_button.value:
            self.camerainhand = True
        else:
            self.camerainhand = False



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
        self.SCENEGRAPH = SCENEGRAPH
        self.pointer_node = self.NAVIGATION_MANAGER.pointer_node
        self.NAVIGATION_NODE = self.NAVIGATION_MANAGER.NAVIGATION_NODE
        self.intersection_geometry = self.NAVIGATION_MANAGER.intersection_geometry

        ### additional parameters ###
        self.navidget_duration = 3.0 # in seconds
        self.navidget_sphere_size = 1.5 # in meters

        self.navidget_on = False

        ### additional variables ###
        self.mode = 0 # 0 = passiv mode; 1 = target-defintion mode; 2 = animation mode

        self.navidget_start_pos = avango.gua.Vec3()
        self.navidget_target_pos = avango.gua.Vec3()        

        self.navidget_start_quat = avango.gua.Quat()
        self.navidget_target_quat = avango.gua.Quat()


        ### additional resources ###

        ## ToDo: init Navidget nodes here
        _loader = avango.gua.nodes.TriMeshLoader()
        self.navidget_node = avango.gua.nodes.TransformNode(Name = "navidget_node")
        self.navidget_node.Tags.value = ["invisible"]
        self.SCENEGRAPH.Root.value.Children.value.append(self.navidget_node)

        self.sphere_geometry = _loader.create_geometry_from_file("sphere_geometry", "data/objects/sphere.obj", avango.gua.LoaderFlags.DEFAULTS | avango.gua.LoaderFlags.MAKE_PICKABLE)
        self.sphere_geometry.Transform.value = avango.gua.make_scale_mat(50.0)
        self.sphere_geometry.Material.value.set_uniform("Color", avango.gua.Vec4(0.0,0.0,1.0,0.1))
        self.navidget_node.Children.value.append(self.sphere_geometry)


        self.camera_transform = avango.gua.nodes.TransformNode(Name = "camera_transform")
        self.navidget_node.Children.value.append(self.camera_transform)

        self.camera_geometry = _loader.create_geometry_from_file("camera_geometry", "data/objects/camera.obj", avango.gua.LoaderFlags.DEFAULTS)
        self.camera_geometry.Transform.value = avango.gua.make_scale_mat(150.0)
        self.camera_transform.Children.value.append(self.camera_geometry)
        
        self.sf_button.connect_from(self.NAVIGATION_MANAGER.pointer_device_sensor.Button0)

        self.always_evaluate(True) # change global evaluation policy


    ### functions ###
    def enable(self, BOOL): # extend respective base-class function
        NavigationTechnique.enable(self, BOOL) # call base-class function

        if self.enable_flag == True:
            self.NAVIGATION_MANAGER.ray_geometry.Tags.value = [] # set ray visible
        else:
            self.NAVIGATION_MANAGER.intersection_geometry.Tags.value = ["invisible"]
            self.NAVIGATION_MANAGER.ray_geometry.Tags.value = ["invisible"]


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

        self.NAVIGATION_MANAGER.calc_pick_result()
        self.NAVIGATION_MANAGER.update_ray_visualization()

        ## ToDo: init Navidget behavior here
        # _rot = self.get_rotation_matrix_between_vectors(self.navidget_node.Transform.value.get_translate(), self.intersection_geometry.Transform.value.get_translate())
        _pick_result = self.NAVIGATION_MANAGER.pick_result
        # if self.navidget_on == True:
        if self.mode == 0:
            self.navidget_node.Tags.value = ["invisible"]
            print(self.mode)
        elif self.mode == 1:
            print(self.mode)
            self.navidget_node.Transform.value = self.intersection_geometry.WorldTransform.value
            self.navidget_node.Tags.value = []

            if _pick_result == None:
                return
            elif _pick_result.Object.value != self.sphere_geometry:
                return

            _intersection_local = avango.gua.make_inverse_mat(self.navidget_node.Transform.value) * self.intersection_geometry.WorldTransform.value
            # self.navidget_target_pos = 
            # _intersection_local = avango.gua.make_inverse_mat(self.navidget_node.Transform.value) \
            #     * avango.gua.make_trans_mat(self.intersection_geometry.WorldTransform.value.get_translate())
            _vec1 = _intersection_local.get_translate()
            _vec2 = avango.gua.Vec3(0.0,0.0,1.0)
            _rot = self.get_rotation_matrix_between_vectors(_vec2, _vec1)

            self.camera_transform.Transform.value = _intersection_local * _rot
        # elif self.navidget_on == False:
        elif self.mode == 2:
            print(self.mode)
            # self.navidget_start_pos = self.NAVIGATION_NODE.Transform.value.get_translate()
            # self.navidget_target_pos = self.camera_transform.Transform.value.get_translate()
            # _translation_anim = self.navidget_start_pos.lerp_to(self.navidget_target_pos, 0.1)
            # print(_translation_anim)

            # self.navidget_start_quat = self.NAVIGATION_NODE.Transform.value.get_rotate()
            # self.navidget_target_quat = self.camera_transform.Transform.value.get_rotate()
            # _rotation_anim = self.navidget_start_quat.slerp_to(self.navidget_target_quat, 0.1)
            # print(_rotation_anim)

            # _tranformation_matrix = avango.gua.make_trans_mat(_translation_anim) * _rotation_anim
            # print(_tranformation_matrix)
            # self.mode = 0

            # self.NAVIGATION_NODE.Transform.value = _tranformation_matrix

    @field_has_changed(sf_button)
    def sf_button_changed(self):
        if self.enable_flag == False:
            return

        ## ToDo: init Navidget behavior here
        if self.mode == 0:
            self.mode = 1
            # self.navidget_node.Transform.value = self.intersection_geometry.WorldTransform.value
            # self.navidget_node.Tags.value = []
        elif self.mode == 1:
            self.mode = 2
        elif self.mode == 2:
            self.mode = 0
        #     self.navidget_node.Tags.value = ["invisible"]



                                      
