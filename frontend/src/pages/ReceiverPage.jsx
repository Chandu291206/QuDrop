import { useState, useEffect } from 'react';
import { receiverSocket } from '../socket';
import { Network, Key, FileDown, AlertTriangle, CheckCircle, ShieldAlert } from 'lucide-react';

export default function ReceiverPage() {
  const [listening, setListening] = useState(false);
  const [status, setStatus] = useState('Idle');
  const [errorMsg, setErrorMsg] = useState(null);
  
  // Key State
  const [qber, setQber] = useState(null);
  const [keyBits, setKeyBits] = useState(null);
  
  // Transfer State
  const [transferData, setTransferData] = useState(null);

  useEffect(() => {
    receiverSocket.connect();
    
    receiverSocket.on('status', (data) => {
      setStatus(data.message);
    });

    receiverSocket.on('error', (data) => {
      setErrorMsg(data.message);
      setStatus('Error');
    });

    receiverSocket.on('key_ready', (data) => {
      setStatus('Key Ready');
      setQber(data.qber);
      setKeyBits(data.key_bits);
      setErrorMsg(null);
    });

    receiverSocket.on('key_aborted', (data) => {
      setStatus('Key Aborted');
      setQber(data.qber);
      setErrorMsg(`Aborted: ${data.reason}`);
    });

    receiverSocket.on('file_received', (data) => {
      setTransferData(data);
      setStatus('File Decrypted');
    });

    return () => {
      receiverSocket.off('status');
      receiverSocket.off('error');
      receiverSocket.off('key_ready');
      receiverSocket.off('key_aborted');
      receiverSocket.off('file_received');
      receiverSocket.disconnect();
    };
  }, []);

  const handleStartListening = () => {
    setListening(true);
    setStatus('Listening for connections on port 5000...');
    setQber(null);
    setKeyBits(null);
    setTransferData(null);
    setErrorMsg(null);
    receiverSocket.emit('start_receiver');
  };

  return (
    <div className="container animate-fade-in">
      <div className="app-header">
        <h1>Receiver (Bob)</h1>
        <div className={`badge ${listening ? 'success' : 'info'}`}>
          <Network size={14} style={{ marginRight: '6px' }} />
          {listening ? 'Active Listener' : 'Idle'}
        </div>
      </div>

      <div className="grid-2">
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <div className="glass-panel" style={{ padding: '1.5rem' }}>
            <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
              <Network size={20} /> Connection Listener
            </h3>
            <p style={{ marginBottom: '1.5rem' }}>
              Start the TCP listener to allow Alice to connect, exchange QKD parameters, and send encrypted files.
            </p>
            <button 
              className="btn btn-primary" 
              onClick={handleStartListening} 
              disabled={listening}
              style={{ width: '100%' }}
            >
              {listening ? 'Listening...' : 'Start Receiver'}
            </button>
          </div>

          <div className="glass-panel" style={{ padding: '1.5rem' }}>
            <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
              <Key size={20} /> Session Status
            </h3>
            
            <div style={{ marginBottom: '1rem' }}>
              <strong>Log: </strong> 
              <span style={{ color: errorMsg ? 'var(--accent-danger)' : 'var(--text-main)' }}>
                {status}
              </span>
            </div>
            
            {qber !== null && (
              <div style={{ marginBottom: '0.5rem' }}>
                <strong>QBER: </strong> 
                <span style={{ color: qber > 0.11 ? 'var(--accent-danger)' : 'var(--accent-success)' }}>
                  {(qber * 100).toFixed(2)}%
                </span>
              </div>
            )}
            
            {keyBits && (
              <div style={{ color: 'var(--accent-success)', display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '1rem' }}>
                <CheckCircle size={18} /> Shared key established ({keyBits} bits)
              </div>
            )}
            
            {errorMsg && (
              <div style={{ color: 'var(--accent-danger)', display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '1rem' }}>
                <ShieldAlert size={18} /> {errorMsg}
              </div>
            )}
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '1.5rem' }}>
          <h3 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
            <FileDown size={20} /> Received Files
          </h3>
          
          {transferData ? (
            <div style={{ background: 'rgba(0,0,0,0.2)', padding: '1.5rem', borderRadius: '8px' }}>
              <h4 style={{ fontSize: '1.2rem', marginBottom: '1rem', color: 'var(--accent-primary)' }}>
                {transferData.filename}
              </h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <p>Saved to: <code>received_files/{transferData.filename}</code></p>
                <p>Receive Rate: {(transferData.receive_rate / 1024).toFixed(2)} KB/s</p>
                
                {transferData.result?.mode === 'exact' && (
                  <div style={{ marginTop: '1rem', borderTop: '1px solid var(--glass-border)', paddingTop: '1rem' }}>
                    <h5 style={{ marginBottom: '0.5rem' }}>Error Analysis</h5>
                    <p>Bit Error Rate: {transferData.result.bit_error_rate_pct.toFixed(4)}%</p>
                    <p>Byte Error Rate: {transferData.result.byte_error_rate_pct.toFixed(4)}%</p>
                    {transferData.result.bit_errors === 0 ? (
                      <p style={{ color: 'var(--accent-success)', marginTop: '0.5rem' }}>Perfect decryption match!</p>
                    ) : (
                      <p style={{ color: 'var(--accent-danger)', marginTop: '0.5rem' }}>Decryption mismatch detected.</p>
                    )}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '3rem 0', color: 'var(--text-muted)' }}>
              <FileDown size={48} style={{ opacity: 0.2, margin: '0 auto 1rem' }} />
              <p>No files received yet in this session.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
