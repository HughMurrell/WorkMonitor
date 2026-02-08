# WorkMonitor
A set of shell scripts that use github commits to record start and stop times for work sessions.

Here we provide shell scripts that use

**startWork** record START time when working on a repository 
**stopWork** record STOP time after completing work on a repository
**tabulateWork** generate csv file tabulating work sessions during a period.

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
   cp tabulateWork ~/.local/bin/tabulateWork
   chmod +x ~/.local/bin/repoMonitor.sh ~/.local/bin/startWork ~/.local/bin/stopWork ~/.local/bin/tabulateWork
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
   tabulateWork
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

## Generating Work Reports

Use `tabulateWork` to generate a CSV report of work sessions from git commits across one or more repositories:

```bash
tabulateWork [-o output_file] <start_date> <stop_date> <repository_path> [repository_path2 ...]
```

**Parameters:**
- `-o output_file`: Optional output file (if omitted, output goes to stdout)
- `start_date`: Start date in format YYYY-MM-DD (inclusive)
- `stop_date`: Stop date in format YYYY-MM-DD (inclusive)
- `repository_path`: Path to a git repository (at least one required, multiple paths allowed)

**Examples:**

Generate a report for a single repository (output to stdout):
```bash
tabulateWork 2024-01-01 2024-01-31 /path/to/your/repository
```

Generate a report for multiple repositories and save to a file:
```bash
tabulateWork -o work_report.csv 2024-01-01 2024-01-31 /path/to/repo1 /path/to/repo2 /path/to/repo3
```

Generate a report and redirect to a file (alternative to `-o`):
```bash
tabulateWork 2024-01-01 2024-01-31 /path/to/repo1 /path/to/repo2 > work_report.csv
```

**Output:**
The script generates a CSV file with the following columns:
- `date`: Date of the work session (YYYY-MM-DD)
- `start_time`: Full datetime when work started (YYYY-MM-DD HH:MM:SS)
- `stop_time`: Full datetime when work stopped (YYYY-MM-DD HH:MM:SS)
- `duration`: Time elapsed between start and stop (HH:MM:SS format)
- `activity`: Repository name followed by ":" and a semicolon-separated list of all commit messages between start and stop commits

**Output behavior:**
- If `-o output_file` is specified, the CSV is written to that file
- If `-o` is omitted, the CSV is written to stdout (can be redirected with `>`)
- The output is automatically sorted by `start_time` in chronological order

The CSV file can be opened in spreadsheet applications like Excel, Google Sheets, or LibreOffice Calc for further analysis.

**Note:** The script pairs START and STOP commits to calculate work sessions. If a START commit doesn't have a matching STOP commit, it will be marked as "Unfinished session" with empty stop time and duration fields. Work sessions from all specified repositories are combined into a single CSV output, sorted chronologically by start time.
