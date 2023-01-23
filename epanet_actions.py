from epanet import toolkit
import math
import logging as log

"""
module for all actions that relate to the epanet project 
or use the project handle (ph
"""

LEAK_ID = "leak_id"
UP_ID = "upstream_id"
DOWN_ID = "downstream_id"
log.basicConfig(level=log.DEBUG)


# class dealing with all actions that directly handle the simulations
class ProjectActions:

    def __init__(self, ph, use_elev):
        self.nodes = None
        self.pipes = None
        self.distance = None
        self.numleaks = None

        self.trig = None
        self.orig_prop = None
        self.downstream_node_index = None
        self.upstream_node_index = None
        self.pipe_index = None
        self.network_units = None
        self.ph = ph
        self.use_elev = use_elev

    # initializes the project using input arguments (args)
    def initialize_subsys(self, args):
        log.debug('initializing subsys')
        toolkit.open(self.ph, args.input_filename, args.report_filename, args.binary_filename)
        toolkit.settimeparam(self.ph, toolkit.HYDSTEP, args.hstep)
        toolkit.setstatusreport(self.ph, toolkit.NORMAL_REPORT)

        log.debug('setting flow units')
        network_units = NetworkUnits(toolkit.getflowunits(self.ph))
        toolkit.setflowunits(self.ph, network_units.flow_index)

        self.network_units = network_units
        self.pipe_index = args.pipe

        try:
            self.distance = args.lstep
            self.numleaks = args.nleaks
        except:
            self.distance = 0
            self.numleaks = 1

    def run_hydraulic_solver(self):
        toolkit.openH(self.ph)
        toolkit.initH(self.ph, toolkit.NOSAVE)
        toolkit.solveH(self.ph)

    # records all info needed to create a leakage suite, then creates that suite
    def add_leakage_suite(self):
        log.debug('getting nodes surrounding pipe w/ index %s' % self.pipe_index)
        self.upstream_node_index, self.downstream_node_index = toolkit.getlinknodes(self.ph, self.pipe_index)
        log.debug('saving properties of original pipe')
        self.orig_prop = LinkProperties(self.ph, self.pipe_index)

        log.debug('initializing trigonometry tools with upstream node %s, downstream node %s and length %s' % (
            self.upstream_node_index, self.downstream_node_index, self.orig_prop.length))
        self.trig = TrigonometryTools(self.ph, self.upstream_node_index, self.downstream_node_index,
                                      self.orig_prop.length)

        log.debug('deleting original pipe')
        toolkit.deletelink(self.ph, self.pipe_index, actionCode=toolkit.UNCONDITIONAL)

        self.create_leakage_suite()

    def create_leakage_suite(self):
        # handles nodes and pipes as arrays so that any number of leaks can be modelled using the same function
        # nodes contains only leakage nodes, while node_ids also contain the ids of the surrounding nodes
        # there's one more pipe than there are nodes because there needs to be a pipe on either side
        self.nodes = [0] * self.numleaks
        node_ids = [''] * (self.numleaks + 2)
        self.pipes = [0] * (self.numleaks + 1)

        # sets first and last node ids to the surrounding nodes (which already exist)
        node_ids[0] = toolkit.getnodeid(self.ph, self.upstream_node_index)
        node_ids[-1] = toolkit.getnodeid(self.ph, self.downstream_node_index)

        # create all new leakage nodes and pipes
        for i in range(self.numleaks):
            node_id = "ln_%s" % i
            self.nodes[i] = toolkit.addnode(self.ph, node_id, nodeType=toolkit.JUNCTION)
            node_ids[i + 1] = node_id

        for i in range(self.numleaks + 1):
            self.pipes[i] = self.make_pipe("pipe_%s" % i, node_ids[i], node_ids[i + 1], self.orig_prop, self.distance)

    def make_pipe(self, pipe_id, start_node, end_node, properties, std_length):
        # sets the length of the pipe to 1 even if user set it to less than 1,
        # because less than 1 is not allowed by epanet
        if std_length < 1:
            std_length = 1
        pipe_index = toolkit.addlink(self.ph, pipe_id, toolkit.PIPE, start_node, end_node)
        toolkit.setpipedata(self.ph, pipe_index, length=std_length, diam=properties.diam, rough=properties.rough,
                            mloss=properties.mloss)
        return pipe_index

    # different functions for moving one and many leaks
    def move_one_leak_along_transect(self, leak_base, iterations):
        pipe_length = toolkit.getlinkvalue(self.ph, self.pipe_index, toolkit.LENGTH)
        results = [""] * round(pipe_length + 1)

        # handles writing the two header rows
        results[0] = ","
        results[1] = 'leakage_position ({}),'.format(self.network_units.length)
        for i in range(iterations):
            results[0] = results[0] + 'leak_coeff: %s,,,' % (leak_base * (i + 1))
            results[1] = results[
                             1] + 'upstream_pressure ({0}),downstream_pressure ({0}),upstream_flow ({1}),' \
                                  'downstream_flow ({1})'.format(
                self.network_units.pressure, self.network_units.flow)

            # prints commas at the end of each iteration except the last one, for correct csv formatting
            if i != iterations - 1:
                results[0] = results[0] + ","
                results[1] = results[1] + ","

        # writes the results. i starts at 1 because it's the distance from the start of the pipe, and that distance
        # must be at least 1 according to epanet
        for i in range(1, round(pipe_length)):
            index = i + 1  # leaves room for two headers at the top of results
            results[index] = "{},".format(i)

            for j in range(iterations):
                leak_coeff = leak_base * (j + 1)
                result_values = self.simulate_leaks(leak_coeff, pipe_length, i)
                results[index] = results[index] + "{},{},{},{}".format(result_values.up_p, result_values.down_p,
                                                                       result_values.up_f, result_values.down_f)
                # adds comma at the end of each iteration except the last
                if j != iterations - 1:
                    results[index] = results[index] + ","

        return results

    def move_several_leaks_along_transect(self, leak_coeff):
        pipe_length = toolkit.getlinkvalue(self.ph, self.pipe_index, toolkit.LENGTH)
        numresults = round(pipe_length) - (self.distance * (self.numleaks - 1) + 1)
        results = [""] * (numresults + 2)

        # writes two header rows
        results[0] = 'distance_between_leaks: {0} {1}, number_of_leaks: {2}' \
            .format(self.distance, self.network_units.length, self.numleaks)
        results[1] = 'first_leak_position({0}),upstream_pressure ({1}),downstream_pressure ({1}),' \
                     'upstream_flow ({2}),downstream_flow ({2})' \
            .format(self.network_units.length, self.network_units.pressure, self.network_units.flow)

        for i in range(numresults):
            index = i + 2
            result_values = self.simulate_leaks(leak_coeff, pipe_length, i + 1)
            results[index] = '{},'.format(result_values.location)
            results[index] = results[index] + "{},{},{},{}".format(result_values.up_p, result_values.down_p,
                                                                   result_values.up_f, result_values.down_f)

        return results

    # works with both single and multiple leaks
    def simulate_leaks(self, leak_coeff, pipe_length, length_to_first_node):
        length_of_suite = self.distance * (self.numleaks - 1)
        length_to_middle = length_to_first_node + (length_of_suite / 2)
        length_after_last_node = pipe_length - (length_to_first_node + length_of_suite)
        # set new lengths of surrounding pipes
        toolkit.setpipedata(self.ph, self.pipes[0], length=length_to_first_node, diam=self.orig_prop.diam,
                            rough=self.orig_prop.rough, mloss=self.orig_prop.mloss)
        toolkit.setpipedata(self.ph, self.pipes[-1], length=length_after_last_node, diam=self.orig_prop.diam,
                            rough=self.orig_prop.rough, mloss=self.orig_prop.mloss)

        for node in self.nodes:
            if self.use_elev:
                leak_elev = self.trig.calculate_node_elevation(length_to_first_node)
                toolkit.setnodevalue(self.ph, self.nodes[0], toolkit.ELEVATION, leak_elev)
                # after this point length_to_first_node is actually the length to the next unread node
                length_to_first_node = length_to_first_node + self.distance
            toolkit.setnodevalue(self.ph, node, toolkit.EMITTER, leak_coeff)

        self.run_hydraulic_solver()

        return Results(self.ph, self.upstream_node_index, self.downstream_node_index, self.pipes[0],
                       self.pipes[-1], length_to_middle)


