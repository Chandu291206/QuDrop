import os
import time
import asyncio
import mimetypes
import socketio
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from server.protocol_runner import ProtocolRunner
from bb84.bb84_core import estimate_qber, privacy_amplify, QBER_THRESHOLD, run_bb84_simulation
from network.connection import (
    connect_to_server, start_server, send_message, receive_message,
    send_list, receive_list, send_qber_sample, receive_qber_sample,
    send_file as send_file_bytes, receive_file
)
from encryption.xor_cipher import xor_encrypt, xor_decrypt

sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
fapi = FastAPI()

fapi.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
@fapi.get("/api/files")
async def get_files():
    public_dir = "public"
    if not os.path.exists(public_dir):
        return []
    files = []
    for f in os.listdir(public_dir):
        if os.path.isfile(os.path.join(public_dir, f)):
            files.append(f)
    return files

@fapi.get("/api/protocols")
async def get_protocols():
    return ["BB84", "B92", "E91", "Six-State"]

# Serve React static files in production
if os.path.exists("frontend/dist"):
    fapi.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")

app = socketio.ASGIApp(sio, other_asgi_app=fapi)

# Global State
tcp_sockets = {}
shared_keys = {}

def apply_channel_noise(bits, prob):
    import random
    noisy = []
    flips = 0
    for b in bits:
        if random.random() < prob:
            noisy.append(1 - b)
            flips += 1
        else:
            noisy.append(b)
    return noisy, flips

def compute_transfer_errors(reference_data, decrypted_data):
    if reference_data is None:
        return {"mode": "disabled", "message": "test disabled"}
        
    common_len = min(len(reference_data), len(decrypted_data))
    byte_errors = 0
    bit_errors = 0
    
    for i in range(common_len):
        ref_byte = reference_data[i]
        dec_byte = decrypted_data[i]
        if ref_byte != dec_byte:
            byte_errors += 1
            bit_errors += (ref_byte ^ dec_byte).bit_count()
            
    length_delta = abs(len(reference_data) - len(decrypted_data))
    byte_errors += length_delta
    bit_errors += length_delta * 8
    
    total_bytes = max(len(reference_data), len(decrypted_data))
    total_bits = total_bytes * 8
    
    return {
        "mode": "exact",
        "bit_errors": bit_errors,
        "total_bits": total_bits,
        "byte_errors": byte_errors,
        "total_bytes": total_bytes,
        "bit_error_rate_pct": (bit_errors / total_bits * 100.0) if total_bits else 0.0,
        "byte_error_rate_pct": (byte_errors / total_bytes * 100.0) if total_bytes else 0.0
    }

# --- SENDER NAMESPACE ---
@sio.on('connect', namespace='/sender')
async def sender_connect(sid, environ):
    pass

@sio.on('disconnect', namespace='/sender')
async def sender_disconnect(sid):
    if sid in tcp_sockets:
        try:
            tcp_sockets[sid].close()
        except:
            pass
        del tcp_sockets[sid]

@sio.on('connect_to_receiver', namespace='/sender')
async def sender_connect_receiver(sid, data):
    ip = data.get('ip')
    try:
        sock = await asyncio.to_thread(connect_to_server, ip)
        tcp_sockets[sid] = sock
        await sio.emit('status', {'message': 'Connected to receiver', 'level': 'success'}, namespace='/sender', to=sid)
    except Exception as e:
        await sio.emit('error', {'message': str(e)}, namespace='/sender', to=sid)

