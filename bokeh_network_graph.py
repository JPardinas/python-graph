import networkx as nx
import numpy as np

from bokeh import events
from bokeh.io import curdoc
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, Range1d, HoverTool, GraphRenderer, Oval, LabelSet, StaticLayoutProvider, Circle, TapTool, CustomJS, MultiLine, NodesAndLinkedEdges, Arrow, NormalHead, DataTable, TableColumn, StringEditor, IntEditor, NumberEditor
from bokeh.models.graphs import from_networkx
from bokeh.models.widgets import TextInput, Button, Paragraph, Div
from bokeh.layouts import layout, column, row
from bokeh.palettes import Spectral8
from bokeh import events


# Prepare Initial Data
## Constants for strings
TEXT_INPUT_DEFAULT_NEW_NODE = "Write new node letter..."
TEXT_INPUT_DEFAULT_ADD_EDGE = "Write node id"
TEXT_INPUT_DEFAULT_DELETE_EDGE = "Write node id"
BUTTON_DEFAULT_CREATE_NEW_NODE = "Create New Node"
BUTTON_DEFAULT_SET_NEW_EDGE = "Set new Edge"
BUTTON_DEFAULT_DELETE_EDGE = "Delete Edge"
BUTTON_DEFAULT_DELETE_NODE = "Delete Selected Nodes"

## Nodes
START_COLOR = '#3288bd'
nodes_letters = ['A','B','C','D']
N = len(nodes_letters)
nodes_colors = [START_COLOR] * N
nodes_keys = list(range(N))

## Initial Positions
divisor = 16
circ = [i*2*np.pi/divisor for i in nodes_keys]
x = [np.cos(i) for i in circ]
y = [np.sin(i) for i in circ]
node_coordinates = dict(zip(nodes_keys, zip(x, y)))
source_nodes_data=dict(index=nodes_keys, letter=nodes_letters, color=nodes_colors, x=x, y=y)

## Edges && Arrows
initial_edges_start = [0,0,0,1]
initial_edges_end = [1,2,3,2]
source_edges_data=dict(start=initial_edges_start, end=initial_edges_end)
x_start_edge = []
x_end_edge = []
y_start_edge = []
y_end_edge = []
edge_slope = []
for key in node_coordinates:
    x_start_edge.append(node_coordinates[source_edges_data['start'][key]][0])
    x_end_edge.append(node_coordinates[source_edges_data['end'][key]][0])
    y_start_edge.append(node_coordinates[source_edges_data['start'][key]][1])
    y_end_edge.append(node_coordinates[source_edges_data['end'][key]][1])
    edge_slope.append(np.arctan2(y_end_edge[key]-y_start_edge[key],x_end_edge[key]-x_start_edge[key]))

source_arrows=ColumnDataSource(dict(start=initial_edges_start, end=initial_edges_end, x_start=x_start_edge, x_end=x_end_edge, y_start=y_start_edge, y_end=y_end_edge, slope=edge_slope))
## Variables for interactions
selectionIndex = 0
node_selected = False



# Plot
## Plot Creation
plot = figure(title="Directed Graph", x_range=(-2,2), y_range=(-2,2),
              tools=['box_select','pan','wheel_zoom','box_zoom','reset','save'], toolbar_location='right')
plot.toolbar.logo=None
# Graph render
## Graph render creation
graph = GraphRenderer()
plot.grid.visible = False

## Set data to the render
graph.node_renderer.data_source.data = source_nodes_data
graph.edge_renderer.data_source.data = source_edges_data
source_nodes=graph.node_renderer.data_source
source_edges=graph.edge_renderer.data_source

## Graph layout
graph_layout = dict(zip(nodes_keys, zip(x, y)))
graph.layout_provider = StaticLayoutProvider(graph_layout=graph_layout)

# Arrows
#arrows = Arrow(end=NormalHead(size=.01*1000),x_start="x_start",y_start="y_start",x_end="x_end",y_end="y_end",source=source_arrows)
#plot.add_layout(arrows)


## Glyph Styles
graph.node_renderer.glyph = Circle(size=30, fill_color='color')
#graph.node_renderer.selection_glyph = Circle(radius=30,fill_alpha=.5)
graph.node_renderer.hover_glyph = Circle(radius=30,fill_color='black')
graph.edge_renderer.glyph = MultiLine(line_color="#CCCCCC",line_alpha=1, line_width=5)
graph.edge_renderer.selection_glyph = MultiLine(line_color='blue', line_width=5)
graph.edge_renderer.hover_glyph = MultiLine(line_color='blue', line_width=5)

## Graph Policy & Append
graph.selection_policy = NodesAndLinkedEdges()
graph.inspection_policy = NodesAndLinkedEdges()
plot.renderers.append(graph)

## Plot Styling
hover1=HoverTool(tooltips=[("Id","@index"),("Letter","@letter")])
#hover2=HoverTool(tooltips=[("Edges","@end")])
tap=TapTool()
plot.add_tools(hover1)
plot.add_tools(tap)


