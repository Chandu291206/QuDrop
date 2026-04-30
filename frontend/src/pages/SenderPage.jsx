import { useState, useEffect } from 'react';
import { senderSocket } from '../socket';
import { Network, Key, FileUp, AlertTriangle, CheckCircle, Shield } from 'lucide-react';

export default function SenderPage() {
  const [ip, setIp] = useState('127.0.0.1');
  const [connected, setConnected] = useState(false);
  
  // QKD State
  const [protocol, setProtocol] = useState('BB84');
  const [rawBits, setRawBits] = useState(256);
  const [noiseEnabled, setNoiseEnabled] = useState(false);
  const [noiseRate, setNoiseRate] = useState(0.02);
  const [keyStatus, setKeyStatus] = useState('Idle');
  const [qber, setQber] = useState(null);
  const [keyBits, setKeyBits] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);
  
  // File Transfer State
  const [availableFiles, setAvailableFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState('');
  const [includeReference, setIncludeReference] = useState(true);
  const [transferStatus, setTransferStatus] = useState(null);

  useEffect(() => {
    senderSocket.connect();
    
    // Fetch files
    fetch('http://localhost:5001/api/files')
      .then(res => res.json())
      .then(data => setAvailableFiles(data))
      .catch(err => console.error("Could not fetch files", err));

    senderSocket.on('status', (data) => {
      if (data.message === 'Connected to receiver') setConnected(true);
      setKeyStatus(data.message);
    });

    senderSocket.on('error', (data) => {
      setErrorMsg(data.message);
      setKeyStatus('Error');
    });

    senderSocket.on('key_ready', (data) => {
      setKeyStatus('Key Ready');
      setQber(data.qber);
      setKeyBits(data.key_bits);
      setErrorMsg(null);
    });

    senderSocket.on('key_aborted', (data) => {
      setKeyStatus('Key Aborted');
      setQber(data.qber);
      setErrorMsg(`Aborted: ${data.reason}`);
    });

    senderSocket.on('file_sent', (data) => {
      setTransferStatus(data);
    });

    return () => {
      senderSocket.off('status');
      senderSocket.off('error');
      senderSocket.off('key_ready');
      senderSocket.off('key_aborted');
      senderSocket.off('file_sent');
      senderSocket.disconnect();
    };
  }, []);

  const handleConnect = () => {
    senderSocket.emit('connect_to_receiver', { ip });
  };

  const handleGenerateKey = () => {
    setKeyStatus('Generating...');
    setQber(null);
    setKeyBits(null);
    setErrorMsg(null);
    setTransferStatus(null);
    
    senderSocket.emit('generate_key', {
      protocol,
      raw_bits: rawBits,
      noise_enabled: noiseEnabled,
      noise_rate: noiseRate
    });
  };

  const handleSendFile = () => {
    if (!selectedFile) return;
    setTransferStatus({ status: 'sending' });
    senderSocket.emit('send_file', {
      filename: selectedFile,
      include_reference: includeReference
    });
  };

  return (
    <div className="container animate-fade-in">
      <div className="app-header">
        <h1>Sender</h1>
        <div className={`badge ${connected ? 'success' : 'warning'}`}>
          <Network size={14} style={{ marginRight: '6px' }} />
          {connected ? 'Connected to Receiver' : 'Not Connected'}
        </div>
      </div>

      <div className="grid-2">
        {/* Network & Protocol Config */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div className="glass-panel" style={{ padding: '1.5rem' }}>
            <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Network size={20} /> Connection
            </h3>
            <div style={{ marginTop: '1rem', display: 'flex', gap: '1rem' }}>
              <input 
                type="text" 
                value={ip} 
                onChange={e => setIp(e.target.value)} 
                placeholder="Receiver IP Address"
                disabled={connected}
              />
              <button className="btn btn-primary" onClick={handleConnect} disabled={connected}>
                Connect
              </button>
            </div>
          </div>

          <div className="glass-panel" style={{ padding: '1.5rem' }}>
            <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
              <Shield size={20} /> Protocol Configuration
            </h3>
            
            <label>QKD Protocol</label>
            <select value={protocol} onChange={e => setProtocol(e.target.value)} style={{ marginBottom: '1rem' }}>
              <option value="BB84">BB84 (Original)</option>
              <option value="B92">B92 (Two-State)</option>
              <option value="E91">E91 (Entanglement)</option>
              <option value="Six-State">Six-State Protocol</option>
            </select>
            
            <div className="grid-2" style={{ marginBottom: '1rem' }}>
              <div>
                <label>Raw Bits</label>
                <input type="number" value={rawBits} onChange={e => setRawBits(parseInt(e.target.value))} />
              </div>
              <div>
                <label>Channel Noise Rate</label>
                <input type="number" step="0.01" value={noiseRate} onChange={e => setNoiseRate(parseFloat(e.target.value))} disabled={!noiseEnabled} />
              </div>
            </div>
            
            <label className="checkbox-wrapper" style={{ marginTop: '1rem' }}>
              <input type="checkbox" checked={noiseEnabled} onChange={e => setNoiseEnabled(e.target.checked)} />
              Enable Channel Noise Simulation
            </label>
            
            <button 
              className="btn btn-primary" 
              style={{ width: '100%', marginTop: '1.5rem' }} 
              onClick={handleGenerateKey}
              disabled={!connected || keyStatus === 'Generating...'}
            >
              <Key size={18} /> Generate Secure Key
            </button>
          </div>
        </div>

        {/* Status & File Transfer */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div className="glass-panel" style={{ padding: '1.5rem' }}>
            <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
              <Key size={20} /> Key Status
            </h3>
            
            <div style={{ marginBottom: '1rem' }}>
              <strong>Status: </strong> 
              <span style={{ color: errorMsg ? 'var(--accent-danger)' : 'var(--accent-primary)' }}>
                {keyStatus}
              </span>
            </div>
            
            {qber !== null && (
              <div style={{ marginBottom: '0.5rem' }}>
                <strong>QBER: </strong> 
                <span style={{ color: qber > 0.11 ? 'var(--accent-danger)' : 'var(--accent-success)' }}>
                  {(qber * 100).toFixed(2)}%
                </span>
                {qber > 0.11 && <AlertTriangle size={14} style={{ marginLeft: '6px', color: 'var(--accent-danger)' }} />}
              </div>
            )}
            
            {keyBits && (
              <div style={{ color: 'var(--accent-success)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <CheckCircle size={18} /> Shared key established ({keyBits} bits)
              </div>
            )}
            
            {errorMsg && (
              <div style={{ color: 'var(--accent-danger)', marginTop: '0.5rem', fontSize: '0.9rem' }}>
                {errorMsg}
              </div>
            )}
          </div>

          <div className="glass-panel" style={{ padding: '1.5rem', opacity: keyBits ? 1 : 0.5, pointerEvents: keyBits ? 'auto' : 'none' }}>
            <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
              <FileUp size={20} /> File Transfer (XOR Encrypted)
            </h3>
            
            <label>Select File from Public Directory</label>
            <select value={selectedFile} onChange={e => setSelectedFile(e.target.value)} style={{ marginBottom: '1rem' }}>
              <option value="">-- Select a file --</option>
              {availableFiles.map(f => <option key={f} value={f}>{f}</option>)}
            </select>
            
            <label className="checkbox-wrapper" style={{ marginBottom: '1.5rem' }}>
              <input type="checkbox" checked={includeReference} onChange={e => setIncludeReference(e.target.checked)} />
              Include plaintext reference (for exact error rate analysis)
            </label>
            
            <button 
              className="btn btn-primary" 
              style={{ width: '100%' }} 
              onClick={handleSendFile}
              disabled={!selectedFile || transferStatus?.status === 'sending'}
            >
              <FileUp size={18} /> Encrypt and Send
            </button>

            {transferStatus && transferStatus.status !== 'sending' && (
              <div style={{ marginTop: '1.5rem', padding: '1rem', background: 'var(--glass-bg)', borderRadius: '8px' }}>
                <h4 style={{ marginBottom: '0.5rem' }}>Transfer Results</h4>
                <p>Send Rate: {(transferStatus.send_rate / 1024).toFixed(2)} KB/s</p>
                {transferStatus.result?.mode === 'exact' && (
                  <>
                    <p>Bit Error Rate: {transferStatus.result.bit_error_rate_pct.toFixed(4)}%</p>
                    <p>Byte Error Rate: {transferStatus.result.byte_error_rate_pct.toFixed(4)}%</p>
                  </>
                )}
              </div>
            )}
            {transferStatus?.status === 'sending' && <p style={{ marginTop: '1rem' }}>Sending...</p>}
          </div>
        </div>
      </div>
    </div>
  );
}
