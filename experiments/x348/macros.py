import logging

import numpy as np
from experiments.x348.plans import x348_scan
from experiments.x348.devices import McgranePalette
from bluesky.preprocessors import run_wrapper 
from bluesky.run_engine import RunEngine
from experiments.x348.devices import SetSequencer

logger = logging.getLogger(__name__)

def base_macro():
    return "Success"

def x348_scan_tool(N, M, start_pt, n_pt, m_pt, start=0, stop=None,
            delay= .15, use_seq=True):
    """
    x384_scan_tool

    Single function for running the x384 snake scan with minimal python
    overhead.

    All (X,Y,Z) coordinates for the motors are specified using the motor's
    position readout when the sample is at the given point. E.g. The start
    point is found by aligning the starting sample in the beam and copying the
    motors' current positions. All of the (X,Y,Z) coordinates use this system.
    None of the (X,Y,Z) Coordinates are relative.

    N Corresponds with the horizontal (X) axis
    M Corresponds with the horizontal (Y) axis

    Parameters
    ----------
    N : int
        The number of samples in the N direction.

    M : int
        The number of samples in the M direction.

    start_pt : np.array or list
        3-length numpy array specifying the starting point (X,Y,Z) of the
        motors. This is used for calibrating the scan area.
    
    n_pt : np.array or list
        3-length numpy array specifying the location (X,Y,Z) of the last point
        in the N direction in the same row as the start_pt. This is used for
        calibrating the scan area.
    
    m_pt : np.array or list
        3-length numpy array specifying the location (X,Y,Z) of the last point
        in the M direction in the same column as the start_pt. This is used for
        calibrating the scan area.

    start : int 
        Index of the first point to scan. Index numbers are allotted starting
        at zero and counting down the samples in the order that the 'snakey
        path' will visit these points. Indexing starts at 0. 

    end : int or None
        Index of the end of the scan. This is value is EXCLUSIVE. E.g using a
        start value of 3 and an end value of 6 means that sample indexes 3, 4,
        and 5 will be scanned but NOT 6. If None is entered is passed, only the
        index listed by 'start' will be scanned. Defaults to None.

    delay : float
        Time to wait for the sequencer to complete. Units are in seconds. 
        Defaults to .15s. 

    use_seq : bool
        Defaults to True. Set this to false to disable the sequencer (and hence
        the beam if it's in burst mode) for a run. This is good for simulating
        runs before they happen
        
    
    """

    start_pt = np.array(start_pt)
    n_pt = np.array(n_pt)
    m_pt = np.array(m_pt)

    sq = SetSequencer("ECS:SYS0:1", name="Event Sequencer")
    pal = McgranePalette( 
        name="mcgpal", 
        N=N, 
        M=M, 
        chip_spacing=0, 
        chip_dims=[N] 
    ) 
    
    pal._accept_calibration( 
        start_pt = start_pt, 
        n_pt = n_pt, 
        m_pt = m_pt, 
    )

    #pal.x_motor.move(start_pt[0])
    #pal.y_motor.move(start_pt[1])
    #pal.z_motor.move(start_pt[2]) 
   

    RE = RunEngine({})
    RE(run_wrapper(x348_scan(
        pal, sq, start, stop, sequencer_delay=delay,
    )))
        



