#!/usr/bin/env python3
"""
WorkMonitor Web Server
A Flask-based web server for managing work sessions across multiple git repositories.
"""

import os
import sys
import json
import subprocess
import fcntl
from pathlib import Path
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Configuration
CONFIG_DIR = Path.home() / ".workmonitor"
CONFIG_FILE = CONFIG_DIR / "repositories.json"
LOCK_FILE = CONFIG_DIR / "monitorWork_server.lock"
DEFAULT_PORT = 5000

app = Flask(__name__, static_folder='.')
CORS(app)  # Enable CORS for local development

class SingleInstance:
    """Ensure only one instance of the server runs at a time."""
    def __init__(self, lock_file):
        self.lock_file = lock_file
        self.lock_fd = None
        
    def __enter__(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        
        try:
            self.lock_fd = open(self.lock_file, 'w')
            fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.lock_fd.write(str(os.getpid()))
            self.lock_fd.flush()
            return self
        except (IOError, OSError):
            print(f"Error: monitorWork_server.py is already running.")
            print(f"Check if another instance is running or remove {self.lock_file}")
            sys.exit(1)
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.lock_fd:
            try:
                fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_UN)
                self.lock_fd.close()
                if self.lock_file.exists():
                    self.lock_file.unlink()
            except:
                pass

def load_repositories():
    """Load repository list from file."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
                return data.get('repositories', [])
        except (json.JSONDecodeError, IOError):
            return []
    return []

def save_repositories(repositories):
    """Save repository list to file."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump({'repositories': repositories}, f, indent=2)
        return True
    except IOError as e:
        print(f"Error saving repositories: {e}")
        return False

@app.route('/')
def index():
    """Serve the main HTML file."""
    return send_from_directory('.', 'monitorWork.html')

@app.route('/api/scan-repositories', methods=['POST'])
def scan_repositories():
    """Scan a folder for git repositories."""
    try:
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
        
        data = request.json
        if not data:
            return jsonify({'error': 'Invalid request data'}), 400
        
        folder_path = data.get('folderPath', '').strip()
        
        if not folder_path:
            return jsonify({'error': 'Folder path is required'}), 400
        
        folder_path = os.path.abspath(os.path.expanduser(folder_path))
        
        # Security: prevent directory traversal outside home directory
        home_path = str(Path.home())
        if not folder_path.startswith(home_path):
            return jsonify({'error': 'Access denied: Cannot scan outside home directory'}), 403
        
        # Check if path exists
        if not os.path.exists(folder_path):
            # Try to suggest similar paths
            parent_dir = os.path.dirname(folder_path)
            suggested_paths = []
            if os.path.isdir(parent_dir):
                try:
                    for item in os.listdir(parent_dir):
                        item_path = os.path.join(parent_dir, item)
                        if os.path.isdir(item_path):
                            # Check if it's similar to what they typed
                            if 'git' in item.lower():
                                suggested_paths.append(item_path)
                except:
                    pass
            
            error_msg = f"Path does not exist: '{folder_path}'"
            if suggested_paths:
                error_msg += f"\nDid you mean one of these?\n" + "\n".join([f"  - {p}" for p in suggested_paths[:5]])
            return jsonify({'error': error_msg}), 400
        
        if not os.path.isdir(folder_path):
            return jsonify({'error': f"Path is not a directory: '{folder_path}'"}), 400
        
        # Scan for git repositories
        git_repos = []
        try:
            for item in os.listdir(folder_path):
                item_path = os.path.join(folder_path, item)
                if os.path.isdir(item_path) and os.path.isdir(os.path.join(item_path, '.git')):
                    git_repos.append({
                        'name': item,
                        'path': item_path
                    })
        except (OSError, PermissionError) as e:
            return jsonify({'error': f'Cannot access directory: {str(e)}'}), 403
        
        # Sort by name
        git_repos.sort(key=lambda x: x['name'])
        
        return jsonify({
            'folderPath': folder_path,
            'repositories': git_repos
        })
    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback.print_exc()
        return jsonify({'error': f'Server error: {error_msg}'}), 500

@app.route('/api/repositories', methods=['GET'])
def get_repositories():
    """Get list of repositories."""
    repositories = load_repositories()
    return jsonify({'repositories': repositories})

@app.route('/api/repositories', methods=['POST'])
def add_repository():
    """Add a new repository."""
    try:
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
        
        data = request.json
        if not data:
            return jsonify({'error': 'Invalid request data'}), 400
        
        path = data.get('path', '').strip()
        
        if not path:
            return jsonify({'error': 'Path is required'}), 400
        
        path = os.path.abspath(os.path.expanduser(path))
        
        # Check if it's a git repository
        if not os.path.isdir(os.path.join(path, '.git')):
            return jsonify({'error': f"'{path}' is not a git repository"}), 400
        
        repositories = load_repositories()
        
        # Check if already exists
        if any(r['path'] == path for r in repositories):
            return jsonify({'error': 'Repository already in list'}), 400
        
        # Add to list
        repositories.append({'path': path, 'selected': False})
        save_repositories(repositories)
        
        return jsonify({'repositories': repositories})
    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback.print_exc()
        return jsonify({'error': f'Server error: {error_msg}'}), 500

@app.route('/api/repositories', methods=['DELETE'])
def remove_repository():
    """Remove a repository."""
    data = request.json
    path = data.get('path', '')
    
    if not path:
        return jsonify({'error': 'Path is required'}), 400
    
    repositories = load_repositories()
    repositories = [r for r in repositories if r['path'] != path]
    save_repositories(repositories)
    
    return jsonify({'repositories': repositories})

