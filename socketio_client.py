import socketio
import asyncio

# Configuration
SERVER_URL = 'http://localhost'
SERVER_PORT = 4768

# Use AsyncClient with explicit binary support
sio = socketio.AsyncClient(
    logger=True,
    engineio_logger=True,
    # Force websocket transport which handles binary better
    # or keep polling but ensure proper binary handling
)

@sio.event
async def connect():
    print(f'✅ Connected to server at {SERVER_URL}:{SERVER_PORT}')
    print(f'   Session ID: {sio.sid}')

    # Small delay to ensure connection is fully established
    await asyncio.sleep(0.1)

    # Emit registration message
    registration_data = {"type": "race-table"}
    print(f'📤 Registering client with data: {registration_data}')
    try:
        await sio.emit('register-client', registration_data)
        print('✅ Registration message sent')
    except Exception as e:
        print(f'❌ Failed to send registration: {e}')

@sio.event
async def disconnect():
    print('❌ Disconnected from server')

@sio.event
async def connect_error(data):
    print(f'❌ Connection error: {data}')

@sio.on('race-table-update')
async def on_race_table_update(data):
    # Handle the binary data here
    data_size = len(data) if isinstance(data, bytes) else 'N/A'
    print(f'📥 Received race-table-update (size: {data_size} bytes)')

    # Uncomment to decode msgpack data:
    import msgpack
    decoded = msgpack.unpackb(data)
    print(decoded.get("session-uid", "N/A"))

@sio.on('*')
async def catch_all(event, data):
    print(f'📨 Received event: {event}')

# Connect to the server
async def main():
    try:
        print(f'🔌 Connecting to {SERVER_URL}:{SERVER_PORT}...')

        # Try websocket first (better binary support)
        await sio.connect(
            f'{SERVER_URL}:{SERVER_PORT}',
            transports=['websocket', 'polling'],  # Try websocket first
            wait_timeout=10
        )

        # Keep the client running
        print('✅ Client is running. Press Ctrl+C to exit.\n')

        # Wait for events
        await sio.wait()

    except KeyboardInterrupt:
        print('\n❕ Shutting down client...')
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()
    finally:
        if sio.connected:
            await sio.disconnect()
            print('Connection closed')

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('\n❕ Interrupted')
