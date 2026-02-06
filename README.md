# WorkMonitor
A set of shell scripts that use github commits to record start and stop times for work sessions.

Here we provide shell scripts that use

**startWork** record START time when working on a repository 
**stopWork** record STOP time after completing work on a repository
**tabulateWork** generate csv file tabulating work sessions

## Installation

### Mac and Linux

1. **Clone or download this repository:**
   ```bash
   git clone https://github.com/HughMurrell/WorkMonitor.git
   cd WorkMonitor
   ```

2. **Create the installation directory (if it doesn't exist):**
   ```bash
   mkdir -p ~/.local/bin
   ```

3. **Copy the scripts to ~/.local/bin and make them executable:**
   ```bash
   cp repoMonitor.sh ~/.local/bin/repoMonitor.sh
   cp startWork ~/.local/bin/startWork
   cp stopWork ~/.local/bin/stopWork
   chmod +x ~/.local/bin/repoMonitor.sh ~/.local/bin/startWork ~/.local/bin/stopWork
   ```

4. **Ensure ~/.local/bin is in your PATH:**
   
   The `~/.local/bin` directory is typically already in PATH on most Linux distributions. If it's not, or if you're on Mac, add it to your shell configuration:
   
   For **Mac** (using zsh):
   ```bash
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
   source ~/.zshrc
   ```
   
   For **Linux** (using bash):
   ```bash
   echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
   source ~/.bashrc
   ```

5. **Verify installation:**
   ```bash
   repoMonitor.sh
   ```
   
   You should see the usage message if the script is working correctly. You can also verify the wrapper scripts:
   ```bash
   startWork
   stopWork
   ```

6. **Optional - Delete the WorkMonitor repository:**
   
   Once the script is installed in `~/.local/bin`, you can delete the WorkMonitor repository as the script is now installed system-wide:
   ```bash
   cd ..
   rm -rf WorkMonitor
   ```

## Usage

You can use the wrapper scripts for a simpler interface, or call `repoMonitor.sh` directly:

### Using wrapper scripts (recommended):

**To start work:**
```bash
startWork /path/to/your/repository
```

**To stop work:**
```bash
stopWork /path/to/your/repository
```

### Using repoMonitor.sh directly:

**To start work:**
```bash
repoMonitor.sh start=/path/to/your/repository
```

**To stop work:**
```bash
repoMonitor.sh stop=/path/to/your/repository
```

The script will create an empty commit with the message:
- "START work on <repository>" when starting work
- "STOP work on <repository>" when stopping work

(where `<repository>` is the name of the repository extracted from the local git repository)

The commit will be pushed to GitHub automatically.