# Functions
## Updates console and Log
counter = 0
def update_console_and_log(text):
    global counter
    counter = counter + 1
    output_log.text = output_log.text + "________________Action" + str(counter) + " ________________"
    output_log.text = output_log.text +  text
    output_console = text
## Sets coordinates and updates layout
def updateGraphNodeRenderer(is_delete=False):
    global divisor, x_start_edge, x_end_edge, y_start_edge, y_end_edge, edge_slope
    ## Set new divisor for positions and size for circles if the length grows
    if is_delete is True:
        if divisor != 16 and divisor > len(nodes_keys):
            divisor = divisor / 2
            graph.node_renderer.glyph.size = graph.node_renderer.glyph.size*2
    else:
        if divisor < len(nodes_keys):
            divisor = divisor * 2
            graph.node_renderer.glyph.size = graph.node_renderer.glyph.size/2

    ## Calculate new coordinates
    circ = [idx*2*np.pi/divisor for idx, i in enumerate(nodes_keys)]
    x = [np.cos(i) for i in circ]
    y = [np.sin(i) for i in circ]

    node_coordinates = dict(zip(nodes_keys, zip(x, y)))
    ## Set new dictionary
    graph.layout_provider.graph_layout = node_coordinates
    graph.node_renderer.data_source.data=dict(index=nodes_keys, letter=nodes_letters, color=nodes_colors, x=x, y=y)

## Create a new node
def createNode():
    new_key = 0
    for key in nodes_keys:
        if key >= new_key : new_key = key + 1

    new_title = text_input_new_node_letter.value
    nodes_keys.append(new_key)
    nodes_letters.append(new_title)
    nodes_colors.append(START_COLOR)
    updateGraphNodeRenderer()

## Delete selected node
def deleteNodeSelected():
    global nodes_keys, nodes_letters, nodes_colors
    ## Selection Index
    selectionIndex=source_nodes.selected.indices[0]
    objectIndexList= []
    ## Update list
    for index in source_nodes.selected.indices:
        objectIndexList.append(source_nodes.data['index'][index])
    ## Delete all items selected
    for objectIndex in objectIndexList:
        ## Delete edges
        source_edges.data={key:[value for i, value in enumerate(source_edges.data[key]) if (source_edges.data["start"][i]==objectIndex or source_edges.data["end"][i]==objectIndex) is False] for key in source_edges.data}
        ## Delete nodes
        source_nodes.data={key:[value for i, value in enumerate(source_nodes.data[key]) if source_nodes.data["index"][i]!=objectIndex] for key in source_nodes.data}
        ## Delete arrows
        #source_arrows.data={key:[value for i, value in enumerate(source_arrows.data[key]) if (source_arrows.data["start"][i]==objectIndex or source_arrows.data["end"][i]==objectIndex) is False] for key in source_arrows.data}

    ## Set new graph
    nodes_keys = source_nodes.data['index']
    nodes_letters = source_nodes.data['letter']
    nodes_colors = source_nodes.data['color']
    updateGraphNodeRenderer(is_delete=True)
    graph.node_renderer.data_source.data=dict(index=nodes_keys, letter=nodes_letters, color=nodes_colors)

## Delete edge from selected node
def deleteEdgeFromNodeSelected():
    ## Selection Index
    selectionIndex=source_nodes.selected.indices[0]
    objectIndexed=source_nodes.data['index'][selectionIndex]
    try:
        node_to_remove_edge = int(text_input_delete_edge.value)

        if node_to_remove_edge not in graph.node_renderer.data_source.data['index']:
            update_console_and_log('That node id does not exists')
        elif objectIndexed == node_to_remove_edge:
            update_console_and_log('You are trying to remove and edge from the same node id')
        else:
            edge_exist = False
            for x in range(len(graph.edge_renderer.data_source.data['start'])):
                if graph.edge_renderer.data_source.data['start'][x] == objectIndexed and graph.edge_renderer.data_source.data['end'][x] == node_to_remove_edge:
                    edge_exist = True
                    initial_edges_start.pop(x)
                    initial_edges_end.pop(x)
                    break

            if edge_exist is True:
                graph.edge_renderer.data_source.data = dict(start=initial_edges_start, end=initial_edges_end)
            else:
                update_console_and_log('That edge not exists')

    except Exception as e:
        update_console_and_log('You must enter the id of the node')


