#!/usr/bin/python

#### import guacamole libraries
import avango
import avango.gua 
import avango.script
from avango.script import field_has_changed
import avango.daemon

### import application libraries
from lib.Device import MouseInput

### import python libraries
# ...

   
class ManipulationManager(avango.script.Script):

    ### input fields
    sf_key_1 = avango.SFBool()
    sf_key_2 = avango.SFBool()
    sf_key_3 = avango.SFBool()

    ### internal fields
    sf_hand_mat = avango.gua.SFMatrix4()
    sf_dragging_trigger = avango.SFBool()


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
        self.TARGET_LIST = TARGET_LIST


        ### variables ###
        self.dragging_technique = 0
        self.dragged_objects_list = []
        self.lf_hand_mat = avango.gua.make_identity_mat() # last frame hand matrix

        
        ## init hand geometry
        _loader = avango.gua.nodes.TriMeshLoader() # init trimesh loader to load external meshes
        
        self.hand_geometry = _loader.create_geometry_from_file("hand_geometry", "data/objects/hand.obj", avango.gua.LoaderFlags.DEFAULTS)
        self.hand_geometry.Transform.value = \
            avango.gua.make_rot_mat(45.0,1,0,0) * \
            avango.gua.make_rot_mat(180.0,0,1,0) * \
            avango.gua.make_scale_mat(0.06)
        self.hand_geometry.Material.value.set_uniform("Color", avango.gua.Vec4(1.0, 0.86, 0.54, 1.0))
        self.hand_geometry.Material.value.set_uniform("Emissivity", 0.9)
        self.hand_geometry.Material.value.set_uniform("Metalness", 0.1)
        
        self.hand_transform = avango.gua.nodes.TransformNode(Name = "hand_transform")
        self.hand_transform.Children.value = [self.hand_geometry]
        PARENT_NODE.Children.value.append(self.hand_transform)
        self.hand_transform.Transform.connect_from(self.sf_hand_mat)
        

        ### init sub-classes ###
        self.mouseInput = MouseInput()
        self.mouseInput.my_constructor("gua-device-mouse")

        # init manipulation technique
        self.IPCManipulation = IsotonicPositionControlManipulation()
        self.IPCManipulation.my_constructor(self.mouseInput.mf_dof, self.mouseInput.mf_buttons)
        self.IPCManipulation.enable_manipulation(True)

        # init field connections      
        self.sf_hand_mat.connect_from(self.IPCManipulation.sf_mat)
        self.sf_dragging_trigger.connect_from(self.IPCManipulation.sf_action_trigger)
                

        ## init keyboard sensor
        self.keyboard_sensor = avango.daemon.nodes.DeviceSensor(DeviceService = avango.daemon.DeviceService())
        self.keyboard_sensor.Station.value = "gua-device-keyboard0"

        self.sf_key_1.connect_from(self.keyboard_sensor.Button16) # key 1
        self.sf_key_2.connect_from(self.keyboard_sensor.Button17) # key 2
        self.sf_key_3.connect_from(self.keyboard_sensor.Button18) # key 3


        ### set initial states ###
        self.set_dragging_technique(1) # switch to 1st dragging variant


    ### functions ###
    
    def set_dragging_technique(self, INT):
        self.dragging_technique = INT
        
        print("Dragging Technique set to technique", self.dragging_technique)
    


    def start_dragging(self):  
        _hand_mat = self.hand_transform.Transform.value

        for _node in self.TARGET_LIST:
            if self.is_highlight_material(_node.CurrentColor.value) == True: # a monkey node in close proximity
                _node.CurrentColor.value = avango.gua.Vec4(1.0, 0.0, 0.0, 1.0)
                _node.Material.value.set_uniform("Color", _node.CurrentColor.value) # switch to dragging material

                self.dragged_objects_list.append(_node) # add node for dragging
          
                ## TODO: Implement individual components of the different dragging strategies here ##
                if self.dragging_technique == 1: # change of node order in scenegraph
                    _node.Parent.value.Children.value.remove(_node)
                    self.hand_transform.Children.value.append(_node)
                    _node.Transform.value = avango.gua.make_inverse_mat(_hand_mat) * _node.Transform.value 

                    pass

                elif self.dragging_technique == 2: # absolute tool-hand offset to tool space
                    pass

                elif self.dragging_technique == 3: # relative tool input to object space
                    pass
  
  
  
    def update_dragging_candidates(self):
        _hand_pos = self.hand_transform.Transform.value.get_translate()
    
        for _node in self.TARGET_LIST:
            _pos = _node.Transform.value.get_translate() # a monkey position

            _dist = (_hand_pos - _pos).length() # hand-object distance
            _color = _node.CurrentColor.value

            ## toggle object highlight
            if _dist < 0.025 and self.is_default_material(_color) == True:
                _node.CurrentColor.value = avango.gua.Vec4(0.0, 1.0, 0.0, 1.0)
                _node.Material.value.set_uniform("Color", _node.CurrentColor.value) # switch to highlight material

            elif _dist > 0.03 and self.is_highlight_material(_color) == True:
                _node.CurrentColor.value = avango.gua.Vec4(1.0, 1.0, 1.0, 1.0)
                _node.Material.value.set_uniform("Color", _node.CurrentColor.value) # switch to default material
    

    def object_dragging(self):
        # apply hand movement to (all) dragged objects
        for _node in self.dragged_objects_list:
            ## TODO: Implement individual components of the different dragging strategies here ##        
            if self.dragging_technique == 1: # change node order in scenegraph

                pass

            elif self.dragging_technique == 2: # absolute tool-hand offset to tool space
                pass

            elif self.dragging_technique == 3: # relative tool input to object space
                pass

  
    def stop_dragging(self):  
        ## handle all dragged objects
        for _node in self.dragged_objects_list:      
            _node.CurrentColor.value = avango.gua.Vec4(0.0, 1.0, 0.0, 1.0)
            _node.Material.value.set_uniform("Color", _node.CurrentColor.value) # switch to highlight material

        ## TODO: Implement individual components of the different dragging strategies here ##
        if self.dragging_technique == 1: # change node order in scenegraph
            transform = _node.WorldTransform.value
            _node.Parent.value.Children.value.remove(_node)
            self.SCENE_ROOT.Children.value.append(_node)
            _node.Transform.value = transform

            pass

        elif self.dragging_technique == 2: # absolute tool-hand offset to tool space
            pass

        elif self.dragging_technique == 3: # relative tool input to object space
            pass
    
        self.dragged_objects_list = [] # clear list


    def is_default_material(self, VEC4):
        return VEC4.x == 1.0 and VEC4.y == 1.0 and VEC4.z == 1.0 and VEC4.w == 1.0


    def is_highlight_material(self, VEC4):
        return VEC4.x == 0.0 and VEC4.y == 1.0 and VEC4.z == 0.0 and VEC4.w == 1.0


    def is_dragging_material(self, VEC4):
        return VEC4.x == 1.0 and VEC4.y == 0.0 and VEC4.z == 0.0 and VEC4.w == 1.0

    
    ### callback functions ###

    @field_has_changed(sf_key_1)
    def sf_key_1_changed(self):
        if self.sf_key_1.value == True: # key is pressed
            self.set_dragging_technique(1) # switch dragging technique


    @field_has_changed(sf_key_2)
    def sf_key_2_changed(self):
        if self.sf_key_2.value == True: # key is pressed
            self.set_dragging_technique(2) # switch dragging technique


    @field_has_changed(sf_key_3)
    def sf_key_3_changed(self):
        if self.sf_key_3.value == True: # key is pressed
            self.set_dragging_technique(3) # switch dragging technique
      

    @field_has_changed(sf_dragging_trigger)
    def sf_dragging_trigger_changed(self):
        if self.sf_dragging_trigger.value == True:
            self.start_dragging()  
        else:
            self.stop_dragging()
      

    def evaluate(self): # evaluated every frame if any input field has changed (incl. dependency evaluation)
        self.update_dragging_candidates()

        self.object_dragging() # possibly drag object with hand input

        self.lf_hand_mat = self.hand_transform.Transform.value
        

