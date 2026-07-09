#!/bin/bash
# Start FastAPI backend
python api.py &

# Serve React frontend on port 3000
python -m http.server 3000 --directory frontend/build &

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?