@sio.on('generate_key', namespace='/sender')
async def sender_generate_key(sid, data):
    sock = tcp_sockets.get(sid)
    if not sock:
        await sio.emit('error', {'message': 'Not connected to receiver'}, namespace='/sender', to=sid)
        return

    protocol = data.get('protocol', 'BB84')
    raw_bits = int(data.get('raw_bits', 256))
    noise_prob = float(data.get('noise_rate', 0.0)) if data.get('noise_enabled', False) else 0.0
    
    start_time = time.perf_counter()
    
    try:
        await sio.emit('status', {'message': f'Starting {protocol}...', 'level': 'info'}, namespace='/sender', to=sid)
        
        await asyncio.to_thread(send_message, sock, "START_QKD")
        await asyncio.to_thread(send_message, sock, protocol)
        
        alice_bits, alice_bases = ProtocolRunner.alice_generate(protocol, raw_bits)
        transmitted_bits = list(alice_bits)
        
        if noise_prob > 0:
            transmitted_bits, flips = apply_channel_noise(transmitted_bits, noise_prob)
            
        await asyncio.to_thread(send_list, sock, {
            "bits": transmitted_bits,
            "bases": alice_bases
        })
        
        bob_payload = await asyncio.to_thread(receive_list, sock)
        bob_bases = bob_payload["bases"]
        extra_data = bob_payload.get("extra_data")
        
        alice_sifted = ProtocolRunner.sift_key_alice(protocol, alice_bits, alice_bases, bob_bases, extra_data)
        
        if not alice_sifted:
            await sio.emit('key_aborted', {'reason': 'No sifted bits', 'qber': 0}, namespace='/sender', to=sid)
            return
            
        _, sample_indices, alice_remaining, _ = estimate_qber(alice_sifted, alice_sifted)
        alice_sample_bits = [alice_sifted[i] for i in sample_indices]
        await asyncio.to_thread(send_qber_sample, sock, sample_indices, alice_sample_bits)
        
        qber_payload = await asyncio.to_thread(receive_list, sock)
        qber = float(qber_payload.get("qber", 1.0))
        
        if qber > QBER_THRESHOLD:
            await sio.emit('key_aborted', {'reason': 'Eavesdropping detected', 'qber': qber}, namespace='/sender', to=sid)
            return
            
        final_key = privacy_amplify(alice_remaining)
        if not final_key:
            await sio.emit('key_aborted', {'reason': 'Privacy amplification failed', 'qber': qber}, namespace='/sender', to=sid)
            return
            
        shared_keys[sid] = final_key
        key_bits = len(final_key) * 8
        elapsed = max(time.perf_counter() - start_time, 1e-9)
        
        await sio.emit('key_ready', {
            'key_bits': key_bits,
            'qber': qber,
            'key_rate': key_bits / elapsed
        }, namespace='/sender', to=sid)
        
    except Exception as e:
        await sio.emit('error', {'message': f'Error during key generation: {str(e)}'}, namespace='/sender', to=sid)

@sio.on('send_file', namespace='/sender')
async def sender_send_file(sid, data):
    sock = tcp_sockets.get(sid)
    if not sock:
        return
        
    filename = data.get('filename')
    include_reference = data.get('include_reference', False)
    
    filepath = os.path.join("public", filename)
    try:
        with open(filepath, "rb") as f:
            file_data = f.read()
            
        encrypted = xor_encrypt(file_data, shared_keys[sid])
        
        await asyncio.to_thread(send_message, sock, "FILE_TRANSFER")
        await asyncio.to_thread(send_message, sock, filename)
        await asyncio.to_thread(send_list, sock, {"include_reference": include_reference})
        
        send_start = time.perf_counter()
        await asyncio.to_thread(send_file_bytes, sock, encrypted)
        if include_reference:
            await asyncio.to_thread(send_file_bytes, sock, file_data)
        send_elapsed = max(time.perf_counter() - send_start, 1e-9)
        
        result_payload = await asyncio.to_thread(receive_list, sock)
        
        await sio.emit('file_sent', {
            'send_rate': len(file_data) / send_elapsed,
            'result': result_payload
        }, namespace='/sender', to=sid)
    except Exception as e:
        await sio.emit('error', {'message': str(e)}, namespace='/sender', to=sid)


# --- RECEIVER NAMESPACE ---
@sio.on('disconnect', namespace='/receiver')
async def receiver_disconnect(sid):
    if sid in tcp_sockets:
        try:
            tcp_sockets[sid].close()
        except:
            pass
        del tcp_sockets[sid]

@sio.on('start_receiver', namespace='/receiver')
async def receiver_start(sid):
    sio.start_background_task(receiver_loop, sid)

