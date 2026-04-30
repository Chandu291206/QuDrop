import { Send, Download, Activity } from 'lucide-react';

export default function HomePage({ onNavigate }) {
  return (
    <div className="container animate-fade-in" style={{ paddingTop: '5rem' }}>
      <div style={{ textAlign: 'center', marginBottom: '4rem' }}>
        <h1 style={{ fontSize: '3.5rem', marginBottom: '1rem' }}>QuDrop</h1>
        <p style={{ fontSize: '1.2rem', maxWidth: '600px', margin: '0 auto' }}>
          A Quantum Key Distribution (QKD) Based Secure File Transfer System 
        </p>
      </div>

      <div className="grid-3">
        <div className="glass-card" style={{ textAlign: 'center', cursor: 'pointer' }} onClick={() => onNavigate('sender')}>
          <div style={{ background: 'rgba(99, 102, 241, 0.1)', width: '64px', height: '64px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1.5rem', color: 'var(--accent-primary)' }}>
            <Send size={32} />
          </div>
          <h3 style={{ fontSize: '1.5rem' }}>Sender</h3>
          <p>Generate QKD keys and send securely encrypted files to a receiver.</p>
        </div>

        <div className="glass-card" style={{ textAlign: 'center', cursor: 'pointer' }} onClick={() => onNavigate('receiver')}>
          <div style={{ background: 'rgba(16, 185, 129, 0.1)', width: '64px', height: '64px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1.5rem', color: 'var(--accent-success)' }}>
            <Download size={32} />
          </div>
          <h3 style={{ fontSize: '1.5rem' }}>Receiver</h3>
          <p>Listen for connections, generate shared keys, and receive files.</p>
        </div>

        <div className="glass-card" style={{ textAlign: 'center', cursor: 'pointer' }} onClick={() => onNavigate('simulation')}>
          <div style={{ background: 'rgba(245, 158, 11, 0.1)', width: '64px', height: '64px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1.5rem', color: 'var(--accent-warning)' }}>
            <Activity size={32} />
          </div>
          <h3 style={{ fontSize: '1.5rem' }}>Simulation Mode</h3>
          <p>Visualize protocol steps and eavesdropping effects interactively.</p>
        </div>
      </div>
    </div>
  );
}
