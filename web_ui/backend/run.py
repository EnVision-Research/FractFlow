import uvicorn
import os

if __name__ == "__main__":
    # Get the directory of the run.py script
    run_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Set the Python path to include the project root, which is one level above the 'web_ui' directory.
    # This ensures that imports like 'from FractFlow.tool_template' work correctly
    # when agent scripts are executed.
    project_root = os.path.abspath(os.path.join(run_dir, '../..'))
    
    # Add project root to PYTHONPATH if it's not already there
    python_path = os.environ.get('PYTHONPATH', '')
    if project_root not in python_path.split(os.pathsep):
        os.environ['PYTHONPATH'] = f"{project_root}{os.pathsep}{python_path}"

    uvicorn.run(
        "app.main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        # The reload_dirs will ensure that uvicorn restarts when any backend code changes.
        reload_dirs=[os.path.join(run_dir, 'app')]
    ) 