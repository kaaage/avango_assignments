#!/usr/bin/python

### import guacamole libraries
import avango
import avango.gua

### import application libraries
from lib.SimpleViewingSetup import *
from lib.SolarSystem import SolarSystem
from lib.Device import *
from lib.Navigation import SteeringNavigation


### global variables ###
#NAVIGATION_MODE = "Spacemouse"
NAVIGATION_MODE = "New Spacemouse"
#NAVIGATION_MODE = "Keyboard"


def start():

    ## init scenegraph
    scenegraph = avango.gua.nodes.SceneGraph(Name = "scenegraph")
    
    ## init solar system
    solarSystem = SolarSystem()
    solarSystem.my_constructor(scenegraph.Root.value)

    ## init navigation technique
    steeringNavigation = SteeringNavigation()
    steeringNavigation.set_start_transformation(avango.gua.make_trans_mat(0.0,0.1,0.3)) # move camera to initial position
  
    if NAVIGATION_MODE == "Spacemouse":
        deviceInput = SpacemouseInput()
        deviceInput.my_constructor("gua-device-spacemouse")
        
        steeringNavigation.my_constructor(deviceInput.mf_dof, deviceInput.mf_buttons, 0.15, 1.0) # connect navigation with spacemouse input
        
    elif NAVIGATION_MODE == "New Spacemouse":
        deviceInput = NewSpacemouseInput()
        deviceInput.my_constructor("gua-device-spacemouse")
            
        steeringNavigation.my_constructor(deviceInput.mf_dof, deviceInput.mf_buttons, 0.1, 1.0) # connect navigation with spacemouse input

    elif NAVIGATION_MODE == "Keyboard":
        deviceInput = KeyboardInput()
        deviceInput.my_constructor("gua-device-keyboard0")

        steeringNavigation.my_constructor(deviceInput.mf_dof, deviceInput.mf_buttons) # connect navigation with keyboard input

    else:    
        print("Error: NAVIGATION_MODE " + NAVIGATION_MODE + " is not known.")
        return


    ## init viewing setup    
    viewingSetup = SimpleViewingSetup(scenegraph, "mono", False)
    #viewingSetup = SimpleViewingSetup(scenegraph, "anaglyph", False)
    viewingSetup.connect_navigation_matrix(steeringNavigation.sf_nav_mat)
    steeringNavigation.set_rotation_center_offset(viewingSetup.get_head_position())

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

