from epanet import toolkit
import math
import logging as log

LEAK_ID = "leak_id"
UP_ID = "upstream_id"
DOWN_ID = "downstream_id"
log.basicConfig(level=log.DEBUG)


class ProjectActions:

    def __init__(self, ph, use_elev):
        self.downstream_pipe_index = None
        self.upstream_pipe_index = None
        self.leakage_node_index = None
        self.trig = None
        self.orig_prop = None
        self.downstream_node_index = None
        self.upstream_node_index = None
        self.pipe_index = None
        self.network_units = None
        self.ph = ph
        self.use_elev = use_elev

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

    def run_hydraulic_solver(self):
        toolkit.openH(self.ph)
        toolkit.initH(self.ph, toolkit.NOSAVE)
        toolkit.solveH(self.ph)

    def close_hydraulic_solver(self):
        toolkit.closeH(self.ph)
        toolkit.close(self.ph)

    def add_leak(self):
        log.debug('getting nodes surrounding pipe w/ index %s' % self.pipe_index)
        self.upstream_node_index, self.downstream_node_index = toolkit.getlinknodes(self.ph, self.pipe_index)
        log.debug('saving properties of original pipe')
        self.orig_prop = LinkProperties(self.ph, self.pipe_index)

        log.debug('initializing trigonometry tools with upstream node %s, downstream node %s and length %s' % (
            self.upstream_node_index, self.downstream_node_index, self.orig_prop.length))
        #upstream_e = toolkit.getnodevalue(self.ph, self.upstream_node_index, toolkit.ELEVATION)
        #downstream_e = toolkit.getnodevalue(self.ph, self.downstream_node_index, toolkit.ELEVATION)
        #self.trig = TrigonometryTools(upstream_e, downstream_e, self.orig_prop.length)
        self.trig = TrigonometryTools(self.ph, self.upstream_node_index, self.downstream_node_index,
                                      self.orig_prop.length)

        log.debug('deleting original pipe and adding leakage node')
        toolkit.deletelink(self.ph, self.pipe_index, actionCode=toolkit.UNCONDITIONAL)
        self.leakage_node_index = toolkit.addnode(self.ph, LEAK_ID, nodeType=toolkit.JUNCTION)

        self.upstream_pipe_index = self.make_pipe(UP_ID, toolkit.getnodeid(self.ph, self.upstream_node_index), LEAK_ID,
                                                  self.orig_prop)
        self.downstream_pipe_index = self.make_pipe(DOWN_ID, LEAK_ID,
                                                    toolkit.getnodeid(self.ph, self.downstream_node_index),
                                                    self.orig_prop)

    def make_pipe(self, id, start_node, end_node, properties):
        pipe_index = toolkit.addlink(self.ph, id, toolkit.PIPE, start_node, end_node)
        toolkit.setpipedata(self.ph, pipe_index, length=1, diam=properties.diam, rough=properties.rough,
                            mloss=properties.mloss)
        return pipe_index

    def move_leak_along_transect(self, leak_base, iterations):
        pipe_length = toolkit.getlinkvalue(self.ph, self.pipe_index, toolkit.LENGTH)
        results = [""] * round(pipe_length + 1)

        results[0] = ""
        results[1] = 'leakage_position ({}),'.format(self.network_units.length)
        for i in range(iterations):
            results[0] = results[0] + 'leak_coeff: %s,,,' % (leak_base * (i + 1))
            results[1] = results[
                             1] + 'upstream_pressure ({0}),downstream_pressure ({0}),upstream_flow ({1}),' \
                                  'downstream_flow ({1})'.format(
                self.network_units.pressure, self.network_units.flow)
            if i != iterations - 1:
                results[0] = results[0] + ","
                results[1] = results[1] + ","

        for i in range(1, round(pipe_length)):
            index = i + 1  # leaves room for two headers at the top of results
            results[index] = "{},".format(i)

            for j in range(iterations):
                leak_coeff = leak_base * (j + 1)
                result_values = self.simulate_leak(leak_coeff, i, pipe_length - i)
                results[index] = results[index] + "{},{},{},{}".format(result_values.up_p, result_values.down_p,
                                                                       result_values.up_f, result_values.down_f)
                if j != iterations - 1:
                    results[index] = results[index] + ","

        return results

    def simulate_leak(self, leak_coeff, length_before_leak, length_after_leak):
        toolkit.setpipedata(self.ph, self.upstream_pipe_index, length=length_before_leak, diam=self.orig_prop.diam,
                            rough=self.orig_prop.rough, mloss=self.orig_prop.mloss)
        toolkit.setpipedata(self.ph, self.downstream_pipe_index, length=length_after_leak, diam=self.orig_prop.diam,
                            rough=self.orig_prop.rough, mloss=self.orig_prop.mloss)
        leak_elev = self.trig.calculate_leak_elevation(length_before_leak)

        if self.use_elev:
            toolkit.setnodevalue(self.ph, self.leakage_node_index, toolkit.ELEVATION, leak_elev)

        toolkit.setnodevalue(self.ph, self.leakage_node_index, toolkit.EMITTER, leak_coeff)

        self.run_hydraulic_solver()

        return Results(self.ph, self.upstream_node_index, self.downstream_node_index, self.upstream_pipe_index,
                       self.downstream_pipe_index)


class TrigonometryTools:
    def __init__(self, ph, upstream_node, downstream_node, pipe_length):
        upstream_node_elevation, downstream_node_elevation = self.get_elevation(ph, upstream_node, downstream_node)
        elevation_diff = upstream_node_elevation - downstream_node_elevation

        self.upstream_node_elevation = upstream_node_elevation
        self.angle = math.asin(elevation_diff / pipe_length)

    def get_elevation(self, ph, upstream_node, downstream_node):
        upstream_elev = toolkit.getnodevalue(ph, upstream_node, toolkit.ELEVATION)
        downstream_elev = toolkit.getnodevalue(ph, downstream_node, toolkit.ELEVATION)
        return upstream_elev, downstream_elev

    def calculate_leak_elevation(self, length_from_upper):
        elevation_diff_from_upper_elevation = math.sin(self.angle) * length_from_upper
        return self.upstream_node_elevation - elevation_diff_from_upper_elevation


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


class LinkProperties:
    def __init__(self, ph, index):
        self.length = toolkit.getlinkvalue(ph, index, toolkit.LENGTH)
        self.diam = toolkit.getlinkvalue(ph, index, toolkit.DIAMETER)
        self.rough = toolkit.getlinkvalue(ph, index, toolkit.ROUGHNESS)
        self.mloss = toolkit.getlinkvalue(ph, index, toolkit.MINORLOSS)


class Results:
    def __init__(self, ph, up_node_index, down_node_index, up_link_index, down_link_index):
        self.up_p = toolkit.getnodevalue(ph, up_node_index, toolkit.PRESSURE)
        self.down_p = toolkit.getnodevalue(ph, down_node_index, toolkit.PRESSURE)
        self.up_f = toolkit.getlinkvalue(ph, up_link_index, toolkit.FLOW)
        self.down_f = toolkit.getlinkvalue(ph, down_link_index, toolkit.FLOW)
