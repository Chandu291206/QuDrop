# Author: Francesco Fiorini & Rostyslav Schiavini Yadzhak

from qiskit import transpile
import qiskit_aer
import qiskit_ibm_runtime.fake_provider 
from qiskit_ibm_runtime.fake_provider import FakeProviderForBackendV2
#from qiskit_ibm_runtime.fake_provider import FakeProvider
import qiskit_ibm_runtime.fake_provider.fake_backend
from execution.six_state import SixState

message_length = int(input("Insert the message length: "))
N_simulazioni = int(input("Insert the simulations number: "))
density = [0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1]
e_ch = 0

list_fake = FakeProviderForBackendV2()
backends = list_fake.backends()

for i in range(len(backends)):
    print("{0}. {1}".format(i,str(backends[i].backend_name)))

i = int(input("Insert the index corresponding to the chosen backend: "))



backend = backends[i]
ss=SixState('',message_length,e_ch,backend)

for k in density:
    for _ in range(N_simulazioni):
        ss.run_simulation(density=k)