class Manipulation(avango.script.Script):

    ### input fields
    mf_dof = avango.MFFloat()
    mf_dof.value = [0.0,0.0,0.0,0.0,0.0,0.0,0.0] # init 7 channels

    mf_buttons = avango.MFBool()
    mf_buttons.value = [False,False] # init 2 channels


    ### output_fields
    sf_mat = avango.gua.SFMatrix4()
    sf_mat.value = avango.gua.make_identity_mat()

    sf_action_trigger = avango.SFBool()
    

    ### constructor
    def __init__(self):
        self.super(Manipulation).__init__()

        ### variables ###
        self.type = ""
        self.enable_flag = False

    
    ### callback functions ###
    def evaluate(self): # evaluated every frame if any input field has changed  
        if self.enable_flag == True:
            self.manipulate()


    @field_has_changed(mf_buttons)
    def mf_buttons_changed(self):
        if self.enable_flag == True:
            _left_button = self.mf_buttons.value[0]
            _right_button = self.mf_buttons.value[1]

            self.sf_action_trigger.value = _left_button ^ _right_button # button left XOR button right

        
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
    
    
    def clamp_matrix(self, MATRIX):    
        # clamp translation to certain range (within screen space)
        _x_range = 0.3 # in meter
        _y_range = 0.15 # in meter
        _z_range = 0.15 # in meter    

        MATRIX.set_element(0,3, min(_x_range, max(-_x_range, MATRIX.get_element(0,3)))) # clamp x-axis
        MATRIX.set_element(1,3, min(_y_range, max(-_y_range, MATRIX.get_element(1,3)))) # clamp y-axis
        MATRIX.set_element(2,3, min(_z_range, max(-_z_range, MATRIX.get_element(2,3)))) # clamp z-axis
         
        return MATRIX



class IsotonicPositionControlManipulation(Manipulation):

    def my_constructor(self, MF_DOF, MF_BUTTONS):
        self.type = "isotonic-position-control"
    
        # init field connections
        self.mf_dof.connect_from(MF_DOF)
        self.mf_buttons.connect_from(MF_BUTTONS)


    ## implement respective base-class function
    def manipulate(self):
        _x = self.mf_dof.value[0]
        _y = self.mf_dof.value[1]
        _z = self.mf_dof.value[2]
          
        _x *= 0.1
        _y *= 0.1
        _z *= 0.1
       
        # accumulate input
        _new_mat = avango.gua.make_trans_mat(_x, _y, _z) * self.sf_mat.value

        # possibly clamp matrix (to screen space borders)
        _new_mat = self.clamp_matrix(_new_mat)

        self.sf_mat.value = _new_mat # apply new matrix to field
    

    ## implement respective base-class function    
    def reset(self):
        self.sf_mat.value = avango.gua.make_identity_mat() # snap hand back to screen center

        