@app.route('/api/repositories/clear', methods=['POST'])
def clear_repositories():
    """Clear all repositories from the list."""
    try:
        save_repositories([])
        # Verify it was cleared
        repositories = load_repositories()
        if len(repositories) > 0:
            return jsonify({'error': 'Failed to clear repositories'}), 500
        return jsonify({'repositories': [], 'message': 'All repositories cleared'})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error clearing repositories: {str(e)}'}), 500

@app.route('/api/repositories/batch-add', methods=['POST'])
def batch_add_repositories():
    """Add multiple repositories at once."""
    try:
        if not request.is_json:
            return jsonify({'error': 'Request must be JSON'}), 400
        
        data = request.json
        if not data:
            return jsonify({'error': 'Invalid request data'}), 400
        
        repo_paths = data.get('paths', [])
        
        if not isinstance(repo_paths, list):
            return jsonify({'error': 'Paths must be a list'}), 400
        
        repositories = load_repositories()
        existing_paths = {r['path'] for r in repositories}
        
        added_count = 0
        errors = []
        
        for path in repo_paths:
            path = path.strip()
            if not path:
                continue
                
            path = os.path.abspath(os.path.expanduser(path))
            
            # Check if it's a git repository
            if not os.path.isdir(os.path.join(path, '.git')):
                errors.append(f"'{path}' is not a git repository")
                continue
            
            # Check if already exists
            if path in existing_paths:
                continue  # Skip, already in list
            
            # Add to list
            repositories.append({'path': path, 'selected': False})
            existing_paths.add(path)
            added_count += 1
        
        save_repositories(repositories)
        
        return jsonify({
            'repositories': repositories,
            'added': added_count,
            'errors': errors
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/api/repositories/update', methods=['POST'])
def update_repositories():
    """Update repository list (for selection changes)."""
    data = request.json
    repositories = data.get('repositories', [])
    
    save_repositories(repositories)
    return jsonify({'repositories': repositories})

@app.route('/api/start-work', methods=['POST'])
def start_work():
    """Execute startWork for selected repositories."""
    data = request.json
    repositories = data.get('repositories', [])
    
    if not repositories:
        return jsonify({'error': 'No repositories selected'}), 400
    
    results = []
    errors = []
    
    for repo_path in repositories:
        try:
            result = subprocess.run(
                ['startWork', repo_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode != 0:
                errors.append(f"{repo_path}: {result.stderr}")
            else:
                results.append(repo_path)
        except FileNotFoundError:
            return jsonify({'error': 'startWork command not found. Please ensure it\'s installed and in your PATH.'}), 500
        except subprocess.TimeoutExpired:
            errors.append(f"{repo_path}: Timeout")
    
    return jsonify({
        'success': len(results),
        'errors': errors,
        'results': results
    })

@app.route('/api/stop-work', methods=['POST'])
def stop_work():
    """Execute stopWork for selected repositories."""
    data = request.json
    repositories = data.get('repositories', [])
    
    if not repositories:
        return jsonify({'error': 'No repositories selected'}), 400
    
    results = []
    errors = []
    
    for repo_path in repositories:
        try:
            result = subprocess.run(
                ['stopWork', repo_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode != 0:
                errors.append(f"{repo_path}: {result.stderr}")
            else:
                results.append(repo_path)
        except FileNotFoundError:
            return jsonify({'error': 'stopWork command not found. Please ensure it\'s installed and in your PATH.'}), 500
        except subprocess.TimeoutExpired:
            errors.append(f"{repo_path}: Timeout")
    
    return jsonify({
        'success': len(results),
        'errors': errors,
        'results': results
    })

@app.route('/api/tabulate-work', methods=['POST'])
def tabulate_work():
    """Execute tabulateWork for selected repositories."""
    data = request.json
    repositories = data.get('repositories', [])
    start_date = data.get('startDate', '')
    end_date = data.get('endDate', '')
    output_file = data.get('outputFile', '')
    
    if not repositories:
        return jsonify({'error': 'No repositories selected'}), 400
    
    if not start_date or not end_date:
        return jsonify({'error': 'Start date and end date are required'}), 400
    
    # Validate date format
    try:
        datetime.strptime(start_date, "%Y-%m-%d")
        datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        return jsonify({'error': 'Invalid date format. Please use YYYY-MM-DD format.'}), 400
    
    if not output_file:
        return jsonify({'error': 'Output file is required'}), 400
    
    # Expand ~ to home directory and convert to absolute path
    output_file = os.path.expanduser(output_file)
    output_file = os.path.abspath(output_file)
    
    try:
        # Build command
        cmd = ['tabulateWork', '-o', output_file, start_date, end_date] + repositories
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            return jsonify({'error': f"Failed to generate work report: {result.stderr}"}), 500
        
        return jsonify({
            'success': True,
            'outputFile': output_file,
            'message': f'Work report saved to {output_file}'
        })
    except FileNotFoundError:
        return jsonify({'error': 'tabulateWork command not found. Please ensure it\'s installed and in your PATH.'}), 500
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Timeout generating work report'}), 500

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='WorkMonitor Web Server')
    parser.add_argument('--port', type=int, default=DEFAULT_PORT,
                        help=f'Port to run the server on (default: {DEFAULT_PORT})')
    parser.add_argument('--host', default='127.0.0.1',
                        help='Host to bind to (default: 127.0.0.1)')
    args = parser.parse_args()
    
    with SingleInstance(LOCK_FILE):
        print(f"Starting WorkMonitor server on http://{args.host}:{args.port}")
        print("Open monitorWork.html in your browser or visit http://127.0.0.1:5000")
        print("Press Ctrl+C to stop the server")
        app.run(host=args.host, port=args.port, debug=False)

