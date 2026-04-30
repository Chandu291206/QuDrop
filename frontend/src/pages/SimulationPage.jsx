import { useState, useEffect } from 'react';
import { simulationSocket } from '../socket';
import { Activity, Play, RefreshCw } from 'lucide-react';

export default function SimulationPage() {
  const [protocol, setProtocol] = useState('BB84');
  const [nBits, setNBits] = useState(20);
  const [eveEnabled, setEveEnabled] = useState(false);
  const [simData, setSimData] = useState(null);
  
  // Animation state (only for BB84)
  const [stepIndex, setStepIndex] = useState(0);
  const [animating, setAnimating] = useState(false);

  useEffect(() => {
    simulationSocket.connect();
    
    simulationSocket.on('simulation_data', (res) => {
      setSimData(res);
      if (res.protocol === 'BB84') {
        setStepIndex(0);
      }
    });

    return () => {
      simulationSocket.off('simulation_data');
      simulationSocket.disconnect();
    };
  }, []);

  useEffect(() => {
    if (animating && simData?.protocol === 'BB84' && stepIndex < 5) {
      const timer = setTimeout(() => {
        setStepIndex(prev => prev + 1);
      }, 1000);
      return () => clearTimeout(timer);
    } else if (stepIndex >= 5) {
      setAnimating(false);
    }
  }, [animating, stepIndex, simData]);

  const runSimulation = () => {
    setSimData(null);
    simulationSocket.emit('run_simulation', { protocol, n_bits: nBits, eve: eveEnabled });
  };

  const startAnimation = () => {
    if (!simData || simData.protocol !== 'BB84') return;
    setStepIndex(1);
    setAnimating(true);
  };

  const getStatusText = () => {
    if (!simData) return "Ready.";
    if (simData.protocol !== 'BB84') return "Simulation complete.";
    
    const messages = {
      0: "Ready.",
      1: "Step 1/5: Sender generated random bits and bases.",
      2: "Step 2/5: Receiver's random bases are revealed.",
      3: "Step 3/5: Receiver's measured bits are revealed.",
      4: "Step 4/5: Basis comparison shows matches and mismatches.",
      5: "Step 5/5: Final sifted key and QBER are shown."
    };
    return messages[stepIndex] || "Running...";
  };

  return (
    <div className="container animate-fade-in">
      <div className="app-header">
        <h1>Protocol Simulation</h1>
        <div className="badge info">
          <Activity size={14} style={{ marginRight: '6px' }} /> Local Math Engine
        </div>
      </div>

      <div className="glass-panel" style={{ padding: '1.5rem', marginBottom: '2rem' }}>
        <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'flex-end', flexWrap: 'wrap' }}>
          <div>
            <label>Protocol</label>
            <select value={protocol} onChange={e => { setProtocol(e.target.value); setSimData(null); }}>
              <option value="BB84">BB84</option>
              <option value="B92">B92</option>
              <option value="E91">E91</option>
              <option value="Six-State">Six-State</option>
            </select>
          </div>
          
          <div>
            <label>Bits to Simulate</label>
            <input type="number" value={nBits} onChange={e => setNBits(parseInt(e.target.value))} style={{ width: '120px' }} />
          </div>
          
          <div style={{ paddingBottom: '0.75rem' }}>
            <label className="checkbox-wrapper">
              <input type="checkbox" checked={eveEnabled} onChange={e => setEveEnabled(e.target.checked)} />
              Enable Eavesdropper
            </label>
          </div>
          
          <button className="btn btn-primary" onClick={runSimulation}>
            <Activity size={16} /> Run
          </button>
          
          {protocol === 'BB84' && simData && (
            <button className="btn btn-secondary" onClick={startAnimation} disabled={animating}>
              <Play size={16} /> Animate
            </button>
          )}
        </div>
      </div>

      {simData && simData.protocol === 'BB84' && (
        <div className="glass-panel" style={{ padding: '2rem' }}>
          <h3 style={{ marginBottom: '1rem', color: stepIndex >= 5 && simData.data.qber > 0.11 ? 'var(--accent-danger)' : 'var(--text-main)' }}>
            {getStatusText()}
          </h3>
          
          <div style={{ fontFamily: 'monospace', fontSize: '1.2rem', lineHeight: '2' }}>
            <div style={{ display: 'flex' }}><span style={{ width: '150px' }}>Sender Bits:</span> {stepIndex >= 1 ? simData.data.alice_bits.join(' ') : ''}</div>
            <div style={{ display: 'flex' }}><span style={{ width: '150px' }}>Sender Bases:</span> {stepIndex >= 1 ? simData.data.alice_bases.join(' ') : ''}</div>
            <br />
            <div style={{ display: 'flex' }}><span style={{ width: '150px' }}>Receiver Bases:</span> {stepIndex >= 2 ? simData.data.bob_bases.join(' ') : '? '.repeat(nBits)}</div>
            <div style={{ display: 'flex' }}><span style={{ width: '150px' }}>Receiver Results:</span> {stepIndex >= 3 ? simData.data.bob_results.join(' ') : '? '.repeat(nBits)}</div>
            <br />
            <div style={{ display: 'flex' }}><span style={{ width: '150px' }}>Matches:</span> 
              {stepIndex >= 4 ? simData.data.matches.map((m, i) => (
                <span key={i} style={{ color: m ? 'var(--accent-success)' : 'var(--accent-danger)', width: '1.2rem', display: 'inline-block' }}>
                  {m ? '✓' : '✗'}
                </span>
              )) : '? '.repeat(nBits)}
            </div>
            <div style={{ display: 'flex' }}><span style={{ width: '150px' }}>Final Key:</span> <span style={{ color: 'var(--accent-primary)' }}>{stepIndex >= 5 ? simData.data.final_key.join(' ') : ''}</span></div>
            <div style={{ display: 'flex' }}><span style={{ width: '150px' }}>QBER:</span> <span style={{ color: stepIndex >= 5 && simData.data.qber > 0.11 ? 'var(--accent-danger)' : 'var(--text-main)' }}>{stepIndex >= 5 ? (simData.data.qber * 100).toFixed(2) + '%' : ''}</span></div>
          </div>
        </div>
      )}

      {simData && simData.protocol !== 'BB84' && (
        <div className="glass-panel" style={{ padding: '2rem' }}>
          <h3>Simulation Result</h3>
          <div className="grid-2" style={{ marginTop: '1.5rem' }}>
            <div className="glass-card">
              <h4 style={{ color: 'var(--text-muted)' }}>Raw Bits</h4>
              <p style={{ fontSize: '2rem', fontWeight: 'bold', color: 'var(--text-main)' }}>{simData.summary.raw_bits}</p>
            </div>
            <div className="glass-card">
              <h4 style={{ color: 'var(--text-muted)' }}>Sifted Bits</h4>
              <p style={{ fontSize: '2rem', fontWeight: 'bold', color: 'var(--accent-primary)' }}>{simData.summary.sifted_bits}</p>
            </div>
            <div className="glass-card">
              <h4 style={{ color: 'var(--text-muted)' }}>QBER</h4>
              <p style={{ fontSize: '2rem', fontWeight: 'bold', color: simData.summary.qber > 0.11 ? 'var(--accent-danger)' : 'var(--accent-success)' }}>
                {(simData.summary.qber * 100).toFixed(2)}%
              </p>
            </div>
            <div className="glass-card">
              <h4 style={{ color: 'var(--text-muted)' }}>Security Check</h4>
              <p style={{ fontSize: '1.5rem', fontWeight: 'bold', color: simData.summary.eavesdropping_detected ? 'var(--accent-danger)' : 'var(--accent-success)' }}>
                {simData.summary.eavesdropping_detected ? 'Eavesdropping Detected' : 'Secure Channel'}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
