#!/usr/bin/python

### import guacamole libraries
import avango
import avango.gua

### import application libraries
from lib.ViewingSetup import StereoViewingSetup
from lib.MultiUserViewingSetup import MultiUserViewingSetup
from lib.Scene import Scene
from lib.Device import NewSpacemouseInput
from lib.Device import KeyboardInput
from lib.Navigation import SteeringNavigation
from lib.Manipulation import ManipulationManager
from lib.LeapSensor import LeapSensor

def start():


    ## create scenegraph
    scenegraph = avango.gua.nodes.SceneGraph(Name = "scenegraph")

    ## init scene
    scene = Scene(SCENEGRAPH = scenegraph, PARENT_NODE = scenegraph.Root.value)


    ## init navigation technique
    deviceInput = NewSpacemouseInput()
    deviceInput.my_constructor("gua-device-spacemouse")
        
    steeringNavigation = SteeringNavigation()
    steeringNavigation.my_constructor(deviceInput.mf_dof, deviceInput.mf_buttons, 0.15, 1.0) # connect navigation with spacemouse input
    steeringNavigation.set_start_matrix(avango.gua.make_trans_mat(-2.1, 0.96, 0.705))

    ## init viewing setup
    ## init viewing and interaction setups
    hostname = open('/etc/hostname', 'r').readline()
    hostname = hostname.strip(" \n")
    
    print("wokstation:", hostname)

    if hostname == "medusa": # Samsung 3D-TV workstation
        _tracking_transmitter_offset = avango.gua.make_trans_mat(-2.1, 0.96, 0.705) * avango.gua.make_rot_mat(90.0, 0, 1, 0) * avango.gua.make_rot_mat(90.0, -1, 0, 0) # transformation into tracking coordinate system

        viewingSetup = MultiUserViewingSetup(
            SCENEGRAPH = scenegraph,
            WINDOW_RESOLUTION = avango.gua.Vec2ui(1400, 1050),
            SCREEN_DIMENSIONS = avango.gua.Vec2(1.135, 0.85),
            SCREEN_MATRIX = avango.gua.make_trans_mat(-(0.525+1.61), 0.96, 0.72) * avango.gua.make_rot_mat(90.0, 0, 1, 0) * avango.gua.make_rot_mat(90.0, -1, 0, 0),
            #SCREEN_MATRIX = avango.gua.make_trans_mat(-2.1, 0.96, 0.705) * avango.gua.make_rot_mat(90.0, 0, 1, 0) * avango.gua.make_rot_mat(90.0, -1, 0, 0),
            # TRACKING_TRANSMITTER_OFFSET = _tracking_transmitter_offset,
            LEFT_POSITION = avango.gua.Vec2ui(0, 0),
            LEFT_RESOLUTION = avango.gua.Vec2ui(1400, 1050),
            RIGHT_POSITION = avango.gua.Vec2ui(1400, 0),
            RIGHT_RESOLUTION = avango.gua.Vec2ui(1400, 1050),
            DISPLAY_STRING_LIST = [[":0.0"], [":0.1"], [":0.2"]], # 3 user slots (left and right eye on same GPU)
            # STEREO_FLAG = True,
            # STEREO_MODE = avango.gua.StereoMode.SIDE_BY_SIDE,
            WARP_MATRIX_RED_RIGHT = "/opt/3D43-warpmatrices/3D43_warp_P1.warp",
            WARP_MATRIX_GREEN_RIGHT = "/opt/3D43-warpmatrices/3D43_warp_P2.warp",
            WARP_MATRIX_BLUE_RIGHT = "/opt/3D43-warpmatrices/3D43_warp_P3.warp",
            WARP_MATRIX_RED_LEFT = "/opt/3D43-warpmatrices/3D43_warp_P1.warp",
            WARP_MATRIX_GREEN_LEFT = "/opt/3D43-warpmatrices/3D43_warp_P2.warp",
            WARP_MATRIX_BLUE_LEFT = "/opt/3D43-warpmatrices/3D43_warp_P3.warp",
            )
     ## init navigation technique
        keyboardInput = KeyboardInput()
        keyboardInput.my_constructor("gua-device-keyboard1")

        steeringNavigation = SteeringNavigation()
        steeringNavigation.my_constructor(keyboardInput.mf_dof, keyboardInput.mf_buttons) # connect steering navigation with keyboard input

        viewingSetup.init_user(HEADTRACKING_SENSOR_STATION = "tracking-dlp-glasses-3")
        viewingSetup.init_user(HEADTRACKING_SENSOR_STATION = "tracking-dlp-glasses-2")
        viewingSetup.init_user(HEADTRACKING_SENSOR_STATION = "tracking-dlp-glasses-1")

        manipulation_manager = ManipulationManager()
        manipulation_manager.my_constructor(PARENT_NODE = viewingSetup.navigation_node, SCENE_ROOT = scenegraph.Root.value, TARGET_LIST = scene.target_list)

        # manipulationManager = ManipulationManager()
        # manipulationManager.my_constructor(
        #     SCENEGRAPH = scenegraph,
        #     NAVIGATION_NODE = viewingSetup.navigation_node,
        #     POINTER_TRACKING_STATION = "tracking-pst-pointer-1",
        #     TRACKING_TRANSMITTER_OFFSET = _tracking_transmitter_offset,
        #     POINTER_DEVICE_STATION = "device-pointer-1",
        #     HEAD_NODE = viewingSetup.head_node,            
        #     )
            
    else:
        print("No Viewing Setup available for this workstation")
        quit()

    # viewingSetup.connect_navigation_matrix(steeringNavigation.sf_nav_mat)
    # steeringNavigation.set_rotation_center_offset(viewingSetup.get_head_position())

    print_graph(scenegraph.Root.value)

    # leap = LeapSensor()LD_PRELOAD=./libLeap.so python3.5 Sample.py
    # leap.my_constructor(SCENE = scene, SCENEGRAPH = scenegraph, TRACKING_TRANSMITTER_OFFSET = _tracking_transmitter_offset)

    ## start application/render loop
    viewingSetup.run(locals(), globals())


### helper functions ###

## print the subgraph under a given node to the console
def print_graph(root_node):
  stack = [(root_node, 0)]
  while stack:
    node, level = stack.pop()
    print("│   " * level + "├── {0} <{1}>".format(
      node.Name.value, node.__class__.__name__))
    stack.extend(
      [(child, level + 1) for child in reversed(node.Children.value)])

## print all fields of a fieldcontainer to the console
def print_fields(node, print_values = False):
  for i in range(node.get_num_fields()):
    field = node.get_field(i)
    print("→ {0} <{1}>".format(field._get_name(), field.__class__.__name__))
    if print_values:
      print("  with value '{0}'".format(field.value))


if __name__ == '__main__':
  start()

