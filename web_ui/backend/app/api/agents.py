import asyncio
import base64
import os
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
    Provides a websocket interface to an agent's interactive mode.
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

        # Start the agent script in interactive mode
        # Note: We must use the system's Python interpreter.
        # This assumes `python` is in the PATH and points to the correct environment.
        # A more robust solution might involve getting the python executable from sys.executable
        # when the server starts.
        cmd = f"python -u {agent_full_path} --interactive"
        
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT, # Redirect stderr to stdout
            cwd=project_root
        )

        async def forward_to_ws():
            """Read from process stdout and forward to websocket."""
            while proc.stdout and not proc.stdout.at_eof():
                line = await proc.stdout.readline()
                if line:
                    await websocket.send_text(line.decode())
                else:
                    break
            await websocket.close()

        async def forward_to_proc():
            """Read from websocket and forward to process stdin."""
            while True:
                try:
                    data = await websocket.receive_text()
                    print(f"Received from WebSocket: {repr(data)}")  # Debug log
                    if proc.stdin:
                        # Convert \r to \n for proper line endings
                        if data == '\r':
                            data = '\n'
                        proc.stdin.write(data.encode())
                        await proc.stdin.drain()
                        # Force flush for immediate processing
                        if data == '\n':
                            proc.stdin.write(b'')  # Empty write to trigger flush
                            await proc.stdin.drain()
                        print(f"Sent to process: {repr(data)}")  # Debug log
                except WebSocketDisconnect:
                    break
        
        # Run both tasks concurrently
        task_to_ws = asyncio.create_task(forward_to_ws())
        task_to_proc = asyncio.create_task(forward_to_proc())

        await asyncio.gather(task_to_ws, task_to_proc)

    except Exception as e:
        await websocket.send_text(f"An error occurred: {e}")
    finally:
        if 'proc' in locals() and proc.returncode is None:
            proc.terminate()
            await proc.wait()
        if not websocket.client_state.value == 3: # i.e. not CLOSED
             await websocket.close() 