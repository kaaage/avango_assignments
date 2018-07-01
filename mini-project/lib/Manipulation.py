#!/usr/bin/python

#### import guacamole libraries
import avango
import avango.gua 
import avango.script
from avango.script import field_has_changed
import avango.daemon
import math
import time

### import application libraries
from lib.Device import MouseInput, SpacemouseInput, NewSpacemouseInput
from lib.LeapSensor import LeapSensor

### import python libraries
# ...


### global variables ###
#SPACEMOUSE_TYPE = "Spacemouse"
SPACEMOUSE_TYPE = "Blue Spacemouse" # blue LED

   
class ManipulationManager(avango.script.Script):

    ### input fields
    sf_key_1 = avango.SFBool()
    sf_key_2 = avango.SFBool()
    sf_key_3 = avango.SFBool()
    sf_key_4 = avango.SFBool()
    sf_key_5 = avango.SFBool()
    sf_key_6 = avango.SFBool()            

    sf_hand_mat = avango.gua.SFMatrix4()


    # constructor
    def __init__(self):
        self.super(ManipulationManager).__init__()

    def my_constructor(self,
        PARENT_NODE = None,
        SCENE_ROOT = None,
        TARGET_LIST = [],
        ):


        ### external references ###        
        self.SCENE_ROOT = SCENE_ROOT

        ## base node ##
        self.base_node = avango.gua.nodes.TransformNode(Name="base_node")
        
        self.base_node.Transform.value = avango.gua.make_trans_mat(-2.1, 0.96, 0.705) * avango.gua.make_rot_mat(90.0, 0, 1, 0) * \
             avango.gua.make_rot_mat(90.0, 1, 0, 0) * avango.gua.make_rot_mat(90.0, -1, 0, 0)
        
        self.base_node.Transform.value = avango.gua.make_trans_mat(-2.1, 0.96, 0.705) * avango.gua.make_rot_mat(90.0, 0, 1, 0)
        PARENT_NODE.Children.value.append(self.base_node)


        ### init leap position sensor
        _leap_transmitter_offset = avango.gua.make_trans_mat(-0.98, -(0.58 + 0.975), 0.27 + 3.48) * avango.gua.make_rot_mat(90.0,0,1,0) # transformation into tracking coordinate system 

        self.leap_tracking_sensor = avango.daemon.nodes.DeviceSensor(DeviceService = avango.daemon.DeviceService())
        self.leap_tracking_sensor.Station.value = "tracking-dlp-leap"

        self.leap_position = avango.gua.nodes.TransformNode(Name = "leap_position")
        self.leap_position.Transform.connect_from(self.leap_tracking_sensor.Matrix)

        # self.leap_position.Transform.value = avango.gua.make_trans_mat(0.0, -0.39, 0.0)
        #self.leap_position.Tags.value = ["invisible"]
        PARENT_NODE.Children.value.append(self.leap_position)


        ### init leap navigation spacemouse  ###           
        self.navigation_transform = avango.gua.nodes.TransformNode(Name = "navigation_transform")
        self.navigation_transform.Transform.connect_from(self.sf_hand_mat)

        ## put Leap 3D model into scene ###
        _LeapModel = avango.gua.nodes.TriMeshLoader().create_geometry_from_file("LEAP", "data/objects/LeapModel.stl", avango.gua.LoaderFlags.DEFAULTS)
        _LeapModel.Transform.value =  avango.gua.make_trans_mat(0.01, 0.054, 0.01) * \
                avango.gua.make_rot_mat(-90,1,0.0,0.0) * \
                avango.gua.make_scale_mat(0.55)
        self.navigation_transform.Children.value.append(_LeapModel)

        ## init Leap
        self.cube_list = []
        self.leap_position.Children.value.append(self.navigation_transform)


        ### init leap sensor ###
        leap = LeapSensor()
        # either append leap to self.navigation_transform or to self.leap_position
        leap.my_constructor(SCENEGRAPH = self.SCENE_ROOT, BASENODE = self.navigation_transform, TARGET_LIST = TARGET_LIST)
    
        

        ## init inputs
        self.mouseInput = MouseInput()
        self.mouseInput.my_constructor("gua-device-mouse")

        if SPACEMOUSE_TYPE == "Spacemouse":
            self.spacemouseInput = SpacemouseInput()
            self.spacemouseInput.my_constructor("gua-device-spacemouse")
            # init field connections
            self.mf_dof.connect_from(MF_DOF)
            self.mf_buttons.connect_from(MF_BUTTONS)

        elif SPACEMOUSE_TYPE == "Blue Spacemouse":
            self.spacemouseInput = NewSpacemouseInput()
            self.spacemouseInput.my_constructor("gua-device-spacemouse")
        

        #done
        self.ERCManipulation = ElasticRateControlManipulation()
        self.ERCManipulation.my_constructor(self.spacemouseInput.mf_dof, self.spacemouseInput.mf_buttons, LEAP = leap)
        
        self.ERCManipulation.enable_manipulation(True)

        # init field connections      
        self.sf_hand_mat.connect_from(self.ERCManipulation.sf_mat)
        #self.sf_hand_mat.value = avango.gua.make_trans_mat(0.0, -0.45, -0.45)

    
    def evaluate(self): # evaluated every frame if any input field has changed (incl. dependency evaluation)
        _leap_pos = self.leap_tracking_sensor.Matrix.value.get_translate()

