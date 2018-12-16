import logging

import numpy as np
import pytest
from bluesky.preprocessors  import run_wrapper
from ophyd.sim import SynAxis
#fromi pcdsdevices.sequencer import EventSequencer, EventSequence
from ophyd.sim import NullStatus, make_fake_device


from ..devices import McgranePalette, SetSequencer as EventSequencer
from .conftest import SynSequencer, McgrainPalette
from ..plans import mcgrane_scan, x348_scan

logger = logging.getLogger(__name__)


FakeSequencer = make_fake_device(EventSequencer)
FakePalette = make_fake_device(McgranePalette)


# Simulated Sequencer for use in scans
# Code stolen from pcdsdevices/tests/test_sequencer.py commit: 0f73862  
class SimSequencer(FakeSequencer):
    """Simulated Sequencer usable in bluesky plans"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Forces an immediate stop on complete
        self.play_mode.put(2)
        # Initialize all signals to *something* to appease bluesky
        # Otherwise, these are all None which is invalid
        self.play_control.sim_put(0)
        self.sequence_length.sim_put(0)
        self.current_step.sim_put(0)
        self.play_count.sim_put(0)
        self.play_status.sim_put(0)
        self.sync_marker.sim_put(0)
        self.next_sync.sim_put(0)
        self.pulse_req.sim_put(0)
        self.sequence_owner.sim_put(0)
        self.sequence.ec_array.sim_put([0] * 2048)
        self.sequence.bd_array.sim_put([0] * 2048)
        self.sequence.fd_array.sim_put([0] * 2048)
        self.sequence.bc_array.sim_put([0] * 2048)

        # Initialize sequence
        initial_sequence = [[0] * 20,
                            [0] * 20,
                            [0] * 20,
                            [0] * 20]
        self.sequence.put_seq(initial_sequence)

    def kickoff(self):
        super().kickoff()
        return NullStatus()


def test_mcgrane_scan(fresh_RE):
    m1 = SynAxis(name="m1")
    m2 = SynAxis(name="m2")
    #seq = SynSequencer('', name='sequencer')
    seq = SimSequencer('', name='sequencer')
    seq._cb_sleep = 0 
    def test_plan():
        yield from mcgrane_scan(m1, m2, seq, 0, 5, 6, 5)
        assert m1.position == 5.0
        assert m2.position == 30
        assert seq.play_control.get() == 1

    # Send all metadata/data captured to the BestEffortCallback.
    fresh_RE(run_wrapper(test_plan()))

def test_x348_scan(fresh_RE):
    #m1 = SynAxis(name="m1")
    #m2 = SynAxis(name="m2")
    #seq = SynSequencer('', name='sequencer')
    pal = McgrainPalette(
        name = 'test_palette',
        N = 10,
        M = 5,
        chip_spacing = 0,
        chip_dims = [10])

    pal._accept_calibration(
        start_pt=np.array([0,0,0]), 
        n_pt=np.array([pal.N-1,0,0]),
        m_pt=np.array([0,pal.M-1,0]))


    seq = SimSequencer('', name='sequencer')
    
    seq._cb_sleep = 0 
    def test_plan():
        yield from x348_scan(pal, seq, 0, 7, .1)
        assert pal.x_motor.position == 1.0
        assert pal.y_motor.position == 3.0
        assert seq.play_control.get() == 1

    # Send all metadata/data captured to the BestEffortCallback.
    fresh_RE(run_wrapper(test_plan()))
