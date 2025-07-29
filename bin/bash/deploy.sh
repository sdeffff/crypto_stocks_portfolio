set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

cd "$PROJECT_ROOT"

source .venv/Scripts/activate

git pull origin main
source venv/bin/activate
pip install -r requirements.txt

tmux kill-session -t fastapi || true
tmux new-session -d -s fastapi "uvicorn main:app --host 0.0.0.0 --port 8000"