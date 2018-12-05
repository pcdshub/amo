import logging
import pdb
import numpy as np
import pytest
from ophyd.tests.conftest import using_fake_epics_pv

from .conftest import McgrainPalette

logger = logging.getLogger(__name__)


def test_McgrainPalette_move_method():
    pal = McgrainPalette(
        name='Test Palette', 
        N = 24*3 + 8,
        M = 23,
        chip_spacing = 0,
        chip_dims = [24*3 + 8])

    #pdb.set_trace()

    pal._accept_calibration(
        start_pt=np.array([0,0,0]), 
        n_pt=np.array([pal.N-1,0,0]),
        m_pt=np.array([0,pal.M-1,0]))

    for i in range(48):
        pal.move(i)
        print(pal.coordinates)



    pal.move(24)
    print(pal.coordinates)
    assert np.all(pal.coordinates == (1.0, 21.0, 0.0))

    pal.move(10, 10)
    print(pal.coordinates)
    assert np.all(pal.coordinates == (10.0, 10.0, 0.0))

    pal.move(1, 1, 1)
    print(pal.coordinates)
    assert np.all(pal.coordinates == (1.0, 1.0, 1.0))
    #assert False
