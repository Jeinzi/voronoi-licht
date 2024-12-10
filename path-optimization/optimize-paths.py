#!/usr/bin/env python3
# https://developers.google.com/optimization/routing/tsp
#
# This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.

import sys
import math
from lxml import etree
from copy import deepcopy
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

def compute_euclidean_distance_matrix(locations):
    """Creates callback to return distance between points."""
    distances = {}
    for from_counter, from_node in enumerate(locations):
        distances[from_counter] = {}
        for to_counter, to_node in enumerate(locations):
            if from_counter == to_counter:
                distances[from_counter][to_counter] = 0
            else:
                # Euclidean distance
                distances[from_counter][to_counter] = (int(
                    10*math.hypot((from_node[0] - to_node[0]),
                               (from_node[1] - to_node[1]))))
    return distances


def build_route_array(manager, routing, solution):
    index = routing.Start(0)
    route_distance = 0
    route = []
    while not routing.IsEnd(index):
        route.append(manager.IndexToNode(index))
        previous_index = index
        index = solution.Value(routing.NextVar(index))
        route_distance += routing.GetArcCostForVehicle(previous_index, index, 0)
    #print('Objective: {}\n'.format(route_distance))
    return route



def calc_route_length(locations, route):
  pass



if __name__ == "__main__":
  if len(sys.argv) <= 1:
    print("Please supply the path to an SVG file.")
    exit()

  filename = sys.argv[1]
  with open(filename, 'r') as f:
    tree = etree.parse(f)
  data = {}
  data['num_vehicles'] = 1
  data['depot'] = 0

  svg_groups = ["side0", "side1", "side2", "side3"]
  for group_name in svg_groups:
    print(f"{group_name}:")
    data['locations'] = []
    elements = []
    unoptimized_distance = 0
    prev_pos = None
    group = tree.find(f".//*[@id='{group_name}']")
    color_error = 0
    for element in group.getchildren():
      if element.tag.split("}")[1] == "path":
        # Check for strokes that are not red and correct them.
        style = element.get("style")
        if style.find("stroke:#ff0000") == -1:
          color_error += 1
          search_text = "stroke:#"
          stroke_pos = style.find(search_text)
          style = style[:stroke_pos] + search_text + "ff0000" + style[stroke_pos+14:]
          element.set("style", style)

        # CSS styles have precedence over XML attributes and Inkscape
        # doesn't seem to correct the latter at all -> delete them.
        etree.strip_attributes(element, "stroke")
        etree.strip_attributes(element, "stroke-width")

        # Get start locations of cutouts.
        d = element.get("d")
        s = d.split(" ")
        if s[0] != "m" and s[0] != "M":
          raise Exception
        pos = tuple(float(i) for i in s[1].split(","))
        #print(f"{element.get('id')}: {pos}")
        data["locations"].append(pos)
        elements.append(deepcopy(element))
        element.getparent().remove(element)
        if prev_pos:
          dx = pos[0] - prev_pos[0]
          dy = pos[1] - prev_pos[1]
          unoptimized_distance += math.sqrt(dx**2 + dy**2)
        prev_pos = pos
    if color_error != 0:
      print(f"  Corrected {color_error} color errors.")
    print(f"  {unoptimized_distance=:.2f}")
    # Create the routing index manager.
    manager = pywrapcp.RoutingIndexManager(len(data['locations']), data['num_vehicles'], data['depot'])

    # Create Routing Model.
    routing = pywrapcp.RoutingModel(manager)
    distance_matrix = compute_euclidean_distance_matrix(data['locations'])

    def distance_callback(from_index, to_index):
      """Returns the distance between the two nodes."""
      # Convert from routing variable Index to distance matrix NodeIndex.
      from_node = manager.IndexToNode(from_index)
      to_node = manager.IndexToNode(to_index)
      return distance_matrix[from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)

    # Define cost of each arc.
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
    search_parameters.local_search_metaheuristic = (
      routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
    search_parameters.time_limit.seconds = 10
    #search_parameters.log_search = True

    # Solve the problem.
    solution = routing.SolveWithParameters(search_parameters)

    # Print solution on console.
    if solution:
      route = build_route_array(manager, routing, solution)
      group = tree.find(f".//*[@id='{group_name}']")
      prev_pos = 0
      optimized_distance = 0
      for node in route:
        group.append(elements[node])
        pos = data["locations"][node]
        if prev_pos:
          dx = pos[0] - prev_pos[0]
          dy = pos[1] - prev_pos[1]
          optimized_distance += math.sqrt(dx**2 + dy**2)
        prev_pos = pos
      filenameOptimized = filename.replace(".svg", "-opt.svg")
      print(f"  {optimized_distance=:.2f}")
      print(f"  Speedup: {unoptimized_distance/optimized_distance:.2f}x")
    else:
      print("  no solution")
  tree.write(filenameOptimized)
