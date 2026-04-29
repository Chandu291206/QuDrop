"""
QKD Protocols Package
Contains adapter modules for various Quantum Key Distribution protocols.
"""

from bb84.bb84_core import alice_generate as alice_generate_bb84
from bb84.bb84_core import bob_measure as bob_measure_bb84
from bb84.bb84_core import sift_key as sift_key_bb84

from protocols.b92_core import alice_generate_b92, bob_measure_b92, sift_key_b92
from protocols.e91_core import generate_e91_key, sift_key_e91
from protocols.six_state_core import alice_generate_six_state, bob_measure_six_state, sift_key_six_state

PROTOCOLS = {
    "BB84": {
        "alice_generate": alice_generate_bb84,
        "bob_measure": bob_measure_bb84,
        "sift_key": sift_key_bb84,
    },
    "B92": {
        "alice_generate": alice_generate_b92,
        "bob_measure": bob_measure_b92,
        "sift_key": sift_key_b92,
    },
    "E91": {
        "generate_key": generate_e91_key,
        "sift_key": sift_key_e91,
    },
    "Six-State": {
        "alice_generate": alice_generate_six_state,
        "bob_measure": bob_measure_six_state,
        "sift_key": sift_key_six_state,
    }
}
