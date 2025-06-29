import asyncio
import base64
import os
import pty
import select
import subprocess
import threading
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.agent_scanner import AgentScanner

router = APIRouter()

# Use the project root directory, assuming the backend is run from there.
# This needs to be robust. Let's calculate it based on this file's location.
# __file__ -> web_ui/backend/app/api/agents.py
# project_root -> FractFlow/
project_root = os.path.abspath(os.path.join(__file__, '../../../../../'))
scanner = AgentScanner(base_path=project_root)


@router.get("/agents")
async def get_agents():
    """
    Scans the 'tools' directory and returns a list of all found agents
    and their dependencies.
    """
    return scanner.scan_agents()


@router.websocket("/ws/{agent_path_encoded}")
async def websocket_endpoint(websocket: WebSocket, agent_path_encoded: str):
    """
    Provides a websocket interface to an agent's interactive mode using PTY.
    """
    await websocket.accept()
    
    try:
        agent_path_decoded = base64.urlsafe_b64decode(agent_path_encoded).decode()
        
        # Security check: Ensure the path is within the project's tools directory
        agent_full_path = os.path.abspath(os.path.join(project_root, agent_path_decoded))
        if not agent_full_path.startswith(os.path.abspath(os.path.join(project_root, 'tools'))):
            await websocket.send_text("Error: Access to this path is not allowed.")
            await websocket.close(code=1008)
            return

        if not os.path.exists(agent_full_path):
            await websocket.send_text(f"Error: Agent script not found at {agent_path_decoded}")
            await websocket.close(code=1008)
            return

        # Start the agent script in interactive mode using PTY
        cmd = f"python -u {agent_full_path} --interactive"
        
        print(f"[PTY] Starting command: {cmd}")
        
        # Create PTY
        master_fd, slave_fd = pty.openpty()
        
        # Start the process with PTY
        proc = subprocess.Popen(
            cmd,
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            shell=True,
            cwd=project_root,
            preexec_fn=os.setsid  # Create new session to handle signals properly
        )
        
        # Close slave end in parent process
        os.close(slave_fd)
        
        print(f"[PTY] Process started with PID: {proc.pid}")
        
        # Keep PTY echo ENABLED - this is essential for proper terminal simulation
        # The PTY should provide character echo just like a real terminal
        # Agent scripts expect terminal to handle character echo, not the application
        print("[PTY] Using default PTY settings with echo enabled (proper terminal behavior)")
        
        # Use asyncio to handle PTY communication
        loop = asyncio.get_event_loop()
        
        async def read_from_pty():
            """Read from PTY master and forward to websocket."""
            buffer = b''  # Buffer for incomplete UTF-8 sequences
            try:
                while proc.poll() is None:  # Process is still running
                    # Use select to check if data is available
                    ready, _, _ = select.select([master_fd], [], [], 0.1)
                    if ready:
                        try:
                            data = os.read(master_fd, 1024)
                            if data:
                                # Add to buffer
                                buffer += data
                                
                                # Try to decode the buffer
                                try:
                                    text = buffer.decode('utf-8')
                                    # If successful, send and clear buffer
                                    print(f"[PTY->WS] Sending: {repr(text)}")
                                    await websocket.send_text(text)
                                    buffer = b''
                                except UnicodeDecodeError as decode_error:
                                    # Keep incomplete sequences in buffer
                                    if decode_error.start == 0:
                                        # Error at beginning - might be incomplete sequence
                                        # Keep buffer and continue reading
                                        if len(buffer) > 10:  # Prevent buffer overflow
                                            # Send with error replacement if buffer gets too large
                                            text = buffer.decode('utf-8', errors='replace')
                                            print(f"[PTY->WS] Sending (with replacements): {repr(text)}")
                                            await websocket.send_text(text)
                                            buffer = b''
                                    else:
                                        # Send valid part, keep invalid part in buffer
                                        valid_part = buffer[:decode_error.start]
                                        invalid_part = buffer[decode_error.start:]
                                        
                                        if valid_part:
                                            text = valid_part.decode('utf-8')
                                            print(f"[PTY->WS] Sending valid part: {repr(text)}")
                                            await websocket.send_text(text)
                                        
                                        buffer = invalid_part
                            else:
                                break
                        except OSError as e:
                            print(f"[PTY] Read error: {e}")
                            break
                    else:
                        # Small delay to prevent busy waiting
                        await asyncio.sleep(0.01)
                        
                print("[PTY] Process ended, closing connection")
                await websocket.close()
                
            except Exception as e:
                print(f"[PTY] Read task error: {e}")
                await websocket.close()

        async def write_to_pty():
            """Read from websocket and forward to PTY master."""
            try:
                while proc.poll() is None:  # Process is still running
                    try:
                        data = await websocket.receive_text()
                        print(f"[WS->PTY] Received: {repr(data)}")
                        
                        # Encode to UTF-8 bytes for PTY
                        try:
                            encoded_data = data.encode('utf-8')
                            # Write to PTY master
                            os.write(master_fd, encoded_data)
                        except UnicodeEncodeError as e:
                            print(f"[PTY] Unicode encode error: {e}")
                            # Try with error replacement
                            encoded_data = data.encode('utf-8', errors='replace')
                            os.write(master_fd, encoded_data)
                        
                    except WebSocketDisconnect:
                        print("[PTY] WebSocket disconnected")
                        break
                    except Exception as e:
                        print(f"[PTY] Write error: {e}")
                        break
                        
            except Exception as e:
                print(f"[PTY] Write task error: {e}")

        # Run both tasks concurrently
        read_task = asyncio.create_task(read_from_pty())
        write_task = asyncio.create_task(write_to_pty())

        try:
            await asyncio.gather(read_task, write_task, return_exceptions=True)
        except Exception as e:
            print(f"[PTY] Task execution error: {e}")

    except Exception as e:
        print(f"[PTY] WebSocket endpoint error: {e}")
        await websocket.send_text(f"An error occurred: {e}")
    finally:
        # Cleanup
        if 'proc' in locals() and proc.poll() is None:
            print(f"[PTY] Terminating process {proc.pid}")
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
        
        if 'master_fd' in locals():
            try:
                os.close(master_fd)
                print("[PTY] Master FD closed")
            except OSError:
                pass
        
        # Ensure WebSocket is closed
        try:
            if websocket.client_state.value != 3:  # Not CLOSED
                await websocket.close()
        except Exception as e:
            print(f"[PTY] WebSocket close error: {e}") 