# class for handling the elevation of the leakage nodes
class TrigonometryTools:
    upstream_node_elevation = None
    angle = None

    """
    If [a] is upstream node and [b] is downstream node, __init__ uses the lengths of [ab]
    and [bc] (derived from the difference in height between [a] and [b] to calculate the angle of [a],
    which can then be used  (in calculate_node_elevation)to find the elevation on a new point anywhere 
    along the [ab] pipe.
    
    [a]* * * [c]
       *    |_*
          *   *
             [b]
    """
    def __init__(self, ph, upstream_node, downstream_node, pipe_length):
        upstream_node_elevation = toolkit.getnodevalue(ph, upstream_node, toolkit.ELEVATION)
        downstream_node_elevation = toolkit.getnodevalue(ph, downstream_node, toolkit.ELEVATION)
        elevation_diff = upstream_node_elevation - downstream_node_elevation

        self.upstream_node_elevation = upstream_node_elevation
        # arcsine gets angle from opposite/hypotenuse
        self.angle = math.asin(elevation_diff / pipe_length)

    def calculate_node_elevation(self, length_from_upper):
        # sine of angle returns opposite / hypotenuse, so we multiply results by hypotenuse to get just
        # opposite, which is the length from the upper node to the current node
        elevation_diff_from_upper_elevation = math.sin(self.angle) * length_from_upper
        return self.upstream_node_elevation - elevation_diff_from_upper_elevation


# class that determines the units used throughout the system
# so that the right unit names will be printed
class NetworkUnits:
    def __init__(self, flow_units):
        if 0 <= flow_units < 5:
            # US customary units
            self.flow_index = 1
            self.flow = 'gpm'
            self.pressure = 'psi'
            self.length = 'foot'
        elif 5 <= flow_units < 10:
            # SI metric units
            self.flow_index = 5
            self.flow = 'lps'
            self.pressure = 'm of head'
            self.length = 'm'
        else:
            raise IndexError


# value class that holds the parameters of a specified pipe
# in order to make this pipe replicable
class LinkProperties:
    def __init__(self, ph, index):
        self.length = toolkit.getlinkvalue(ph, index, toolkit.LENGTH)
        self.diam = toolkit.getlinkvalue(ph, index, toolkit.DIAMETER)
        self.rough = toolkit.getlinkvalue(ph, index, toolkit.ROUGHNESS)
        self.mloss = toolkit.getlinkvalue(ph, index, toolkit.MINORLOSS)


# value class that holds a single set of results
class Results:
    def __init__(self, ph, up_node_index, down_node_index, up_link_index, down_link_index, location):
        self.up_p = toolkit.getnodevalue(ph, up_node_index, toolkit.PRESSURE)
        self.down_p = toolkit.getnodevalue(ph, down_node_index, toolkit.PRESSURE)
        self.up_f = toolkit.getlinkvalue(ph, up_link_index, toolkit.FLOW)
        self.down_f = toolkit.getlinkvalue(ph, down_link_index, toolkit.FLOW)
        self.location = location