async def receiver_loop(sid):
    try:
        sock = await asyncio.to_thread(start_server)
        tcp_sockets[sid] = sock
        await sio.emit('status', {'message': 'Sender connected. Waiting for protocol...', 'level': 'success'}, namespace='/receiver', to=sid)
        
        msg = await asyncio.to_thread(receive_message, sock)
        if msg != "START_QKD":
            return
            
        protocol = await asyncio.to_thread(receive_message, sock)
        await sio.emit('status', {'message': f'{protocol} session started', 'level': 'info'}, namespace='/receiver', to=sid)
        
        alice_data = await asyncio.to_thread(receive_list, sock)
        alice_bits = alice_data["bits"]
        alice_bases = alice_data["bases"]
        
        bob_bases, bob_results, extra_data = ProtocolRunner.bob_measure(protocol, alice_bits, alice_bases)
        
        await asyncio.to_thread(send_list, sock, {
            "bases": bob_bases,
            "extra_data": extra_data
        })
        
        bob_sifted = ProtocolRunner.sift_key_bob(protocol, bob_results, alice_bases, bob_bases, extra_data)
        sample_indices, alice_sample_bits = await asyncio.to_thread(receive_qber_sample, sock)
        
        if not sample_indices:
            qber = 0.0
            bob_remaining = bob_sifted
        else:
            valid_pairs = []
            for idx, a_bit in zip(sample_indices, alice_sample_bits):
                if 0 <= idx < len(bob_sifted):
                    valid_pairs.append((idx, a_bit))
            
            if not valid_pairs:
                qber = 1.0
                bob_remaining = []
            else:
                errors = sum(1 for idx, a_bit in valid_pairs if bob_sifted[idx] != a_bit)
                qber = errors / len(valid_pairs)
                sample_set = {idx for idx, _ in valid_pairs}
                bob_remaining = [bit for i, bit in enumerate(bob_sifted) if i not in sample_set]
                
        await asyncio.to_thread(send_list, sock, {"qber": qber})
        
        if qber > QBER_THRESHOLD:
            await sio.emit('key_aborted', {'reason': 'Eavesdropping detected', 'qber': qber}, namespace='/receiver', to=sid)
            return
            
        final_key = privacy_amplify(bob_remaining)
        if not final_key:
            await sio.emit('key_aborted', {'reason': 'Privacy amplification failed', 'qber': qber}, namespace='/receiver', to=sid)
            return
            
        shared_keys[sid] = final_key
        await sio.emit('key_ready', {
            'key_bits': len(final_key) * 8,
            'qber': qber,
            'key_rate': 0
        }, namespace='/receiver', to=sid)
        
        # Wait for file
        msg = await asyncio.to_thread(receive_message, sock)
        if msg == "FILE_TRANSFER":
            filename = await asyncio.to_thread(receive_message, sock)
            meta = await asyncio.to_thread(receive_list, sock)
            include_ref = meta.get("include_reference", False)
            
            receive_start = time.perf_counter()
            encrypted = await asyncio.to_thread(receive_file, sock)
            ref_data = await asyncio.to_thread(receive_file, sock) if include_ref else None
            receive_elapsed = max(time.perf_counter() - receive_start, 1e-9)
            
            decrypted = xor_decrypt(encrypted, shared_keys[sid])
            os.makedirs("received_files", exist_ok=True)
            with open(os.path.join("received_files", filename), "wb") as f:
                f.write(decrypted)
                
            result_payload = compute_transfer_errors(ref_data, decrypted)
            await asyncio.to_thread(send_list, sock, result_payload)
            
            await sio.emit('file_received', {
                'filename': filename,
                'receive_rate': len(encrypted) / receive_elapsed,
                'result': result_payload
            }, namespace='/receiver', to=sid)
            
    except Exception as e:
        await sio.emit('error', {'message': str(e)}, namespace='/receiver', to=sid)


# --- SIMULATION NAMESPACE ---
@sio.on('run_simulation', namespace='/simulation')
async def simulation_run(sid, data):
    protocol = data.get('protocol', 'BB84')
    n_bits = int(data.get('n_bits', 20))
    eve = data.get('eve', False)
    
    if protocol == "BB84":
        sim_data = run_bb84_simulation(n_bits, eve)
        await sio.emit('simulation_data', {'protocol': 'BB84', 'data': sim_data}, namespace='/simulation', to=sid)
    else:
        # Generic fast simulation for B92, E91, Six-State
        alice_bits, alice_bases = ProtocolRunner.alice_generate(protocol, n_bits)
        bob_bases, bob_results, extra_data = ProtocolRunner.bob_measure(protocol, alice_bits, alice_bases)
        
        alice_sifted = ProtocolRunner.sift_key_alice(protocol, alice_bits, alice_bases, bob_bases, extra_data)
        bob_sifted = ProtocolRunner.sift_key_bob(protocol, bob_results, alice_bases, bob_bases, extra_data)
        
        if len(alice_sifted) == 0 or len(bob_sifted) == 0:
            qber = 0
        else:
            errors = sum(1 for i in range(min(len(alice_sifted), len(bob_sifted))) if alice_sifted[i] != bob_sifted[i])
            qber = errors / min(len(alice_sifted), len(bob_sifted))
            
        await sio.emit('simulation_data', {
            'protocol': protocol,
            'summary': {
                'raw_bits': n_bits,
                'sifted_bits': len(alice_sifted),
                'qber': qber,
                'eavesdropping_detected': qber > QBER_THRESHOLD
            }
        }, namespace='/simulation', to=sid)

