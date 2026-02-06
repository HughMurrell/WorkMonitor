# WorkMonitor
A set of shell scripts that use github commits to record start and stop times for work sessions.

Here we plane to create shell scripts:

1. record START time when working on a repository 
2. generate csv file from the last commit of the day that records the hours worked that day.

## Installation

### Mac and Linux

1. **Clone or download this repository:**
   ```bash
   git clone https://github.com/HughMurrell/WorkMonitor.git
   cd WorkMonitor
   ```

2. **Make the script executable:**
   ```bash
   chmod +x startWork.sh
   ```

3. **Optional - Add to your PATH for global access:**
   
   For **Mac** (using zsh):
   ```bash
   echo 'export PATH="$PATH:/path/to/WorkMonitor"' >> ~/.zshrc
   source ~/.zshrc
   ```
   
   For **Linux** (using bash):
   ```bash
   echo 'export PATH="$PATH:/path/to/WorkMonitor"' >> ~/.bashrc
   source ~/.bashrc
   ```
   
   Replace `/path/to/WorkMonitor` with the actual path to the WorkMonitor directory.

4. **Verify installation:**
   ```bash
   ./startWork.sh
   ```
   
   You should see the usage message if the script is working correctly.

## Usage

Run the script with the path to your GitHub repository:

```bash
./startWork.sh /path/to/your/repository
```

Or with an optional message suffix:

```bash
./startWork.sh /path/to/your/repository "additional message"
```

The script will create an empty commit with a message starting with "START" and push it to GitHub.
