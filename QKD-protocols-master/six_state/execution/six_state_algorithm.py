#!/usr/bin/env python3

# Author: Francesco Fiorini & Rostyslav Schiavini Yadzhak
# Inspired by: Daniel Escanez-Exposito (https://github.com/jdanielescanez/quantum-solver)

from qiskit import QuantumCircuit
from execution.classes.sender import Sender
from execution.classes.receiver import Receiver
from random import SystemRandom, randrange
from alive_progress import alive_bar
from halo import Halo
import binascii
import pandas as pd
import time


SIX_STATE_SIMULATOR = 'SIX-STATE SIMULATOR'
DATA = {
  'Algorithm': ['SSP'],
  'Backend': ['-'],
  'String': ['-'],
  'Interception Density': ['-'],
  'Alice Values': [],
  'Alice Axes': [],
  'Eve Values': [],
  'Eve Axes': [],
  'Bob Values': [],
  'Bob Axes': [],
  'Alice Key': [],
  'Bob Key': [],
  'Shared Key': [],
  'Result': [],
  'Shared differences': ['-'],
  'Shared key length': ['-'],
  'Shared BER': ['-'],
  'Full key differences': ['-'],
  'Full key length': ['-'],
  'Full key BER': ['-']
}

## An implementation of the Six-State protocol
## @see https://qiskit.org/textbook/ch-algorithms/quantum-key-distribution.html
class SixStateAlgorithm:

  def __generate_key(self, backend, original_bits_size, verbose, ech):
    # Encoder Alice
    key_gen_time = time.time()
    alice = Sender('Alice', original_bits_size)
    alice.set_values()
    alice.set_axes()
    message,iteration_times = alice.encode_quantum_message()



    # Interceptor Eve
    eve = Receiver('Eve', original_bits_size)
    eve.set_axes()
    message, iteration_times = eve.decode_quantum_message_Eve(message, self.measure_density, backend)


    # Decoder Bob
    bob = Receiver('Bob', original_bits_size)
    bob.set_axes()
    message,iteration_times = bob.decode_quantum_messageBob(message, 1, backend)


    # Alice - Bob Remove Garbage
    alice_axes = alice.axes # Alice share her axes
    bob_axes = bob.axes # Bob share his axes

    # Delete the difference
    alice.remove_garbage(bob_axes)
    bob.remove_garbage(alice_axes)


    # Bob share some values of the key to check
    SHARED_SIZE = round(0.5 * len(bob.key))
    shared_key = bob.key[:SHARED_SIZE]

    if verbose:
      alice.show_values()
      alice.show_axes()
      DATA['Alice Values'] = str(alice.show_values())
      DATA['Alice Axes'] = str(alice.show_axes())

      eve.show_values()
      eve.show_axes()
      DATA['Eve Values'] = str(eve.show_values())
      DATA['Eve Axes'] = str(eve.show_axes())

      bob.show_values()
      bob.show_axes()
      DATA['Bob Values'] = str(bob.show_values())
      DATA['Bob Axes'] = str(bob.show_axes())

      alice.show_key()
      bob.show_key()
      DATA['Alice Key'] = str(alice.show_key())
      DATA['Bob Key'] = str(bob.show_key())

      print('\nShared Bob Key:')
      print(shared_key)
      DATA['Shared Key'] = str(shared_key)

    alice_key = alice.show_key()
    compare = alice_key[:len(shared_key)]
    # BER calculation
    counter = 0
    for i in range(len(shared_key)):
      if(shared_key[i] != compare[i]):
        counter = counter + 1
    DATA["Shared differences"] = str(counter)
    DATA["Shared key length"] = str(len(shared_key))
    DATA["Shared BER"] = str(counter/len(shared_key))
    sampleQber=counter/len(shared_key)
    psample=(sampleQber-ech)/(0.33-0.66*ech**2-0.33*ech)
    print('\nSample p: '+str(psample))

    alice_key = alice.show_key()
    bob_key = bob.show_key()
    counter = 0
    for i in range(len(alice_key)):
      if(alice_key[i] != bob_key[i]):
        counter = counter + 1
    DATA["Full key differences"] = str(counter)
    DATA["Full key length"] = str(len(alice_key))
    DATA["Full key BER"] = str(counter/len(alice_key))

    

    # Alice check the shared key
    if alice.check_key(shared_key):
     
      shared_size = len(shared_key)
      alice.confirm_key(shared_size)
      bob.confirm_key(shared_size)
      if verbose:
        print('\nFinal Keys')
        alice.show_key()
        bob.show_key()
        print('\nSecure Communication!')
    elif verbose:
      print('\nUnsecure Communication! Eve has been detected intercepting messages\n')
      DATA['Result'] = 'Unsecure (intercepted)'

    return alice, bob

  ## Run the implementation of Six-State protocol
  def run(self, message, backend, original_bits_size, measure_density, n_bits, verbose,ech):
    ## The original size of the message
    self.original_bits_size = original_bits_size
    ## The probability of an interception occurring
    self.measure_density = measure_density

    alice, bob = self.__generate_key(backend, original_bits_size, verbose,ech)
  

  
    if not (alice.is_safe_key and bob.is_safe_key):
      if verbose:
        print('❌ Message not send')
        DATA['Result'] = 'Message not sent'
        df = pd.DataFrame(DATA)
        filename = 'data.xlsx'
        df.to_excel(filename, index=False)
      return False

    alice.generate_otp(n_bits)
    bob.generate_otp(n_bits)

    encoded_message = alice.xor_otp_message(message)
    decoded_message = bob.xor_otp_message(encoded_message)

    if verbose:
      alice.show_otp()
      bob.show_otp()


      print('\nInitial Message:')
      print(message)

      print('Encoded Message:')
      print(encoded_message)

      print('💡 Decoded Message:')
      print(decoded_message)

      if message == decoded_message:
        print('\n✅ The initial message and the decoded message are identical')
        DATA['Result'] = 'Secure'
      else:
        print('\n❌ The initial message and the decoded message are different')
        DATA['Result'] = 'Different messages'

      print(DATA)
      df = pd.DataFrame(DATA)
      filename = 'data.xlsx'
      df.to_excel("data.xlsx")
      #df.to_csv("home/data.csv")

    return True
