# Author: Francesco Fiorini & Rostyslav Schiavini Yadzhak
# Inspired by: Daniel Escanez-Exposito (https://github.com/jdanielescanez/quantum-solver)

from qiskit import QuantumCircuit
from execution.classes.partecipant import Partecipant
from qiskit import transpile
import qiskit_aer
from qiskit_ibm_runtime.fake_provider import *
import time
from numpy.random import rand


simulator1 = qiskit_aer.Aer.get_backend('aer_simulator')

class Receiver(Partecipant):

    def __init__(self, name='', original_bits_size=0):
        super().__init__(name, original_bits_size)
    
    def decode_quantum_message_Eve(self,message,density,backend):
        self.values = []
        iteration_times = []
        for i,qc in enumerate(message):
            qc.barrier()
            start_time = time.time()
            if rand() < density:
                if self.axes[i]==1:
                    qc.h(0)
                if self.axes[i]==2:
                    qc.append(self.hy,[0])
                qc.measure(0,0)
                transpiled_qc = transpile(qc,backend=backend)
                result = backend.run(transpiled_qc,shots = 1,memory = True).result()
                measured_bit = int(result.get_memory()[0])
                self.values.append(measured_bit)
                transpiled_qc = transpile(qc,simulator1)
                resultTrue = int(simulator1.run(transpiled_qc, shots=1,memory = True).result().get_memory()[0])

                if resultTrue != measured_bit: 
                    qc.x(0)
                if self.axes[i] == 1:
                    qc.h(0)
                if self.axes[i] == 2:
                    qc.append(self.hy,[0])
            else:
                self.values.append(-1)

            time_ms = (time.time() - start_time) * 1000
            iteration_times.append(time_ms)

        return message, iteration_times
    
    def decode_quantum_messageBob(self, message, density, backend):
    ## The values of the participant
        self.values = []
        iteration_times = []

        for i, qc in enumerate(message):
            start_time = time.time()
            qc.barrier()
            if rand() < density:
                if self.axes[i] == 1:
                    qc.h(0)
                elif self.axes[i] == 2:
                    qc.append(self.hy, [0])
                qc.measure(0, 0)
                transpiled_qc = transpile(qc, backend=backend)
                result = backend.run(transpiled_qc, shots=1, memory=True).result()
                measured_bit = int(result.get_memory()[0])
                self.values.append(measured_bit)
            else:
                self.values.append(-1)
            time_ms = (time.time() - start_time) * 1000
            iteration_times.append(time_ms)
        return message, iteration_times
    
  


