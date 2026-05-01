import asyncio
import socketio
import time

sio_sender = socketio.AsyncClient()
sio_receiver = socketio.AsyncClient()

async def test_qkd():
    await sio_receiver.connect('http://localhost:5001', namespaces=['/receiver'])
    await sio_sender.connect('http://localhost:5001', namespaces=['/sender'])
    
    @sio_receiver.on('status', namespace='/receiver')
    async def r_status(data):
        print("Receiver Status:", data)
        
    @sio_receiver.on('error', namespace='/receiver')
    async def r_error(data):
        print("Receiver Error:", data)
        
    @sio_sender.on('status', namespace='/sender')
    async def s_status(data):
        print("Sender Status:", data)
        
    @sio_sender.on('error', namespace='/sender')
    async def s_error(data):
        print("Sender Error:", data)
        
    @sio_sender.on('key_ready', namespace='/sender')
    async def s_ready(data):
        print("Sender Key Ready:", data)

    @sio_receiver.on('key_ready', namespace='/receiver')
    async def r_ready(data):
        print("Receiver Key Ready:", data)

    print("Starting receiver...")
    await sio_receiver.emit('start_receiver', namespace='/receiver')
    await asyncio.sleep(1)
    
    print("Sender connecting to receiver...")
    await sio_sender.emit('connect_to_receiver', {'ip': '127.0.0.1'}, namespace='/sender')
    await asyncio.sleep(1)
    
    print("Sender generating key...")
    await sio_sender.emit('generate_key', {'protocol': 'BB84', 'raw_bits': 256}, namespace='/sender')
    
    await asyncio.sleep(3)
    
    await sio_sender.disconnect()
    await sio_receiver.disconnect()

asyncio.run(test_qkd())
