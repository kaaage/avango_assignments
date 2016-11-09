#!/usr/bin/python

# import guacamole libraries
import avango
import avango.gua
import avango.script
from avango.script import field_has_changed

# import application libraries
from lib.KeyboardInput import KeyboardInput
from lib.Intersection import Intersection

# import python libraries
import time


class Avatar:
  
    ## constructor
    def __init__(self,
        SCENEGRAPH = None,
        START_MATRIX = avango.gua.make_identity_mat(),
        ):


        ### resources ###
        _loader = avango.gua.nodes.TriMeshLoader() # init trimesh loader to load external meshes

        ## init avatar nodes
        self.avatar_geometry = _loader.create_geometry_from_file("avatar_geometry", "data/objects/monkey.obj", avango.gua.LoaderFlags.DEFAULTS)
        self.avatar_geometry.Transform.value = avango.gua.make_scale_mat(0.03)
        self.avatar_geometry.Material.value.set_uniform("Color", avango.gua.Vec4(1.0, 0.2, 0.2, 1.0))

        self.avatar_transform = avango.gua.nodes.TransformNode(Name = "avatar_node")
        self.avatar_transform.Children.value = [self.avatar_geometry]
        SCENEGRAPH.Root.value.Children.value.append(self.avatar_transform)



        ## init internal sub-classes
        self.input = KeyboardInput()

        self.accumulator = Accumulator()
        self.accumulator.my_constructor(START_MATRIX = START_MATRIX)

        self.groundFollowing = GroundFollowing()
        self.groundFollowing.my_constructor(SCENEGRAPH = SCENEGRAPH, START_MATRIX = START_MATRIX)


        ## init field connections (dependency graph)
        self.accumulator.sf_move_vec.connect_from(self.input.sf_move_vec) # propagate movement vector into movement accumulator        
        self.avatar_transform.Transform.connect_from(self.accumulator.sf_mat) # connect final movement matrix to avatar node matrix

        # ToDo: integrate the groundFollowing into the dataflow
        # evtl. replace existing field connections with new one
        # pay attention to potential loops in the dataflow --> use weak field connections to prevent loops
        # ...




################################
## Movement accumulator takes the (relative) movement vector of a KeyboardInput instance and applies
## it to an accumulated (absolute) matrix.
################################

class Accumulator(avango.script.Script):

    ## input fields
    sf_move_vec = avango.gua.SFVec3()

    ## output field
    sf_mat = avango.gua.SFMatrix4()
  
  
    ## constructor
    def __init__(self):
        self.super(Accumulator).__init__()


    def my_constructor(self,
        START_MATRIX = avango.gua.make_identity_mat(),
        ):

        ## set initial state                    
        self.sf_mat.value = START_MATRIX


    ###  callback functions ###
    def evaluate(self): # evaluated once every frame if any input field has changed
        #print("movement input", self.sf_move_vec.value)

        # ToDO: accumulate movement input to output matrix        
        #print(self.sf_mat.value)# += self.sf_move_vec.value
        self.sf_mat.value = self.sf_mat.value * avango.gua.make_trans_mat(self.sf_move_vec.value)
        #print(self.sf_mat.value)
        
        pass



################################
## GroundFollowing takes a matrix from an MovementAccumulator instance and corrects it with
## respect to gravity in the scene. The result can then be applied to the avatar's transformation node.
################################

class GroundFollowing(avango.script.Script):

    ## input fields
    sf_mat = avango.gua.SFMatrix4()

    ## ouput fields
    sf_modified_mat = avango.gua.SFMatrix4()

    ## internal fields
    mf_pick_result = avango.gua.MFPickResult()


    ## constructor
    def __init__(self):
        self.super(GroundFollowing).__init__()


    def my_constructor(self,
        SCENEGRAPH = None,
        START_MATRIX = avango.gua.make_identity_mat(),
        ):

        ### parameters ###
        self.fall_velocity = 0.003 # in meter/sec

        self.pick_length = 1.0 # in meter
        self.pick_direction = avango.gua.Vec3(0.0,-1.0,0.0)


        ### variables ###
        self.fall_vec = avango.gua.Vec3()

        self.lf_time = time.time()


        ## init internal sub-classes
        self.gravity_intersection = Intersection()
        self.gravity_intersection.my_constructor(SCENEGRAPH, self.sf_mat, self.pick_length, self.pick_direction)

        ## init field connections
        self.mf_pick_result.connect_from(self.gravity_intersection.mf_pick_result)

        ## set initial state                                                                                    ss
        self.sf_modified_mat.value = START_MATRIX
        

    ###  callback functions ###
    def evaluate(self): # evaluated once every frame if any input field has changed
    
        self.lf_time = time.time() # save absolute time of last frame (required for frame-rate independent mapping)
            
        #print(len(self.mf_pick_result.value))
        if len(self.mf_pick_result.value) > 0: # intersection found
            ## compute gravity response
            _pick_result = self.mf_pick_result.value[0] # get first intersection target from list

            _distance = _pick_result.Distance.value # distance from ray matrix to intersection point
            _distance -= 0.025 # subtract half avatar height from distance
            _distance -= self.fall_velocity

            if _distance > 0.01: # avatar above ground
                self.fall_vec.y = self.fall_velocity * -1.0

            else: # avatar (almost) on ground
                self.fall_vec.y = 0.0
            
            #print(self.fall_vec)

            self.sf_modified_mat.value = \
                avango.gua.make_trans_mat(self.fall_vec) * \
                self.sf_mat.value                
            
        else: # no intersection found
            self.sf_modified_mat.value = self.sf_mat.value # no changes needed
            
