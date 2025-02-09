# Copyright 2023. Allen Institute. All rights reserved
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
# following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following
# disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following
# disclaimer in the documentation and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote
# products derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
import os
from bmtk.simulator.pointnet.modules.sim_module import SimulatorMod
from bmtk.simulator.pointnet.io_tools import io
from bmtk.utils.reports.spike_trains import SpikeTrains
from bmtk.simulator.pointnet.pyfunction_cache import py_modules


class SpikesInputsMod(SimulatorMod):
    def __init__(self, name, input_type, module, **kwargs):
        self._name = name
        self._input_type = input_type
        self._module = module
        self._params = kwargs
        self._spike_trains = None

    def initialize(self, sim):
        io.log_info('Build virtual cell stimulations for {}'.format(self._name))
        
        node_set = sim.net.get_node_set(self._params['node_set'])
       
        if self._module == 'function':
            if 'spikes_function' not in self._params:
                io.log_exception('missing parameter "spikes_function" for input {self._name}, module {self._module}')
            spikes_generator = self._params['spikes_function']
            if spikes_generator not in py_modules.spikes_generators:
                io.log_exception(f'Could not find @spikes_generator function "{spikes_generator}" required for {self._name} inputs.')
            spikes_func = py_modules.spikes_generator(name=spikes_generator)
            
            self._spike_trains = SpikeTrains(cache_to_disk=False)
            for node in node_set.fetch_nodes():
                timestamps = spikes_func(node, sim)
                self._spike_trains.add_spikes(
                    node_ids=node.node_id, 
                    timestamps=timestamps, 
                    population=node.population_name
                )
        else:
            self._spike_trains = SpikeTrains.load(
                path=self._params['input_file'], 
                file_type=self._module, 
                **self._params
            )

        sim.net.add_spike_trains(self._spike_trains, node_set, sim.get_spike_generator_params())
