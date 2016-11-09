import avango
import avango.gua
import avango.script
from avango.script import field_has_changed

from SimpleViewer import SimpleViewer

class TimedRotate(avango.script.Script):
  TimeIn = avango.SFFloat()
  MatrixOut = avango.gua.SFMatrix4()
  RotationSpeed = avango.SFFloat()

  def __init__(self):
    self.super(TimedRotate).__init__()
    self.RotationSpeed.value = 50.0

  @field_has_changed(TimeIn)
  def update(self):
    self.MatrixOut.value = avango.gua.make_rot_mat(self.TimeIn.value*self.RotationSpeed.value,
                                                   0.0, 1.0, 0.0)


viewer = SimpleViewer()
timed_rotate = TimedRotate()

def add_sample_monkey(graph):
  loader = avango.gua.nodes.TriMeshLoader()
  monkey = loader.create_geometry_from_file("another_monkey", "data/objects/monkey.obj", avango.gua.LoaderFlags.DEFAULTS)
  monkey.Material.value.set_uniform("ColorMap", "data/textures/stones.jpg")
  monkey.Transform.value = avango.gua.make_trans_mat(2, 1, 0) * avango.gua.make_rot_mat(90, 0, 1, 0) * avango.gua.make_scale_mat(0.5, 0.5, 0.5)
  graph.Root.value.Children.value.append(monkey)

def print_graph(graph):
  root_node = graph.Root.value
  stack = [(root_node, 0)]
  while stack:
    node, level = stack.pop()
    print("│   " * level + "├── {0} <{1}>".format(
      node.Name.value, node.__class__.__name__))
    stack.extend(
      [(child, level + 1) for child in reversed(node.Children.value)])

def build_end_of_tutorial_state():

  graph = avango.gua.nodes.SceneGraph(Name = 'scenegraph')
  viewer.SceneGraph.value = graph
  viewer.set_background_image('data/textures/checker.png')

  loader = avango.gua.nodes.TriMeshLoader()
  monkey_node = loader.create_geometry_from_file('monkey', 'data/objects/monkey.obj', avango.gua.LoaderFlags.DEFAULTS)
  monkey_node.Material.value.set_uniform("ColorMap", "data/textures/grass.jpg")
  monkey_node.Transform.connect_from(timed_rotate.MatrixOut)
  graph.Root.value.Children.value.append(monkey_node)

  lamp_node = avango.gua.nodes.LightNode(Type=avango.gua.LightType.SPOT, Name='lamp')
  lamp_node.Transform.value = avango.gua.make_trans_mat(0, 3, 0) * avango.gua.make_rot_mat(-90, 1, 0, 0) * avango.gua.make_scale_mat(55, 55, 30)
  graph.Root.value.Children.value.append(lamp_node)

  plane_node = loader.create_geometry_from_file('floor', 'data/objects/plane.obj', avango.gua.LoaderFlags.DEFAULTS)
  plane_node.Transform.value = avango.gua.make_trans_mat(0, -2, 0) * avango.gua.make_scale_mat(5, 1, 5)
  plane_node.Material.value.set_uniform("ColorMap", "data/textures/tiles.jpg")
  graph.Root.value.Children.value.append(plane_node)

  add_sample_monkey(graph)

  tea_move_node = avango.gua.nodes.TransformNode(Name = 'teaMove')
  tea_move_node.Transform.value = avango.gua.make_trans_mat(0, -1.85, 0)
  graph.Root.value.Children.value.append(tea_move_node)

  transform_node = avango.gua.nodes.TransformNode(Name = 'group')
  transform_node.Transform.connect_from(timed_rotate.MatrixOut)
  tea_move_node.Children.value.append(transform_node)

  pot1 = loader.create_geometry_from_file('pot1', 'data/objects/teapot.obj', avango.gua.LoaderFlags.DEFAULTS)
  pot1.Transform.value = avango.gua.make_trans_mat(2,  0, 0) * avango.gua.make_scale_mat(0.2, 0.2, 0.2)
  pot2 = loader.create_geometry_from_file('pot2', 'data/objects/teapot.obj', avango.gua.LoaderFlags.DEFAULTS)
  pot2.Transform.value = avango.gua.make_trans_mat(0,  0, 2) * avango.gua.make_scale_mat(0.2, 0.2, 0.2)
  pot3 = loader.create_geometry_from_file('pot3', 'data/objects/teapot.obj', avango.gua.LoaderFlags.DEFAULTS)
  pot3.Transform.value = avango.gua.make_trans_mat(-2,  0, 0) * avango.gua.make_scale_mat(0.2, 0.2, 0.2)
  transform_node.Children.value = [pot1, pot2, pot3]

  viewer.start_navigation()

def start():
  global timed_rotate

  timer = avango.nodes.TimeSensor()
  timed_rotate.TimeIn.connect_from(timer.Time)
  build_end_of_tutorial_state()

  logger = avango.gua.nodes.Logger(EnableWarning = True)

  viewer.run(locals(), globals(), False)

if __name__ == '__main__':
  start()

