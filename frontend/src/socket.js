import { io } from 'socket.io-client';

// In development, the backend runs on port 5001. In production, it runs on the same port as the frontend.
const SOCKET_URL = import.meta.env.DEV ? 'http://localhost:5001' : '/';

export const senderSocket = io(`${SOCKET_URL}/sender`, { autoConnect: false });
export const receiverSocket = io(`${SOCKET_URL}/receiver`, { autoConnect: false });
export const simulationSocket = io(`${SOCKET_URL}/simulation`, { autoConnect: false });