class Manipulation(avango.script.Script):

    ### input fields
    mf_dof = avango.MFFloat()
    mf_dof.value = [0.0,0.0,0.0,0.0,0.0,0.0,0.0] # init 7 channels

    mf_buttons = avango.MFBool()
    mf_buttons.value = [False,False] # init 2 channels


    ### Leap Start position
    sf_mat = avango.gua.SFMatrix4()
    sf_mat.value = avango.gua.make_trans_mat(0.0, -0.45, -0.45)

    sf_action_trigger = avango.SFBool()

    ### constructor
    def __init__(self):
        self.super(Manipulation).__init__()

        ### variables ###
        self.type = ""
        self.enable_flag = False # TODO: Remove the useless Manipulation classes

        self.in_center = False

    
    ### callback functions ###
    def evaluate(self): # evaluated every frame if any input field has changed  
        if self.enable_flag == True:
            self.manipulate()


    @field_has_changed(mf_buttons)
    def mf_buttons_changed(self):
        if self.enable_flag == True:
            _left_button = self.mf_buttons.value[0]
            _right_button = self.mf_buttons.value[1]

            if _left_button: 
                # print("Trigger dragging mode")
                self.trigger_dragging()
            if _right_button: 
                print("Reset to real leap position")
                if self.in_center == False:
                    self.center()
                else:
                    self.reset()

        
    ### functions ###
    def enable_manipulation(self, FLAG):   
        self.enable_flag = FLAG
    
        if self.enable_flag == True:
            print(self.type + " enabled")
    
            self.reset()
      
   
    def manipulate(self):
        raise NotImplementedError("To be implemented by a subclass.")


    def reset(self):
        raise NotImplementedError("To be implemented by a subclass.")
    
    def center(self):
        raise NotImplementedError("To be implemented by a subclass.")
    
    def clamp_matrix(self, MATRIX):    
        # clamp translation to certain range (within screen space)
        _x_range = 0.8 # in meter
        _y_range = 0.8 # in meter
        _z_range = 1.6 # in meter    

        MATRIX.set_element(0,3, min(_x_range, max(-_x_range, MATRIX.get_element(0,3)))) # clamp x-axis
        MATRIX.set_element(1,3, min(_y_range, max(-_y_range, MATRIX.get_element(1,3)))) # clamp y-axis
        MATRIX.set_element(2,3, min(_z_range, max(-_z_range, MATRIX.get_element(2,3)))) # clamp z-axis
         
        return MATRIX

class ElasticRateControlManipulation(Manipulation):

    _x = 0.0
    _y = -0.45
    _z = -0.45
    def my_constructor(self, MF_DOF, MF_BUTTONS, LEAP):
        self.type = "elastic-rate-control"
        #self.sf_mat.value = avango.gua.make_trans_mat(0.0, -0.45, -0.45) #TODO: i do not know how and where to set the initial leap position to center

        # init field connections
        self.mf_dof.connect_from(MF_DOF)
        self.mf_buttons.connect_from(MF_BUTTONS)

        self.leap = LEAP


    ## implement respective base-class function
    def manipulate(self):
        # #isomorphic
        self._x += self.mf_dof.value[0] * 0.001
        self._y += self.mf_dof.value[1] * 0.001
        self._z += self.mf_dof.value[2] * 0.001
        # accumulate input
        _new_mat = avango.gua.make_trans_mat(self._x, self._y, self._z)
        # possibly clamp matrix (to screen space borders)
        _new_mat = self.clamp_matrix(_new_mat)
        self.sf_mat.value = _new_mat # apply new matrix to field

    ## implement respective base-class function
    def reset(self):
        self.in_center = False
        self.sf_mat.value = avango.gua.make_identity_mat() 
        self._x = 0.0
        self._y = 0.0
        self._z = 0.0

    def center(self):
        # TODO: Calculate center position by inverse scenegraph
        self.in_center = True
        self._x = 0.0
        self._y = -0.45
        self._z = -0.45
        _new_mat = avango.gua.make_trans_mat(self._x, self._y, self._z)
        self.sf_mat.value = _new_mat # apply new matrix to field

    def trigger_dragging(self):
        self.leap.dragging_mode = True if self.leap.dragging_mode == False else False