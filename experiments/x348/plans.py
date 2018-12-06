import logging
import time


import pandas as pd
from bluesky.plan_stubs import abs_set, rel_set, checkpoint, mv
from bluesky.plans import scan, inner_product_scan, list_scan
from bluesky.preprocessors import stub_wrapper

from .exceptions import InvalidSampleError

logger = logging.getLogger(__name__)


def x348_scan(palette, sequencer, first_target, last_target=None,
        sequencer_delay=None):
    """
    Parameters
    ----------
    palette : experiments.x348.devices.McgranePalette
        Pallete object w/ motors and math modules. This is an ophyd object
        representing the mobile target-holding device. This plan presumes that
        the palette object has already been calibrated. externally

    sequencer : 
        Ophyd object for controlling LCLS sequencer. In burst mode this object
        allows sequences of shots to be called on demand. 

    first_target : int 
        Index of the first target on the sample to be struck by the beam. This
        is inclusive such that if this argument is 5, sample No. 5 will be the
        first sample to recieve beam.

    last_target : int or None.
        Index of the last target on the sample to be struck. This is exclusive
        such that if this argument is 5, sample No. 5 will NOT recive beam.
        Presuming that the indexes are in posive order (first target <
        last_target), No. 4 will be the last to recieve beam. In the event that
        this is None, only the first_target will be scanned.

    sequencer_delay : float
        A delay time to wait after each sequencer run. This may be necessary if
        the sequencer start command does not block until the sequence's
        completion.
    """

    # Handle the default value for the sequencer delay
    if sequencer_delay is None:
        sequencer_delay = 0.0

    # Set the sequencer's delay duration
    sequencer._cb_sleep = sequencer_delay

    # Create the ordered range of targets to be sampled
    if last_target is not None:
        index_sequence = range(first_target, last_target) 
    else:
        index_sequence = [first_target]

    # Generate spatial coordinate list of all samples to test. 
    xyz_sequence = []
    for target_index in index_sequence:
        xyz_sequence.append(
            palette.locate_2d(*palette.locate_1d(target_index))) 

    for index, coordinates in zip(index_sequence, xyz_sequence):
        yield from mv(
            palette.x_motor, coordinates[0],
            palette.y_motor, coordinates[1],
            palette.z_motor, coordinates[2],
        )

        yield from abs_set(sequencer, 1, wait=True)
        
        
        #print("~~~~~~~~~~~~")
        #print(index)
        #print(palette.x_motor.position)
        #print(palette.y_motor.position)
        #print(palette.z_motor.position)


def mcgrane_scan(outer_motor, inner_motor, sequencer, outer_start,
                 outer_stop, outer_steps, inner_steps, inner_step_size=1,
                 use_sequencer=True, wait=None):
    """Relative scan nested into a normal scan, that starts the sequencer at
    each inner step.

    Performs a normal scan using the outer motor, and then performs a
    relative scan within each outer motor step using the inner motor. The
    sequencer is then triggered at every inner step in the scan.

    Parameters
    ----------
    outer_motor : Motor
        Motor to perform the outer normal scan

    inner_motor : Motor
        Motor to perform the inner relative scan

    sequencer : Sequencer
        Sequencer to trigger at every inner motor step

    outer_start : float
        Starting position of the outer motor

    outer_stop : float
        Stopping position of the outer motor
    
    outer_steps : float
        Number of steps to take during the scan, including the endpoints

    inner_steps : int or list
        Number of relative steps to take at every outer step if an int. If it's
        a list, it is the list of relative motions to perform at every outer
        step

    wait : float, optional
        The amount of time to wait at each step     
    """
    # Create the list of relative motions that will be performed
    if isinstance(inner_steps, int):
        # If it is an int, create a list of unit motions of that length
        inner_steps = [1] * inner_steps

    scan_positions = []

    # Define what will be done at every monochrometer step
    def outer_per_step(detectors, motor, step):
        # Set a checkpoint in case the scan is interrupted
        yield from checkpoint()

        # Move the monochrometer to the inputted energy
        logger.info('Outer Step: Moving {0} to {1}'.format(
            outer_motor.name, step))
        yield from abs_set(outer_motor, step, wait=True)

        # Define what we will do at every motor step
        def inner_per_step(detectors, motor, step):
            # Set a checkpoint in case the scan is interrupted
            yield from checkpoint()

            """
            # Notify the user where we are trying to move to
            goal_sample = inner_motor.position + inner_step_size
            goal_index = inner_motor.locate_1d(goal_sample)
            logger.info('Inner Step: Moving {0} to {1} (sample {2})'.format(
                inner_motor.name, goal_index, goal_sample))
            """

            # Move the motor to the inputted step
            yield from rel_set(inner_motor, inner_step_size, wait=True)

            if use_sequencer:
                # # Start and wait for the sequencer
                logger.info('Inner Step: Starting the sequencer')
                yield from abs_set(sequencer, 1, wait=True)

            # Wait the specified amount of time
            if wait:
                logger.info("Inner Step: Waiting for {0} second(s)...".format(
                    wait))
                time.sleep(wait)

            # Fill the dataframe
            scan_positions.append((outer_motor.position, 
                                   #inner_motor.chip,
                                   inner_motor.position,
                                   #*inner_motor.index,
                                   #*inner_motor.coordinates
                                   ))
 
        # Define the larger inner scan as a list_scan. We cannot use
        # rel_list_scan because it includes the reset_positions_decorator,
        # which we do not want to do
        yield from stub_wrapper(list_scan([], inner_motor, inner_steps,
                                          per_step=inner_per_step))

    # # Set the sequencer to run once
    if use_sequencer:
        yield from abs_set(sequencer.play_mode, 0, wait=True)

    try:
        # Perform the larger scan
        yield from stub_wrapper(scan([], outer_motor, outer_start, outer_stop,
                                     outer_steps, per_step=outer_per_step))
    except InvalidSampleError:
        logger.warning('Reached the end of "{0}". Ending scan in position '
                       '{1} (sample {2})'.format(inner_motor.name, 
                                                 inner_motor.index, 
                                                 inner_motor.position))

    # Create the dataframe and return it
    '''
    columns = ('mono', 'chip', 'sample', 'i', 'j', 'x', 'y', 'z')
    df = pd.DataFrame(scan_positions, columns=columns)
    df.index.name = 'Scan Step'
    return df
    '''
    return None

