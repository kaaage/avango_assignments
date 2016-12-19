#!/usr/bin/python

### import guacamole libraries ###
import avango
import avango.gua
import avango.script
from avango.script import field_has_changed
import avango.daemon



class RayPointer(avango.script.Script):

    ## input fields
    sf_button = avango.SFBool()


    ## constructor
    def __init__(self):
        self.super(RayPointer).__init__()


    def my_constructor(self,
        SCENEGRAPH = None,
        PARENT_NODE = None,
        POINTER_TRACKING_STATION = None,
        TRACKING_TRANSMITTER_OFFSET = avango.gua.make_identity_mat(),
        POINTER_DEVICE_STATION = None,
        ):


        ### external references ###
        self.SCENEGRAPH = SCENEGRAPH


        ### parameters ###
        
        ## visualization
        self.ray_length = 2.0 # in meter
        self.ray_thickness = 0.0075 # in meter

        self.intersection_point_size = 0.01 # in meter

        ## picking
        self.white_list = []   
        self.black_list = ["invisible"]

        self.pick_options = avango.gua.PickingOptions.PICK_ONLY_FIRST_OBJECT \
                            | avango.gua.PickingOptions.GET_POSITIONS \
                            | avango.gua.PickingOptions.GET_NORMALS \
                            | avango.gua.PickingOptions.GET_WORLD_POSITIONS \
                            | avango.gua.PickingOptions.GET_WORLD_NORMALS


        ### resources ###
    
        ## init sensors
        self.pointer_tracking_sensor = avango.daemon.nodes.DeviceSensor(DeviceService = avango.daemon.DeviceService())
        self.pointer_tracking_sensor.Station.value = POINTER_TRACKING_STATION
        self.pointer_tracking_sensor.TransmitterOffset.value = TRACKING_TRANSMITTER_OFFSET
            
        self.pointer_device_sensor = avango.daemon.nodes.DeviceSensor(DeviceService = avango.daemon.DeviceService())
        self.pointer_device_sensor.Station.value = POINTER_DEVICE_STATION

        self.sf_button.connect_from(self.pointer_device_sensor.Button0)


        ## init nodes

        self.pointer_node = avango.gua.nodes.TransformNode(Name = "pointer_node")
        self.pointer_node.Transform.connect_from(self.pointer_tracking_sensor.Matrix)
        PARENT_NODE.Children.value.append(self.pointer_node)


        _loader = avango.gua.nodes.TriMeshLoader()

        self.ray_geometry = _loader.create_geometry_from_file("ray_geometry", "data/objects/cylinder.obj", avango.gua.LoaderFlags.DEFAULTS)
        self.ray_geometry.Transform.value = \
            avango.gua.make_trans_mat(0.0,0.0,self.ray_length * -0.5) * \
            avango.gua.make_rot_mat(-90.0,1,0,0) * \
            avango.gua.make_scale_mat(self.ray_thickness, self.ray_length, self.ray_thickness)
        self.ray_geometry.Material.value.set_uniform("Color", avango.gua.Vec4(1.0,0.0,0.0,1.0))
        self.pointer_node.Children.value.append(self.ray_geometry)


        self.intersection_geometry = _loader.create_geometry_from_file("intersection_geometry", "data/objects/sphere.obj", avango.gua.LoaderFlags.DEFAULTS)
        self.intersection_geometry.Tags.value = ["invisible"] # set geometry invisible
        self.intersection_geometry.Material.value.set_uniform("Color", avango.gua.Vec4(1.0,0.0,0.0,1.0))
        self.SCENEGRAPH.Root.value.Children.value.append(self.intersection_geometry)



        self.ray = avango.gua.nodes.Ray()
      
      
        self.always_evaluate(True) # change global evaluation policy
      
        
    
    ### functions ###

    def calc_pick_result(self, PICK_MAT = avango.gua.make_identity_mat()):

        # update ray parameters
        self.ray.Origin.value = PICK_MAT.get_translate()

        _vec = avango.gua.make_rot_mat(PICK_MAT.get_rotate_scale_corrected()) * avango.gua.Vec3(0.0,0.0,-1.0)
        _vec = avango.gua.Vec3(_vec.x,_vec.y,_vec.z)

        self.ray.Direction.value = _vec * self.ray_length

        # intersect
        _mf_pick_result = self.SCENEGRAPH.ray_test(self.ray, self.pick_options, self.white_list, self.black_list)

        return _mf_pick_result


    def update_ray_visualization(self, PICK_WORLD_POS = None, PICK_DISTANCE = 0.0):

        if PICK_WORLD_POS is None: # nothing hit
            self.ray_geometry.Transform.value = \
                avango.gua.make_trans_mat(0.0,0.0,self.ray_length * -0.5) * \
                avango.gua.make_rot_mat(-90.0,1,0,0) * \
                avango.gua.make_scale_mat(self.ray_thickness, self.ray_length, self.ray_thickness)
        
            self.intersection_geometry.Tags.value = ["invisible"] # set intersection point invisible

        else: # something hit
            self.ray_geometry.Transform.value = \
                avango.gua.make_trans_mat(0.0,0.0,PICK_DISTANCE * -0.5) * \
                avango.gua.make_rot_mat(-90.0,1,0,0) * \
                avango.gua.make_scale_mat(self.ray_thickness, PICK_DISTANCE, self.ray_thickness)

            self.intersection_geometry.Tags.value = [] # set intersection point invisible

            self.intersection_geometry.Transform.value = avango.gua.make_trans_mat(PICK_WORLD_POS) * avango.gua.make_scale_mat(self.intersection_point_size)


    def start_dragging(self, NODE):          
        self.dragged_node = NODE        
        self.dragging_offset_mat = avango.gua.make_inverse_mat(self.pointer_node.WorldTransform.value) * self.dragged_node.WorldTransform.value # object transformation in pointer coordinate system

  
    def stop_dragging(self): 
        self.dragged_node = None
        self.dragging_offset_mat = avango.gua.make_identity_mat()


    def dragging(self):
        if self.dragged_node is not None: # object to drag
            _new_mat = self.pointer_node.WorldTransform.value * self.dragging_offset_mat # new object position in world coodinates
            _new_mat = avango.gua.make_inverse_mat(self.dragged_node.Parent.value.WorldTransform.value) * _new_mat # transform new object matrix from global to local space
        
            self.dragged_node.Transform.value = _new_mat


    ### callback functions ###

    @field_has_changed(sf_button)
    def sf_button_changed(self):
        if self.sf_button.value == True: # button pressed
            _mf_pick_result = self.calc_pick_result(PICK_MAT = self.pointer_node.WorldTransform.value)
    
            if len(_mf_pick_result.value) > 0: # intersection found
                _pick_result = _mf_pick_result.value[0] # get first pick result

                _node = _pick_result.Object.value # get intersected geometry node
                #_node = _node.Parent.value # take the parent node of the geomtry node (the whole car)

                self.start_dragging(_node)

        else: # button released
            self.stop_dragging()

    
    def evaluate(self):   
        ## calc ray intersection
        _mf_pick_result = self.calc_pick_result(PICK_MAT = self.pointer_node.WorldTransform.value)

        #print("hits:", len(_mf_pick_result.value))
    
        if len(_mf_pick_result.value) > 0: # intersection found
            _pick_result = _mf_pick_result.value[0] # get first pick result

            _node = _pick_result.Object.value # get intersected geometry node
    
            _pick_pos = _pick_result.Position.value # pick position in object coordinate system
            _pick_world_pos = _pick_result.WorldPosition.value # pick position in world coordinate system
    
            _distance = _pick_result.Distance.value * self.ray_length # pick distance in ray coordinate system
    
            print(_node, _pick_pos, _pick_world_pos, _distance)
        
            self.update_ray_visualization(PICK_WORLD_POS = _pick_world_pos, PICK_DISTANCE = _distance)
    
        else: # nothing hit
            self.update_ray_visualization() # apply default ray visualization
        


        self.dragging() # possibly drag object

