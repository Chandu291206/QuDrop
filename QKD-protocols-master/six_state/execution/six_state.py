# Author: Francesco Fiorini & Rostyslav Schiavini Yadzhak

from execution.six_state_algorithm import SixStateAlgorithm
import time
import numpy as np
from halo import Halo
from numpy.random import randint
from random import SystemRandom, randrange
import string
from alive_progress import alive_bar
import pandas as pd
from math import ceil


SIX_STATE_SIMULATOR = 'SIX-STATE SIMULATOR'
DATA = {
  'Algorithm': ['SSP'],
  'Backend': [],
  'String': [],
  'Interception Density': [],
  'Alice Values': ['-'],
  'Alice Axes': ['-'],
  'Eve Values': ['-'],
  'Eve Axes': ['-'],
  'Bob Values': ['-'],
  'Bob Axes': ['-'],
  'Alice Key': ['-'],
  'Bob Key': ['-'],
  'Shared Key': ['-'],
  'Result': ['-'],
  'Shared differences': ['-'],
  'Shared key length': ['-'],
  'Shared BER': ['-'],
  'Full key differences': ['-'],
  'Full key length': ['-'],
  'Full key BER': ['-']
}

## Main class of Six-State Simulator
## @see https://qiskit.org/textbook/ch-algorithms/quantum-key-distribution.html
class SixState:
  ## Constructor
  def __init__(self, token, message, ech, backend):
    ## The implemented protocol
    self.six_state_algorithm = SixStateAlgorithm()
    ## The IBMQ Experience token
    self.message = message
    self.ech = ech
    self.token = token
    self.backend = backend

  ## Run Six-State simulation once
  def run_simulation(self, density):
    DATA['String'] = self.message
    DATA['Interception Density']=str(density)
    DATA['Backend'] = str(self.backend.backend_name)
    N_BITS = 6
    bits_size = self.message #* 10 * N_BITS
    possible_chars = string.ascii_lowercase + string.ascii_uppercase + string.digits
    message = ''.join(SystemRandom().choice(possible_chars) for _ in range(ceil(self.message)))
    execution_description = str(self.backend)
    execution_description += ' with message "'
    execution_description += message + '" and density "' + str(density) + '"'
    halo_text = 'Running Six-State simulation in ' + execution_description
    halo = Halo(text=halo_text, spinner="dots")
    try:
      halo.start()
      start_time = time.time()
      print(start_time)
      self.six_state_algorithm.run(message, self.backend, bits_size, density, N_BITS, True,self.ech)
      time_ms = (time.time() - start_time) * 1000
      halo.succeed()
      print('  Six-State simulation runned in', str(time_ms), 'ms')

      
      df1 = pd.read_excel('data.xlsx')
      df2 = pd.DataFrame(DATA)
      df1.replace('-', pd.NA, inplace=True)
      df2.replace('-', pd.NA, inplace=True)

      merged_df = df1.combine_first(df2)
      concat_row = merged_df.iloc[0].to_frame().T

      final_df = pd.read_excel('final_data.xlsx')
      file_concat = pd.concat([final_df, concat_row], axis=0)
      file_concat.to_excel('final_data.xlsx', index=False)


    except Exception as exception:
      halo.fail()
      print('Exception:', exception)
