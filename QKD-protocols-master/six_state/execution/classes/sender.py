#!/usr/bin/env python3

# Author: Francesco Fiorini & Rostyslav Schiavini Yadzhak
# Inspired by: Daniel Escanez-Exposito (https://github.com/jdanielescanez/quantum-solver)

from execution.classes.partecipant import Partecipant
from qiskit import QuantumCircuit
import time

## The Sender entity in the Six-State implementation
## @see https://qiskit.org/textbook/ch-algorithms/quantum-key-distribution.html
class Sender(Partecipant):
  ## Constructor
  def __init__(self, name='', original_bits_size=0):
    super().__init__(name, original_bits_size)
    
  ## Encode the message (values) using a quantum circuit
  def encode_quantum_message(self):
    
    encoded_message = []
    iteration_times = []

    for i in range(len(self.axes)):
      start_time = time.time()
      qc = QuantumCircuit(1, 1)
      if self.values[i] == 1:
        qc.x(0)
      if self.axes[i] == 1:
        qc.h(0)
      elif self.axes[i] == 2:
        qc.append(self.hy, [0])
      encoded_message.append(qc)
      time_ms = (time.time() - start_time) * 1000
      iteration_times.append(time_ms)
    return encoded_message, iteration_times