## Sets a new edge
def setEdgeForNodeSelected():
    ## Selection Index
    selectionIndex=source_nodes.selected.indices[0]
    objectIndexed=source_nodes.data['index'][selectionIndex]
    try:
        node_to_connect = int(text_input_add_edge.value)
        not_exist_yet = True
        if node_to_connect not in graph.node_renderer.data_source.data['index']:
            update_console_and_log('That node id does not exists')
        elif objectIndexed == node_to_connect:
            update_console_and_log('You are trying to edge the same node id')
        else:
            for x in range(len(graph.edge_renderer.data_source.data['start'])):
                if graph.edge_renderer.data_source.data['start'][x] == objectIndexed and graph.edge_renderer.data_source.data['end'][x] == node_to_connect:
                    not_exist_yet = False
                    break

            if not_exist_yet is True:
                initial_edges_start.append(objectIndexed)
                initial_edges_end.append(node_to_connect)
                graph.edge_renderer.data_source.data = dict(start=initial_edges_start, end=initial_edges_end)
            else:
                update_console_and_log('That edge already exists')

    except Exception as e:
        update_console_and_log('You must enter the id of the node')


## New node method
def newNode():
    if text_input_new_node_letter.value != TEXT_INPUT_DEFAULT_NEW_NODE:
        update_console_and_log("Creating node: " + text_input_new_node_letter.value)
        createNode()
    else:
        update_console_and_log("You must enter a node Letter")

## Delete node method
def deleteNode():
    global node_selected
    if node_selected is True:
        deleteNodeSelected()
    else:
        update_console_and_log('There is not node selected')

## Set Edge method
def setEdge():
    global node_selected
    if node_selected is True:
        if text_input_add_edge.value != TEXT_INPUT_DEFAULT_ADD_EDGE:
            update_console_and_log("Setting edge to " + text_input_add_edge.value)
            setEdgeForNodeSelected()
        else:
            update_console_and_log("You must enter the node id")
    else:
        update_console_and_log('There is not node selected')

## Delete edge method
def deleteEdge():
    global node_selected
    if node_selected is True:
        if text_input_delete_edge.value != TEXT_INPUT_DEFAULT_DELETE_EDGE:
            update_console_and_log("Deleting edge " + text_input_delete_edge.value)
            deleteEdgeFromNodeSelected()
        else:
            update_console_and_log("You must enter the node id")
    else:
        update_console_and_log('There is not node selected')


## Select node method
def callback(attrname, old, new):
    global node_selected, selectionIndex
    try:
        selectionIndex=graph.node_renderer.data_source.selected.indices[0]
        node_selected=True
    except Exception as e:
        node_selected=False

## Callback Setters
graph.node_renderer.data_source.selected.on_change('indices', callback)



# Web Page
## Widgets
text_input_new_node_letter=TextInput(value=TEXT_INPUT_DEFAULT_NEW_NODE)
text_input_add_edge=TextInput(value=TEXT_INPUT_DEFAULT_ADD_EDGE)
text_input_delete_edge=TextInput(value=TEXT_INPUT_DEFAULT_DELETE_EDGE)
button_create_new_node=Button(label=BUTTON_DEFAULT_CREATE_NEW_NODE)
button_set_new_edge=Button(label=BUTTON_DEFAULT_SET_NEW_EDGE)
button_delete_edge=Button(label=BUTTON_DEFAULT_DELETE_EDGE)
button_delete_node=Button(label=BUTTON_DEFAULT_DELETE_NODE)
output_console=Paragraph()
output_log=Paragraph()
labels = LabelSet(x='x', y='y', text='letter', source=graph.node_renderer.data_source,
                  x_offset=-5, y_offset=-9, text_color='white',
                  background_fill_alpha=1)
div_log = Div(text="""Log""", width=300, height=100)
div_console = Div(text="""Console""", width=300, height=100)

## Set widgets properties
button_create_new_node.on_click(newNode)
button_delete_node.on_click(deleteNode)
button_set_new_edge.on_click(setEdge)
button_delete_edge.on_click(deleteEdge)

## Append
plot.renderers.append(labels)



#Adjacency Matrix
adjMatrix = []
size = len(graph.node_renderer.data_source.data['index'])
for i in range(size):
    adjMatrix.append([0 for i in range(size)])

letter_columns = [
    TableColumn(field = 'letter', title = " ", editor = StringEditor(), name = 'left_column')]

data_columns = [
    TableColumn(field = 'letter', title = "A", editor = StringEditor(), name = 'left_column')]

data_table_column_left_letters = DataTable(source = graph.node_renderer.data_source, width = 25, height = 80, columns = letter_columns, header_row=True, index_position=None)
data_table_column_a = DataTable(source = graph.node_renderer.data_source, width = 25, height = 80, columns = data_columns, header_row=True, index_position=None)
data_table_column_left_letters.height = 2000
data_table_column_a.height = 2000


# Final Layout
row_create_node = row([button_create_new_node, text_input_new_node_letter])
row_add_edge = row([button_set_new_edge, text_input_add_edge])
row_delete_edge = row([button_delete_edge, text_input_delete_edge])


row_table = row([data_table_column_left_letters,data_table_column_a])



left_column=column([div_log, output_log])
mid_column=column([row_create_node, row_add_edge, row_delete_edge, button_delete_node,plot,row_table])
right_column=column([div_console, output_console])
row = row([left_column, mid_column, right_column])

curdoc().add_root(row)
