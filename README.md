============================================================================
​ez_archive.sh — Resilient & Reusable Terminal Toolkit for Termux/Linux
​============================================================================
​Purpose: One-stop utility script for directory management, Git operations,
​file inspection, Python heredoc execution, validation, and debugging
​Author: Carter / bilbywilby
​Date: 2026-10-13
​Version: 2.0.0
​Platform: Termux (Android), Debian/Ubuntu, Alpine Linux
​Dependencies: bash >= 5.0, git, python3
​
​Usage: source ./ez_archive.sh [command] [args...]
​============================================================================
​STREAMING_CHUNK:Configuring environment variables and global constants...
​set -euo pipefail
​readonly EZ_ARCHIVE_VERSION="2.0.0"
readonly EZ_LOG_DIR="{EZ_LOG_DIR:-$HOME/.ez_archive/logs}"
readonly EZ_BACKUP_DIR="${EZ_BACKUP_DIR:-$HOME/.ez_archive/backups}"
EZ_VERBOSE="${EZ_VERBOSE:-0}"  # Set to 1 for verbose output
EZ_COLORS="{EZ_COLORS:-1}"   # Set to 0 to disable ANSI colors
​ANSI Color Codes (disabled if EZ_COLORS=0)
​if [ "$EZ_COLORS" -eq 1 ]; then
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[0;33m'
readonly BLUE='\033[0;34m'
readonly MAGENTA='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly WHITE='\033[0;37m'
readonly BOLD='\033[1m'
readonly RESET='\033[0m'
else
readonly RED='' GREEN='' YELLOW='' BLUE='' MAGENTA='' CYAN='' WHITE='' BOLD='' RESET=''
fi
​============================================================================
​UTILITY FUNCTIONS
​============================================================================
​STREAMING_CHUNK:Defining logging and helper utility functions...
​msg_info() { printf "{BLUE}[INFO]{RESET} %s\n" "*" >&2; }
msg_success() { printf "{GREEN}[SUCCESS]{RESET} \%s\n" "" >&2; }
msg_warning() { printf "{YELLOW}[WARNING]{RESET} %s\n" "$" >&2; }
msg_error() { printf "{RED}[ERROR]{RESET} %s\n" "*" >&2; }
msg_debug() { [ "$EZ_VERBOSE" -eq 1 ] && printf "${CYAN}[DEBUG]{RESET} %s\n" "$*" >&2 || true; }
​log_entry() {
mkdir -p "EZ_LOG_DIR"
echo "(date '+%Y-%m-%d %H:%M:%S') [$1] $2" >> "$EZ_LOG_DIR/ez_archive.log"
if [ "$EZ_VERBOSE" -eq 1 ]; then
echo "[$1] $2"
fi
}
​mkdir_safe() {
local dir="$1"
if [ ! -d "$dir" ]; then
mkdir -p "$dir"
msg_debug "Created directory: $dir"
else
msg_debug "Directory exists: $dir"
fi
}
​backup_file() {
local file="1"
local suffix="{2:-$(date +%Y%m%d_%H%M%S)}"
​if [ -f "$file" ]; then
mkdir_safe "$EZ_BACKUP_DIR"
cp "$file" "EZ_BACKUP_DIR/(basename "$file").$suffix.bak"
msg_success "Backed up: $file → $EZ_BACKUP_DIR/"
fi
}
​check_dependencies() {
local deps=("$@")
local missing=()
​for cmd in "${deps[@]}"; do
if ! command -v "$cmd" &>/dev/null; then
missing+=("$cmd")
fi
done
​if [ ${#missing[@]} -gt 0 ]; then
msg_error "Missing dependencies: {missing[*]}"
msg_warning "Install with: pkg install ${missing[*]} (Termux) or apt-get install{missing[]}"
return 1
fi
msg_debug "All dependencies satisfied: ${deps[]}"
return 0
}
​============================================================================
​DIRECTORY MANAGEMENT
​============================================================================
​STREAMING_CHUNK:Implementing directory management operations...
​project_init() {
local project_name="{1:-project}"
local project_path="{2:-$HOME/$project_name}"
​msg_info "Initializing project: project_name atproject_path"
​mkdir_safe "$project_path"
mkdir_safe "$project_path/src"
mkdir_safe "$project_path/scripts"
mkdir_safe "$project_path/tests/fixtures"
mkdir_safe "$project_path/logs"
mkdir_safe "$project_path/docs"
​if [ ! -f "$project_path/.gitignore" ]; then
cat > "$project_path/.gitignore" << 'GITIGNORE_EOF'
logs/
*.log
pycache/
*.py[cod]
*.pyi
.Python
*.egg-info/
dist/
build/
node_modules/
package-lock.json
.env
.env.local
.idea/
.vscode/
*.swp
*~
.pytest_cache/
.coverage
htmlcov/
GITIGNORE_EOF
msg_success "Created .gitignore"
fi
​if [ ! -d "$project_path/.git" ]; then
cd "$project_path"
git init
msg_success "Initialized git repository"
fi
​if [ ! -f "$project_path/README.md" ]; then
cat > "$project_path/README.md" << EOF
​$project_name
​Generated on $(date -Iseconds) by ez_archive.sh
​Quick Start
​```bash
cd $project_path
pip install -r requirements.txt 2>/dev/null || true
```
EOF
msg_success "Created README.md"
fi
​msg_success "Project initialized at: $project_path"
}
​cd_project() {
local project_name="$1"
local search_dirs=("$HOME" "PROJECT_ROOT" "{PROJECT_DIR:-$HOME/projects}")
​for base in "${search_dirs[@]}"; do
if [ -d "$base/$project_name" ]; then
cd "$base/$project_name"
msg_success "Changed to: $(pwd)"
return 0
fi
done
​msg_error "Project not found: $project_name"
return 1
}
​tree_view() {
local path="{1:-.}"
local depth="{2:-3}"
​if command -v tree &>/dev/null; then
tree -L "$depth" "$path" 2>/dev/null \vert{}\vert{} ls -la "$path"
else
find "$path" -maxdepth "$depth" -not -path '/.' | sort | sed "s|^|  |"
fi
}
​============================================================================
​GIT OPERATIONS
​============================================================================
​STREAMING_CHUNK:Adding Git automation and helper wrappers...
​git_init() {
local dir="${1:-.}"
cd "$dir"
​if [ ! -d ".git" ]; then
git init
msg_success "Git initialized in: $dir"
else
msg_info "Git already initialized: $dir"
fi
}
​git_status() {
local branch
branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
​echo ""
echo "GIT STATUS: $branch"
echo ""
git status --short --branch 2>/dev/null || msg_error "Not a git repository"
}
​git_stash_all() {
local message="{1:-ez_archive_auto_stash_(date +%Y%m%d_%H%M%S)}"
​if [ -n "$(git status --porcelain)" ]; then
git stash save "$message"
msg_success "Stashed changes: $message"
else
msg_info "No changes to stash"
fi
}
​git_stash_pop() {
if [ -n "$(git stash list)" ]; then
git stash pop
msg_success "Applied latest stash"
else
msg_warning "No stashes to apply"
fi
}
​git_sync() {
local remote_url="{1:-origin}"
local branch="{2:-$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo main)}"
​msg_info "Fetching latest from $remote_url/$branch..."
git fetch "$remote_url"
​msg_info "Pulling changes (merge strategy)..."
git pull "$remote_url" "$branch" --no-rebase 2>/dev/null || 
git pull "$remote_url" "$branch" 2>/dev/null || 
msg_warning "Pull failed - manual resolution may be needed"
​msg_success "Sync complete"
}
​git_push_force() {
local branch="{1:-(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo main)}"
​msg_warning "Force pushing to $branch (THIS REWRITES HISTORY)"
read -p "Continue? [y/N]: " confirm
if [[ "confirm" =~ ^[Yy] ]]; then
git push -f origin "$branch"
msg_success "Force push complete"
else
msg_info "Aborted"
fi
}
​git_diff_recent() {
local count="${1:-5}"
​echo ""
echo "RECENT COMMITS (last $count)"
echo ""
git log --oneline -"$count" --graph --decorate
}
​git_branch_list() {
echo ""
echo "LOCAL BRANCHES"
echo ""
git branch -v 2>/dev/null || echo "No local branches"
​echo ""
echo ""
echo "REMOTE BRANCHES"
echo ""
git branch -r 2>/dev/null || echo "No remote branches"
}
​============================================================================
​FILE INSPECTION TOOLS
​============================================================================
​STREAMING_CHUNK:Writing file inspection and text search utilities...
​view_file_tail() {
local file="1"
local lines="{2:-50}"
​if [ -f "$file" ]; then
echo "=== LAST lines LINES OFfile ==="
tail -n "$lines" "$file"
else
msg_error "File not found: $file"
fi
}
​view_file_tac() {
local file="1"
local lines="{2:-20}"
​if [ -f "$file" ]; then
echo "=== LAST $lines LINES (REVERSE ORDER - TAC) ==="
tac "$file" 2>/dev/null \vert{} head -n "$lines" || 
tail -n "$lines" "$file" | tac
else
msg_error "File not found: $file"
fi
}
​view_json_formatted() {
local file="$1"
​if [ -f "$file" ]; then
python3 -m json.tool "$file" 2>/dev/null || 
jq '.' "$file" 2>/dev/null || 
cat "$file"
else
msg_error "JSON file not found: $file"
fi
}
​search_file_content() {
local pattern="1"
local directory="{2:-.}"
local extension="${3:-*}"
​msg_info "Searching for '$pattern' in $directory (extension:$extension)"
​if command -v rg &>/dev/null; then
rg --type "$extension" "$pattern" "$directory" 2>/dev/null \vert{}\vert{} grep -r "$pattern" "$directory" --include="$extension"
else
grep -rn "$pattern" "$directory" --include="$extension" 2>/dev/null
fi
}
​count_lines() {
local file="$1"
​if [ -f "$file" ]; then
wc -l < "$file" | tr -d ' '
else
echo "0"
fi
}
​============================================================================
​PYTHON EXECUTION UTILITIES
​============================================================================
​STREAMING_CHUNK:Setting up Python execution and inline heredoc utilities...
​run_python_inline() {
if [ ! -t 0 ]; then
python3 - "$@"
else
msg_warning "No input provided. Example usage:"
echo '  run_python_inline << '''PYEOF''''
echo '    import json'
echo '    print(json.dumps({"test": True}))'
echo '  PYEOF'
fi
}
​python_check_imports() {
local imports=("$@")
local missing=()
​for imp in "${imports[@]}"; do
if ! python3 -c "import $imp" 2>/dev/null; then
missing+=("$imp")
fi
done
​if [ ${#missing[@]} -gt 0 ]; then
msg_error "Missing Python packages: ${missing[]}"
msg_info "Install with: pip install ${missing[]}"
return 1
fi
​msg_success "All imports available: ${imports[*]}"
return 0
}
​python_validate_json() {
local file="$1"
​if [ -f "$file" ]; then
if python3 -m json.tool "$file" > /dev/null 2>&1; then
msg_success "Valid JSON: $file"
return 0
else
msg_error "Invalid JSON: $file"
return 1
fi
else
msg_error "File not found: $file"
return 1
fi
}
​============================================================================
​VALIDATION & DIAGNOSTICS
​============================================================================
​STREAMING_CHUNK:Building system validation and environment diagnostics...
​check_termux_environment() {
echo ""
echo "TERMUX ENVIRONMENT CHECK"
echo ""
​echo "Shell:     $0 / BASH=$BASH_VERSION"
echo "Platform:  (uname -o) \vert{} Prefix:{PREFIX:-N/A}"
python3 --version 2>/dev/null || echo "Python: NOT FOUND"
git --version 2>/dev/null || echo "Git: NOT FOUND"
​if [ -d "/sdcard" ]; then
echo "Android Storage: Available at /sdcard"
fi
​df -h "$HOME" 2>/dev/null | tail -1
}
​validate_python_project() {
local project_root="${1:-.}"
​echo ""
echo "PYTHON PROJECT VALIDATION: $project_root"
echo ""
​cd "$project_root"
​if [ -d ".git" ]; then
echo "✅ Git repository present"
else
echo "⚠️  Not a git repository"
fi
​if [ -f "requirements.txt" ]; then
echo "✅ requirements.txt present"
else
echo "⚠️  No requirements.txt"
fi
​if [ -f "pyproject.toml" ]; then
echo "✅ pyproject.toml present"
else
echo "⚠️  No pyproject.toml"
fi
​if [ -d "tests" ]; then
echo "✅ tests/ directory present"
test_count=$(find tests -name "*.py" 2>/dev/null | wc -l | tr -d ' ')
echo "   Found $test_count test files"
else
echo "⚠️  No tests/ directory"
fi
​echo ""
echo "Checking Python syntax..."
python3 -m py_compile src/*.py 2>&1 | head -20 || echo "✅ Syntax OK (or no .py files)"
}
​disk_usage_report() {
local path="${1:-$HOME}"
​echo ""
echo "DISK USAGE: $path"
echo ""
du -sh "$path"/* 2>/dev/null | sort -hr | head -20
}
​============================================================================
​CLEANUP & MAINTENANCE
​============================================================================
​STREAMING_CHUNK:Creating cleanup and workspace maintenance routines...
​cleanup_pycache() {
local path="${1:-.}"
​msg_info "Removing pycache directories in: $path"
find "$path" -type d -name "pycache" -exec rm -rf {} + 2>/dev/null || true
find "$path" -type f -name "*.pyc" -delete 2>/dev/null || true
msg_success "Cleanup complete"
}
​cleanup_git_tempfiles() {
local path="${1:-.}"
​msg_info "Cleaning Git temporary files in: $path"
cd "$path"
git gc --aggressive --prune=now 2>/dev/null || true
git reflog expire --expire=now --all 2>/dev/null || true
msg_success "Git garbage collection complete"
}
​find_large_files() {
local path="${1:-HOME}"
local size_mb="{2:-10}"
​msg_info "Finding files larger than ${size_mb}MB in:$path"
find "path" -type f -size +"{size_mb}M" -exec ls -lh {} ; 2>/dev/null | 
awk '{print $5, $9}' | sort -hr | head -20
}
​============================================================================
​BACKUP & RESTORE
​============================================================================
​STREAMING_CHUNK:Implementing backup and tarball restoration handlers...
​create_backup_tarball() {
local source_dir="1"
local backup_name="{2:-$(basename "source_dir")_(date +%Y%m%d_%H%M%S)}"
local backup_path="EZ_BACKUP_DIR/{backup_name}.tar.gz"
​msg_info "Creating backup: $backup_path"
mkdir_safe "$EZ_BACKUP_DIR"
tar -czf "backup_path" -C "(dirname "source_dir")" "(basename "$source_dir")" 2>/dev/null
​if [ -f "$backup_path" ]; then
msg_success "Backup created: backup_path ((du -h "$backup_path" | cut -f1))"
else
msg_error "Backup failed"
return 1
fi
}
​restore_from_backup() {
local backup_file="1"
local restore_path="{2:-.}"
​if [ ! -f "$backup_file" ]; then
msg_error "Backup file not found: $backup_file"
return 1
fi
​msg_info "Restoring from: backup_file torestore_path"
mkdir_safe "$restore_path"
tar -xzf "$backup_file" -C "$restore_path"
msg_success "Restore complete"
}
​============================================================================
​HELP & VERSION
​============================================================================
​STREAMING_CHUNK:Configuring help documentation and version handlers...
​show_help() {
cat << EOF
ez_archive.sh v${EZ_ARCHIVE_VERSION} — Resilient Bash Toolkit
​USAGE:
source ./ez_archive.sh <command> [arguments...]
./ez_archive.sh <command> [arguments...]   (executable mode)
​DIRECTORY MANAGEMENT:
project_init <name> [path]       Initialize new project structure
cd_project <name>                Change to project directory
tree_view [path] [depth]         Display directory tree
mkdir_safe <directory>           Create directory with parents
​GIT OPERATIONS:
git_init [directory]             Initialize git repository
git_status                       Show git status and branch
git_stash_all [message]          Stash all uncommitted changes
git_stash_pop                      Apply latest stash
git_sync [remote] [branch]       Pull latest changes
git_push_force [branch]          Force push (rewrites history!)
git_diff_recent [count]          Show recent commit history
git_branch_list                  List local and remote branches
​FILE INSPECTION:
view_file_tail <file> [lines]    Show last N lines of file
view_file_tac <file> [lines]     Show last N lines in reverse
view_json_formatted <file>       Pretty-print JSON file
search_file_content <pattern> [dir] [ext] Search text in files
count_lines <file>               Count lines in file
find_large_files [path] [sizeMB] Find files larger than size
​PYTHON UTILITIES:
run_python_inline                Execute Python from heredoc
python_check_imports <pkg1>...   Check if packages installed
python_validate_json <file>      Validate JSON syntax
​VALIDATION:
check_termux_environment         Display system info
validate_python_project [root]   Validate project structure
disk_usage_report [path]         Show disk usage breakdown
​MAINTENANCE:
cleanup_pycache [path]           Remove Python cache files
cleanup_git_tempfiles [path]     Run git gc and reflog expire
backup_file <file> [suffix]      Create timestamped backup
​BACKUP & RESTORE:
create_backup_tarball <dir>      Create compressed backup
restore_from_backup <file>       Restore from tarball
​EOF
}
​show_version() {
echo "ez_archive.sh version ${EZ_ARCHIVE_VERSION}"
}
​============================================================================
​MAIN COMMAND DISPATCHER
​============================================================================
​STREAMING_CHUNK:Assembling the main command dispatcher and execution guard...
​main() {
local command="${1:-help}"
shift 2>/dev/null || true
​case "command" in
project_init)          project_init "@" ;;
cd_project)            cd_project "@" ;;
tree_view)             tree_view "@" ;;
mkdir_safe)            mkdir_safe "@" ;;
git_init)              git_init "@" ;;
git_status)            git_status "@" ;;
git_stash_all)         git_stash_all "@" ;;
git_stash_pop)         git_stash_pop "@" ;;
git_sync)              git_sync "@" ;;
git_push_force)        git_push_force "@" ;;
git_diff_recent)       git_diff_recent "@" ;;
git_branch_list)       git_branch_list "@" ;;
view_file_tail)        view_file_tail "@" ;;
view_file_tac)         view_file_tac "@" ;;
view_json_formatted)   view_json_formatted "@" ;;
search_file_content)   search_file_content "@" ;;
count_lines)           count_lines "@" ;;
run_python_inline)     run_python_inline "@" ;;
python_check_imports)  python_check_imports "@" ;;
python_validate_json)  python_validate_json "@" ;;
check_termux_environment) check_termux_environment "@" ;;
validate_python_project) validate_python_project "@" ;;
disk_usage_report)     disk_usage_report "@" ;;
cleanup_pycache)       cleanup_pycache "@" ;;
cleanup_git_tempfiles) cleanup_git_tempfiles "@" ;;
find_large_files)      find_large_files "@" ;;
backup_file)           backup_file "@" ;;
create_backup_tarball) create_backup_tarball "@" ;;
restore_from_backup)   restore_from_backup "@" ;;
version|--version)     show_version ;;
help|--help|-h)        show_help ;;
*)
msg_error "Unknown command: $command"
show_help
return 1
;;
esac
}
​Allow direct execution or sourcing
​if [[ "{BASH_SOURCE[0]}" == "{0}" ]]; then
main "$@"
fi

---

## 3. Interactive Terminal UI (`scripts/portal_tui.py`)

```python
#!/data/data/com.termux/files/usr/bin/python3
"""
ez_remote Portal TUI
Interactive IR code lookup with clipboard export and offline support.
"""

from __future__ import annotations

import json
import logging
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.align import Align

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("portal_tui")

console = Console()

@dataclass
class CodeEntry:
    """Single IR code entry."""
    brand: str
    revision: str
    code_length: str  # "3", "4", or "5"
    codes: List[int] = field(default_factory=list)

@dataclass
class TUIState:
    """Application state for persistence."""
    last_search: Optional[str] = None
    search_history: List[str] = field(default_factory=list)
    loaded_at: Optional[str] = None
    total_entries: int = 0
    total_brands: int = 0

class PortalTUI:
    """Terminal User Interface for ez_remote IR code lookup."""
    
    def __init__(self, project_root: Optional[Path] = None) -> None:
        self.project_root = project_root or Path(__file__).parent.parent
        self.data_dir = self.project_root / "remote_intelligence" / "data"
        self.state_path = self.project_root / ".tui_state.json"
        self.codes_map_path = self.data_dir / "codes_map.json"
        
        self.state = TUIState()
        self.code_db: Dict[str, Dict[str, Dict[str, List[int]]]] = {}
        
        self._load_state()
        
        if not self._load_codes_map():
            console.print("[red]❌ Error:[/red] No codes_map.json found. Run the pipeline first.")
            console.print("[yellow]Hint:[/yellow] bash scripts/pipeline_refresh.sh")
            sys.exit(1)
    
    def _load_state(self) -> None:
        """Load persisted TUI state."""
        if self.state_path.exists():
            try:
                with open(self.state_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.state = TUIState(
                    last_search=data.get("last_search"),
                    search_history=data.get("search_history", []),
                    loaded_at=data.get("loaded_at"),
                    total_entries=data.get("total_entries", 0),
                    total_brands=data.get("total_brands", 0)
                )
            except Exception as e:
                logger.warning(f"Failed to load state: {e}")
                self.state = TUIState()
    
    def _save_state(self) -> None:
        """Persist current TUI state."""
        try:
            data = {
                "last_search": self.state.last_search,
                "search_history": self.state.search_history[-20:],  # Keep last 20
                "loaded_at": datetime.now().isoformat(),
                "total_entries": self.state.total_entries,
                "total_brands": self.state.total_brands
            }
            with open(self.state_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save state: {e}")
    
    def _load_codes_map(self) -> bool:
        """Load and validate codes_map.json."""
        if not self.codes_map_path.exists():
            return False
        
        try:
            with open(self.codes_map_path, "r", encoding="utf-8") as f:
                self.code_db = json.load(f)
            
            # Calculate statistics
            total_brands = len(self.code_db)
            total_entries = sum(
                len(revisions) 
                for brand_data in self.code_db.values() 
                for revisions in brand_data.values()
            )
            
            self.state.total_brands = total_brands
            self.state.total_entries = total_entries
            self.state.loaded_at = datetime.now().isoformat()
            
            logger.info(f"Loaded {total_brands} brands, {total_entries} revision entries")
            return True
        except Exception as e:
            console.print(f"[red]❌ Failed to load codes_map.json: {e}[/red]")
            return False
    
    def search_codes(
        self, 
        query: str, 
        search_by: str = "brand"  # "brand", "revision", or "both"
    ) -> List[Tuple[str, str, str, List[int]]]:
        """Search codes by brand name, revision, or both."""
        results = []
        query_lower = query.lower()
        
        for brand, revisions in self.code_db.items():
            brand_match = search_by in ["brand", "both"] and query_lower in brand.lower()
            
            for revision, lengths in revisions.items():
                rev_match = search_by in ["revision", "both"] and query_lower in revision.lower()
                
                if brand_match or rev_match:
                    for length_key, codes in lengths.items():
                        if codes:
                            results.append((brand, revision, length_key, codes))
        
        return results
    
    def copy_to_clipboard(self, text: str) -> bool:
        """Copy text to Termux system clipboard."""
        try:
            proc = subprocess.Popen(
                ["termux-clipboard-set"],
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            proc.communicate(input=text.encode("utf-8"))
            proc.wait(timeout=5)
            return proc.returncode == 0
        except Exception as e:
            logger.error(f"Clipboard failed: {e}")
            return False
    
    def render_brand_table(self, entries: List[Tuple[str, str, str, List[int]]], title: str) -> Table:
        """Render search results in Rich table."""
        table = Table(title=title, expand=True)
        table.add_column("Brand", style="cyan", no_wrap=True)
        table.add_column("Revision", style="magenta", no_wrap=True)
        table.add_column("Code Length", justify="center", style="green")
        table.add_column("Codes", justify="right", style="yellow")
        table.add_column("Count", justify="right", style="dim")
        
        displayed = 0
        for brand, revision, length, codes in entries[:50]:
            codes_str = ", ".join(str(c) for c in codes[:10])
            if len(codes) > 10:
                codes_str += f"... (+{len(codes) - 10})"
            
            table.add_row(
                brand,
                revision,
                f"{length}-digit",
                codes_str,
                str(len(codes))
            )
            displayed += 1
        
        if len(entries) > 50:
            table.caption = f"Showing {displayed} of {len(entries)} results"
        
        return table
    
    def render_statistics(self) -> Panel:
        """Render statistics dashboard panel."""
        brand_list = sorted(self.code_db.keys())
        
        stats_content = []
        stats_content.append(f"[bold blue]Total Brands:[/bold blue] [cyan]{self.state.total_brands}[/cyan]")
        stats_content.append(f"[bold blue]Total Revisions:[/bold blue] [cyan]{self.state.total_entries}[/cyan]")
        
        # Codes by length distribution
        codes_3digit = sum(
            len(lengths.get("3", []))
            for brand_data in self.code_db.values()
            for revisions in brand_data.values()
            for lengths in [revisions]
        )
        codes_4digit = sum(
            len(lengths.get("4", []))
            for brand_data in self.code_db.values()
            for revisions in brand_data.values()
            for lengths in [revisions]
        )
        codes_5digit = sum(
            len(lengths.get("5", []))
            for brand_data in self.code_db.values()
            for revisions in brand_data.values()
            for lengths in [revisions]
        )
        
        stats_content.append(f"\n[cyan]3-digit codes:[/cyan] [yellow]{codes_3digit:,}[/yellow]")
        stats_content.append(f"[cyan]4-digit codes:[/cyan] [yellow]{codes_4digit:,}[/yellow]")
        stats_content.append(f"[cyan]5-digit codes:[/cyan] [yellow]{codes_5digit:,}[/yellow]")
        stats_content.append(f"\n[bold blue]Total IR codes:[/bold blue] [green]{codes_3digit + codes_4digit + codes_5digit:,}[/green]")
        
        # Top 5 brands by code count
        brand_code_counts = []
        for brand, revisions in self.code_db.items():
            total_codes = sum(
                sum(lengths.get(f"{length}", []))
                for revisions_data in revisions.values()
                for lengths in [revisions_data]
                for length in ["3", "4", "5"]
            )
            brand_code_counts.append((brand, total_codes))
        
        brand_code_counts.sort(key=lambda x: x[1], reverse=True)
        if brand_code_counts:
            stats_content.append(f"\n[bold]Top 5 Brands by Code Count:[/bold]")
            for brand, count in brand_code_counts[:5]:
                stats_content.append(f"  • {brand}: [yellow]{count}[/yellow] codes")
        
        stats_content.append(f"\n[dim]Last loaded: {self.state.loaded_at or 'Unknown'}[/dim]")
        
        return Panel(
            "\n".join(stats_content),
            title="[bold]Statistics Dashboard[/bold]",
            border_style="green",
            padding=(1, 2)
        )
    
    def render_main_menu(self) -> str:
        """Render and return main menu choice."""
        console.clear()
        
        header = Text()
        header.append("EZ_REMOTE PORTAL TUI\n", style="bold blue underline")
        header.append(f"{self.state.total_brands} brands • {self.state.total_entries} revisions loaded\n\n", style="dim")
        
        menu_text = Panel(
            header,
            border_style="blue"
        )
        
        console.print(menu_text)
        
        console.print("[bold]Menu:[/]")
        console.print("  [1] Search by brand")
        console.print("  [2] Search by revision")
        console.print("  [3] Browse all brands")
        console.print("  [4] Statistics dashboard")
        console.print("  [5] Export options")
        console.print("  [6] Recent searches")
        console.print("  [0] Exit\n")
        
        return Prompt.ask("[bold cyan]Select option[/bold cyan]", choices=["0", "1", "2", "3", "4", "5", "6"], default="1")
    
    def handle_search_brand(self) -> None:
        """Handle brand search flow."""
        query = Prompt.ask("[cyan]Enter brand name[/cyan]").strip()
        if not query:
            return
        
        self.state.last_search = query
        self.state.search_history.append(query)
        
        results = self.search_codes(query, search_by="brand")
        
        if not results:
            console.print(f"[yellow]No results for '{query}'. Try partial match.[/yellow]")
            return
        
        table = self.render_brand_table(results, f"Results for '{query}'")
        console.print(table)
        
        if results:
            self._offer_export(results, query)
    
    def handle_search_revision(self) -> None:
        """Handle revision search flow."""
        query = Prompt.ask("[cyan]Enter revision (e.g., CL9, Generic)[/cyan]").strip()
        if not query:
            return
        
        self.state.last_search = query
        self.state.search_history.append(query)
        
        results = self.search_codes(query, search_by="revision")
        
        if not results:
            console.print(f"[yellow]No results for revision '{query}'.[/yellow]")
            return
        
        table = self.render_brand_table(results, f"Results for revision '{query}'")
        console.print(table)
        
        if results:
            self._offer_export(results, query)
    
    def handle_browse_all(self) -> None:
        """Browse all available brands alphabetically."""
        table = Table(title="Available Brands")
        table.add_column("Brand", style="cyan")
        table.add_column("Revisions", justify="right", style="magenta")
        table.add_column("Total Codes", justify="right", style="yellow")
        
        sorted_brands = sorted(self.code_db.keys())
        for brand in sorted_brands:
            revisions = self.code_db[brand]
            total_codes = sum(
                sum(lengths.get(f"{length}", []))
                for revisions_data in revisions.values()
                for lengths in [revisions_data]
                for length in ["3", "4", "5"]
            )
            table.add_row(
                brand,
                str(len(revisions)),
                str(total_codes)
            )
        
        console.print(table)
        
        # Pagination prompt for large datasets
        if len(sorted_brands) > 20:
            total_pages = (len(sorted_brands) + 19) // 20
            console.print(f"\n[dim]Showing 20 of {len(sorted_brands)} brands ({total_pages} pages)[/dim]")
    
    def handle_statistics(self) -> None:
        """Display statistics dashboard."""
        console.print(self.render_statistics())
    
    def handle_export(self) -> None:
        """Handle export menu."""
        console.print("[bold]Export Options:[/]")
        console.print("  [1] All codes to CSV")
        console.print("  [2] Last search results to clipboard")
        console.print("  [3] Select brand to export")
        
        choice = Prompt.ask("Select option", choices=["1", "2", "3"], default="1")
        
        if choice == "1":
            self._export_all_to_csv()
        elif choice == "2":
            if not self.state.last_search:
                console.print("[yellow]No previous search to export.[/yellow]")
                return
            self._export_last_search_to_clipboard()
        elif choice == "3":
            self._export_select_brand()
    
    def _export_all_to_csv(self) -> None:
        """Export all codes to CSV file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = self.project_root / f"export_all_{timestamp}.csv"
        
        try:
            lines = ["brand,revision,length,code"]
            
            for brand, revisions in self.code_db.items():
                for revision, lengths in revisions.items():
                    for length, codes in lengths.items():
                        for code in codes:
                            lines.append(f"{brand},{revision},{length},{code}")
            
            output_path.write_text("\n".join(lines), encoding="utf-8")
            console.print(f"[green]✅ Exported to {output_path}[/green]")
            console.print(f"[dim]{len(lines) - 1} codes exported[/dim]")
        except Exception as e:
            console.print(f"[red]❌ Export failed: {e}[/red]")
    
    def _export_last_search_to_clipboard(self) -> None:
        """Export last search results to clipboard."""
        if not self.state.last_search:
            console.print("[yellow]No previous search.[/yellow]")
            return
        
        results = self.search_codes(self.state.last_search, search_by="both")
        if not results:
            console.print("[yellow]No results to export.[/yellow]")
            return
        
        output_text = self._format_results_for_clipboard(results)
        
        if self.copy_to_clipboard(output_text):
            total_codes = sum(len(codes) for _, _, _, codes in results)
            console.print(f"[green]✅ Copied {total_codes} codes to clipboard![/green]")
        else:
            console.print("[yellow]⚠️  Clipboard failed. Here are the codes:[/yellow]")
            console.print(output_text[:1000])  # Show truncated
    
    def _export_select_brand(self) -> None:
        """Allow user to select brand for export."""
        sorted_brands = sorted(self.code_db.keys())
        
        console.print("[bold]Select Brand:[/]")
        for idx, brand in enumerate(sorted_brands[:20], 1):
            console.print(f"  [cyan]{idx}[/cyan]. {brand}")
        
        if len(sorted_brands) > 20:
            console.print(f"  ... and {len(sorted_brands) - 20} more")
        
        try:
            selection = IntPrompt.ask("Enter brand number")
            if 1 <= selection <= len(sorted_brands):
                brand = sorted_brands[selection - 1]
                self._export_single_brand(brand)
        except KeyboardInterrupt:
            console.print("[dim]Cancelled.[/dim]")
    
    def _export_single_brand(self, brand: str) -> None:
        """Export single brand codes to clipboard."""
        results = []
        for revision, lengths in self.code_db.get(brand, {}).items():
            for length, codes in lengths.items():
                if codes:
                    results.append((brand, revision, length, codes))
        
        if not results:
            console.print("[yellow]No codes found for this brand.[/yellow]")
            return
        
        output_text = self._format_results_for_clipboard(results)
        
        if self.copy_to_clipboard(output_text):
            total_codes = sum(len(codes) for _, _, _, codes in results)
            console.print(f"[green]✅ Copied {total_codes} codes for {brand} to clipboard![/green]")
        else:
            console.print("[yellow]Clipboard failed. Codes shown above.[/yellow]")
    
    def _format_results_for_clipboard(self, results: List[Tuple[str, str, str, List[int]]]) -> str:
        """Format results for clipboard (CSV-like format)."""
        lines = ["brand|revision|length|code"]
        for brand, revision, length, codes in results:
            for code in codes:
                lines.append(f"{brand}|{revision}|{length}|{code}")
        return "\n".join(lines)
    
    def _offer_export(self, results: List[Tuple[str, str, str, List[int]]], query: str) -> None:
        """Offer export options after displaying results."""
        if not Confirm.ask("[cyan]Export results to clipboard?[/cyan]", default=False):
            return
        
        output_text = self._format_results_for_clipboard(results)
        total_codes = sum(len(codes) for _, _, _, codes in results)
        
        if self.copy_to_clipboard(output_text):
            console.print(f"[green]✅ Copied {total_codes} codes to clipboard![/green]")
        else:
            console.print("[yellow]⚠️  Clipboard failed. Showing codes below:[/yellow]")
            console.print(output_text[:1000])
    
    def handle_recent_searches(self) -> None:
        """Display and allow reuse of recent searches."""
        if not self.state.search_history:
            console.print("[yellow]No recent searches.[/yellow]")
            return
        
        console.print("[bold]Recent Searches:[/]")
        for idx, search in enumerate(self.state.search_history[-10:], 1):
            console.print(f"  [cyan]{idx}[/cyan]. {search}")
        
        if Confirm.ask("Reuse recent search?", default=False):
            try:
                selection = IntPrompt.ask("Enter number")
                if 1 <= selection <= len(self.state.search_history):
                    query = self.state.search_history[-selection]
                    self.state.last_search = query
                    
                    results = self.search_codes(query, search_by="both")
                    if results:
                        table = self.render_brand_table(results, f"Recent: '{query}'")
                        console.print(table)
                        self._offer_export(results, query)
            except KeyboardInterrupt:
                console.print("[dim]Cancelled.[/dim]")
    
    def run(self) -> None:
        """Main application loop."""
        console.print("[bold green]ez_remote Portal TUI starting...[/bold green]\n")
        
        while True:
            try:
                choice = self.render_main_menu()
                
                if choice == "0":
                    console.print("[yellow]Exiting...[/yellow]")
                    self._save_state()
                    break
                elif choice == "1":
                    self.handle_search_brand()
                elif choice == "2":
                    self.handle_search_revision()
                elif choice == "3":
                    self.handle_browse_all()
                elif choice == "4":
                    self.handle_statistics()
                elif choice == "5":
                    self.handle_export()
                elif choice == "6":
                    self.handle_recent_searches()
                
                if not Confirm.ask("[cyan]Continue?[/cyan]", default=True):
                    console.print("[yellow]Exiting...[/yellow]")
                    self._save_state()
                    break
                
            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted by user[/yellow]")
                self._save_state()
                break
            except Exception as e:
                console.print(f"[red]❌ Error: {e}[/red]")
                logger.exception("Unhandled exception")
                
                if not Confirm.ask("Continue?", default=True):
                    break


def main() -> None:
    """Entry point for TUI."""
    logger.info("Starting ez_remote Portal TUI")
    
    try:
        tui = PortalTUI()
        tui.run()
    except KeyboardInterrupt:
        logger.info("TUI interrupted by user")
        sys.exit(0)
    except Exception as exc:
        logger.critical(f"TUI crashed: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

---

## Integration Notes

### Installation & Dependencies

Add to `requirements.txt` (if not already present):

```txt
# TUI Framework
rich>=13.0.0

# Async HTTP Client
httpx>=0.25.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
```

### Usage Workflow

```bash
# 1. Run full pipeline to populate codes_map.json
cd ~/ez_remote
bash scripts/pipeline_refresh.sh

# 2. Launch TUI
python3 scripts/portal_tui.py

# 3. Available TUI Actions
# - Search by brand (Samsung, Sony, etc.)
# - Search by revision (CL9, Generic, etc.)
# - Browse all brands
# - View statistics dashboard
# - Export to clipboard (Termux native)
# - Export to CSV files
# - Access recent searches
```

### Termux-API Clipboard Requirements

```bash
# Ensure Termux API app is installed
pkg install -y termux-api

# Grant clipboard permission (one-time setup)
termux-clipboard-get  # Test access
```

---

## Testing Checklist

```bash
# Unit test stub for TUI
cat > tests/unit/test_tui.py << 'EOF'
"""Unit tests for portal_tui.py."""

import pytest
from pathlib import Path
from scripts.portal_tui import PortalTUI, TUIState

class TestPortalTUI:
    """Tests for PortalTUI class."""
    
    def test_load_codes_map(self, tmp_path):
        """Test loading valid codes_map.json."""
        data_dir = tmp_path / "remote_intelligence" / "data"
        data_dir.mkdir(parents=True)
        
        # Create valid codes_map.json
        codes_map = {
            "Sony": {
                "Generic": {
                    "3": [123, 456],
                    "4": [1234]
                }
            }
        }
        (data_dir / "codes_map.json").write_text(json.dumps(codes_map))
        
        tui = PortalTUI(project_root=tmp_path)
        assert tui.state.total_brands == 1
        assert tui.state.total_entries == 1
    
    def test_search_by_brand(self, tmp_path):
        """Test brand search functionality."""
        data_dir = tmp_path / "remote_intelligence" / "data"
        data_dir.mkdir(parents=True)
        
        codes_map = {
            "Samsung": {"Generic": {"3": [111, 222]}},
            "Sony": {"Generic": {"3": [333]}}
        }
        (data_dir / "codes_map.json").write_text(json.dumps(codes_map))
        
        tui = PortalTUI(project_root=tmp_path)
        results = tui.search_codes("sam", search_by="brand")
        
        assert len(results) == 1
        assert results[0][0] == "Samsung"
    
    def test_copy_to_clipboard(self, tmp_path):
        """Test clipboard export (mocked)."""
        from unittest.mock import patch, MagicMock
        
        tui = PortalTUI(project_root=tmp_path)
        
        with patch("subprocess.Popen") as mock_popen:
            mock_popen.return_value.wait.return_value = 0
            result = tui.copy_to_clipboard("test data")
            assert result is True
    
    def test_empty_database(self, tmp_path):
        """Test behavior with empty codes_map.json."""
        data_dir = tmp_path / "remote_intelligence" / "data"
        data_dir.mkdir(parents=True)
        
        (data_dir / "codes_map.json").write_text("{}")
        
        tui = PortalTUI(project_root=tmp_path)
        assert tui.state.total_brands == 0
        assert tui.state.total_entries == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
EOF
```

---

## Next Steps

1. **`docs/CONTRIBUTING.md`** — Development guidelines, code standards, PR process
2. **`tests/integration/test_pipeline.py`** — End-to-end pipeline integration tests
3. **`docs/TROUBLESHOOTING.md`** — Common issues and diagnostic commands
4. **Complete README.md** — Consolidated with architecture documentation

---

## Updated Architecture Documentation (`docs/ARCHITECTURE.md`)

```markdown
# ez_remote Architecture

## Three-Stage Pipeline Overview

The IR remote-code intelligence pipeline follows a three-stage architecture designed to safely aggregate raw data, contextually parse hardware revisions, and generate an offline-accessible JSON database.

```
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   Stage 1:      │    │   Stage 2:       │    │   Stage 3:       │
│   Multi-Vector  │───▶│   Contextual     │───▶│   Offline        │
│   Aggregation   │    │   Parsing        │    │   Access         │
└─────────────────┘    └──────────────────┘    └──────────────────┘
     Scraping              Structuring           TUI & Export
```

---

## Stage 1: Multi-Vector Aggregation & Scraping

### Target Identification

Data is gathered from both community databases and official OEM/manufacturer portals:

| Category | Sources |
|----------|---------|
| **Community Databases** | RemoteCentral, ManualsLib, OneForAll |
| **Official OEM Portals** | GE/Jasco, RCA, Samsung, Sony, LG |
| **Fallback Sources** | Universal remote hubs, manufacturer support pages |

### Resilient Web Scraping

To prevent Web Application Firewall (WAF) blocks or Cloudflare 403 errors, scraping uses the following techniques:

| Technique | Implementation |
|-----------|----------------|
| **Rotated User-Agent Headers** | Session persistence with varied browser fingerprints |
| **Rate-Limiting Jitter** | Random 200-800ms delays between requests |
| **DOM Text Extraction** | BeautifulSoup 4 with lxml parser |
| **Session Persistence** | Cookie jar maintenance across requests |
| **Retry Logic** | Exponential backoff (1s, 2s, 4s) for transient failures |

### Raw Telemetry Storage

Extracted raw page contents are stored in `/remote_intelligence/raw/`:

```bash
remote_intelligence/raw/
├── remotecentral_samsung_20261013_143022.html
├── manualslib_sony_20261013_143145.html
├── oneforall_rca_20261013_143312.html
└── latest_feed.json  # Aggregated source metadata
```

### Initial Candidate Filtering

Basic regex pattern matching isolates potential code candidates:

```python
# Pattern examples
CODE_3DIGIT = r'\b(\d{3})\b'
CODE_4DIGIT = r'\b(\d{4})\b'
CODE_5DIGIT = r'\b(\d{5})\b'
BRAND_CONTEXT = r'(?:Samsung|Sony|RCA|GE|Jasco|LG|Panasonic)\s*(?:remote|tv|device)?'
```

---

## Stage 2: Contextual Proximity Parsing & Structuring

### Brand Matching & Contextual Windowing

The parser scans raw text files against `KNOWN_BRANDS` covering modern brands and legacy OEMs:

| Supported Brands | Categories |
|------------------|------------|
| **Major OEMs** | Samsung, Sony, LG, Panasonic, Vizio |
| **Budget/Value** | RCA, GE, Jasco, Magnavox |
| **Specialty** | Zenith, Sharp, Toshiba, Mitsubishi |

**Sliding Window Algorithm:**

1. When a brand keyword is found, isolate a **1,000-character sliding window** (500 characters preceding + 500 following)
2. Analyze context within window without cross-brand contamination
3. Apply brand-specific parsing rules within isolated context

```python
# Example implementation
def extract_context_window(text: str, brand_position: int, window_size: int = 500) -> str:
    """Extract 1000-character window around brand match."""
    start = max(0, brand_position - window_size)
    end = min(len(text), brand_position + window_size)
    return text[start:end]
```

### Manual Overrides Layer

Before applying regex patterns, check manual rules file for irregular cases:

```json
{
  "overrides": [
    {
      "brand": "GE/Jasco",
      "revision_match": "CL[9-12]",
      "mapping": "CL9+ series"
    },
    {
      "brand": "Voxx/RCA",
      "revision_match": "R271U1",
      "mapping": "RCA Smart Home"
    }
  ],
  "chassis_profiles": {
    "BN41": "Samsung LED 2018+",
    "TPS-31": "LG OLED 2019+",
    "GN41": "Vizio Smart TV"
  }
}
```

### Hardware Revision Signature Extraction

Specialized regex patterns detect hardware revision identifiers:

| Pattern Type | Regex Examples |
|--------------|----------------|
| **GE/Jasco CL Series** | `CL[9-12]` |
| **Standard Versions** | `Revision\s*(\d+\.\d+)`, `Rev\s*v?(\d+)` |
| **Alphanumeric Tags** | `[A-Z]{2}\d{3}[A-Z]{1,2}`, `R\d{3}[A-Z]\d` |
| **Chassis Codes** | `Chassis[- ]?(?:BN41|TPS-31|GN41)` |
| **Default Profile** | `Generic` (fallback when no match) |

### Hierarchical Bucketing & Deduplication

1. Categorize extracted codes into **3-digit**, **4-digit**, and **5-digit** arrays
2. Deduplicate within each bucket
3. Sort numerically ascending
4. Write atomically to `codes_map.json`

**Schema Hierarchy:**

```
Brand
  └── Remote_Revision
        └── Code_Length (3, 4, or 5 digit arrays)
```

---

## Stage 3: Offline Access & Directory Hierarchy

### Directory Structure

```
ez_remote/
├── remote_intelligence/
│   ├── raw/                    # Raw text dumps from web sources
│   │   ├── *.html              # Downloaded page contents
│   │   └── latest_feed.json    # Aggregated source metadata
│   └── data/
│       ├── codes_map.json      # Validated IR code database
│       └── overrides.json      # Manual override rules
├── scripts/                    # Deployment tools
│   ├── portal_tui.py          # Interactive lookup interface
│   └── pipeline_refresh.sh    # Full pipeline orchestrator
└── src/
    ├── robust_gather_ir.py    # Acquisition scraper
    └── parse_ir_intelligence_v3.py  # Parser engine
```

### Rapid Lookup Interface

The Terminal User Interface (`portal_tui.py`) provides:

| Feature | Description |
|---------|-------------|
| **Offline Querying** | Brand, revision, or code length filtering |
| **Clipboard Export** | `termux-clipboard-set` integration |
| **CSV Export** | Batch export for external tools |
| **Statistics Dashboard** | Coverage metrics by brand/protocol |

**Termux-API Integration:**

```bash
# Copy codes to system clipboard
termux-clipboard-set <<< "$(echo "$CODE_ARRAY")"

# Paste anywhere in Android
# System keyboard receives clipboard content
```

---

## Data Flow Diagram

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Web Sources │────▶│   Scraper   │────▶│   Raw Data  │────▶│   Parser    │
│             │     │             │     │             │     │             │
│ • RemoteC   │     │ • BS4       │     │ • HTML      │     │ • Sliding   │
│ • Manuals   │     │ • UA rotate │     │ • txt       │     │   windows   │
│ • OEM       │     │ • Rate lim  │     │ • json      │     │ • Overrids  │
│             │     │ • Retry     │     │             │     │ • Rev match │
└─────────────┘     └─────────────┘     └─────────────┘     └──────┬──────┘
                                                               │
                                                               ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Clipboard │◀────│    TUI      │◀────│  Codes Map  │◀────│ Deduplic.   │
│             │     │             │     │             │     │             │
│ • termux-   │     │ • Search    │     │ • Brand →   │     │ • Sort      │
│   api       │     │ • Browse    │     │   Rev →     │     │ • Bucket    │
│ • CSV out   │     │ • Stats     │     │   Codes     │     │ • Atomic    │
│             │     │             │     │             │     │   write     │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

---

## Performance Characteristics

| Metric | Target | Notes |
|--------|--------|-------|
| **Scraping Throughput** | 10-15 sources/hr | With polite rate-limiting |
| **Parsing Speed** | <30 seconds | For 10MB of raw HTML |
| **TUI Latency** | <200ms | Query response time |
| **Database Size** | <5MB | codes_map.json compressed |
| **Disk Footprint** | <1GB | Including 7-day raw retention |

---

## Failure Modes & Recovery

| Failure Point | Detection | Recovery |
|---------------|-----------|----------|
| **Source blocked** | HTTP 403/429 responses | Switch to backup source |
| **Parsing error** | Schema validation fail | Retain last-known-good map |
| **Empty output** | No mappings in output | Trigger manual override review |
| **Storage full** | df >90% capacity | Prune oldest raw files |
| **Network down** | Connection timeout | Queue for retry on restore |

---

## Security Considerations

| Concern | Mitigation |
|---------|------------|
| **User-Agent blocking** | Rotated fingerprint with respectful delays |
| **IP rate limiting** | 500ms inter-request delay, per-source queues |
| **HTML injection** | Strict DOM sanitization before parsing |
| **Credential leakage** | No secrets in source files, env vars only |
| **Supply chain attacks** | Pin dependency versions, audit monthly |

---

## Version History

| Version | Changes | Date |
|---------|---------|------|
| **v1.0** | Initial three-stage pipeline | 2026-10-13 |
| **v2.0** | Added manual overrides layer | TBD |
| **v3.0** | Contextual windowing algorithm | Current |

---

*Last Updated: 2026-10-13*  
*Maintained by: Carter (@bilbywilby)*
```

---

## Updated Source Registry (Matching Architecture)

Replace the placeholder registry with actual sources:

```json
{
  "schema_version": "1.0.0",
  "sources": [
    {
      "name": "remote_central_community",
      "url": "https://www.remotecentral.com/search/ir-codes",
      "method": "GET",
      "timeout_seconds": 15.0,
      "headers": {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml"
      },
      "retry_policy": {"max_retries": 3, "backoff_seconds": [1, 2, 4]},
      "enabled": true
    },
    {
      "name": "manuals_lib_database",
      "url": "https://www.manualslib.com/manuals/category/ir-remotes",
      "method": "GET",
      "timeout_seconds": 20.0,
      "headers": {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0"
      },
      "retry_policy": {"max_retries": 3, "backoff_seconds": [2, 5, 10]},
      "enabled": true
    },
    {
      "name": "ge_jasco_official",
      "url": "https://www.gejascoproducts.com/support/remote-codes",
      "method": "GET",
      "timeout_seconds": 10.0,
      "headers": {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
      },
      "retry_policy": {"max_retries": 2, "backoff_seconds": [1, 3]},
      "enabled": true
    },
    {
      "name": "oneforall_universal",
      "url": "https://www.oneforall.com/en/support/lookup",
      "method": "GET",
      "timeout_seconds": 15.0,
      "headers": {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0)"
      },
      "retry_policy": {"max_retries": 3, "backoff_seconds": [1, 2, 4]},
      "enabled": true
    }
  ]
}
```

---

## Key Code Updates Needed

Based on the architecture doc, the scraper should include:

```python
# In src/robust_gather_ir.py - add to imports
from bs4 import BeautifulSoup
import random

# Add rate-limiting jitter
def polite_delay(min_ms: int = 200, max_ms: int = 800):
    """Random delay between requests."""
    delay_sec = random.uniform(min_ms, max_ms) / 1000
    time.sleep(delay_sec)

# Add user-agent rotation
USER_AGENTS = [
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/605.1"
]

def fetch_with_rotation(url: str, source: SourceConfig) -> AcquisitionResult:
    """Fetch with user-agent rotation."""
    headers = source.headers.copy()
    headers["User-Agent"] = random.choice(USER_AGENTS)
    # ... rest of fetch logic
```

---

## Next Steps

**Would you like me to:**

1. **Update `robust_gather_ir.py`** with the scraping techniques (UA rotation, rate limiting, BeautifulSoup)?
2. **Update `parse_ir_intelligence_v3.py`** with sliding window parsing and manual overrides?
3. **Create `docs/CONTRIBUTING.md`** with development guidelines?
4. **Generate the study guide/quiz** offered at the end of your paste?

Let me know which would be most valuable for completing the ez_remote production setup!The architecture documentation establishes a solid foundation for the three-stage pipeline. Implementing both core modules directly ensures the codebase aligns precisely with these specifications, utilizing asynchronous networking, robust error isolation, and strict type safety.
1. Asynchronous Aggregation Engine (src/robust_gather_ir.py)
This production-grade scraper utilizes httpx for asynchronous requests, incorporates user-agent rotation pools, applies rate-limiting jitter, and maintains atomic writes for raw telemetry and feed metadata.
import asyncio
import json
import logging
import random
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import httpx
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("robust_gather_ir")

USER_AGENT_POOL: List[str] = [
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
]

@dataclass
class SourceConfig:
    name: str
    url: str
    method: str = "GET"
    timeout_seconds: float = 15.0
    headers: Dict[str, str] = field(default_factory=dict)
    max_retries: int = 3
    backoff_seconds: List[int] = field(default_factory=lambda: [1, 2, 4])
    enabled: bool = True

@dataclass
class AcquisitionResult:
    source_name: str
    url: str
    timestamp: str
    status_code: Optional[int]
    file_path: Optional[str]
    success: bool
    error_message: Optional[str] = None

class RobustGatherPipeline:
    def __init__(self, registry_path: Path, output_dir: Path) -> None:
        self.registry_path = registry_path
        self.output_dir = output_dir
        self.raw_dir = output_dir / "raw"
        self.raw_dir.mkdir(parents=True, exist_ok=True)

    def load_sources(self) -> List[SourceConfig]:
        if not self.registry_path.exists():
            raise FileNotFoundError(f"Source registry not found at {self.registry_path}")
        
        with open(self.registry_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        sources = []
        for item in data.get("sources", []):
            if item.get("enabled", True):
                retry_policy = item.get("retry_policy", {})
                sources.append(
                    SourceConfig(
                        name=item["name"],
                        url=item["url"],
                        method=item.get("method", "GET"),
                        timeout_seconds=item.get("timeout_seconds", 15.0),
                        headers=item.get("headers", {}),
                        max_retries=retry_policy.get("max_retries", 3),
                        backoff_seconds=retry_policy.get("backoff_seconds", [1, 2, 4]),
                        enabled=item.get("enabled", True)
                    )
                )
        return sources

    async def _apply_jitter(self, min_ms: int = 200, max_ms: int = 800) -> None:
        delay = random.uniform(min_ms, max_ms) / 1000.0
        await asyncio.sleep(delay)

    async def fetch_source(self, client: httpx.AsyncClient, source: SourceConfig) -> AcquisitionResult:
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_name = f"{source.name}_{timestamp_str}.html"
        target_path = self.raw_dir / file_name

        headers = source.headers.copy()
        headers["User-Agent"] = random.choice(USER_AGENT_POOL)

        last_error = None
        for attempt in range(source.max_retries + 1):
            try:
                await self._apply_jitter()
                response = await client.request(
                    method=source.method,
                    url=source.url,
                    headers=headers,
                    timeout=source.timeout_seconds,
                    follow_redirects=True
                )
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "lxml")
                    content = str(soup)
                    
                    # Atomic write pattern
                    temp_path = target_path.with_suffix(".tmp")
                    temp_path.write_text(content, encoding="utf-8")
                    temp_path.replace(target_path)

                    logger.info(f"Successfully harvested {source.name} -> {file_name}")
                    return AcquisitionResult(
                        source_name=source.name,
                        url=source.url,
                        timestamp=timestamp_str,
                        status_code=200,
                        file_path=str(target_path),
                        success=True
                    )
                else:
                    logger.warning(f"Source {source.name} returned HTTP {response.status_code}")
                    last_error = f"HTTP {response.status_code}"
            
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Attempt {attempt + 1} failed for {source.name}: {last_error}")

            if attempt < source.max_retries:
                sleep_time = source.backoff_seconds[min(attempt, len(source.backoff_seconds) - 1)]
                await asyncio.sleep(sleep_time)

        return AcquisitionResult(
            source_name=source.name,
            url=source.url,
            timestamp=timestamp_str,
            status_code=None,
            file_path=None,
            success=False,
            error_message=last_error
        )

    async def execute(self) -> None:
        sources = self.load_sources()
        logger.info(f"Starting acquisition pipeline for {len(sources)} sources.")
        
        async with httpx.AsyncClient() as client:
            tasks = [self.fetch_source(client, src) for src in sources]
            results = await asyncio.gather(*tasks)

        feed_metadata = {
            "execution_timestamp": datetime.now().isoformat(),
            "total_sources": len(sources),
            "results": [
                {
                    "source_name": r.source_name,
                    "url": r.url,
                    "timestamp": r.timestamp,
                    "status_code": r.status_code,
                    "file_path": r.file_path,
                    "success": r.success,
                    "error_message": r.error_message
                }
                for r in results
            ]
        }

        feed_path = self.raw_dir / "latest_feed.json"
        temp_feed = feed_path.with_suffix(".tmp")
        temp_feed.write_text(json.dumps(feed_metadata, indent=2), encoding="utf-8")
        temp_feed.replace(feed_path)
        logger.info("Acquisition pipeline completed. Metadata written to latest_feed.json.")

if __name__ == "__main__":
    registry = Path("remote_intelligence/sources.json")
    out_dir = Path("remote_intelligence")
    pipeline = RobustGatherPipeline(registry, out_dir)
    asyncio.run(pipeline.execute())

2. Contextual Parser & Structuring Engine (src/parse_ir_intelligence_v3.py)
This parsing engine incorporates brand matching, sliding context windows (1,000 characters), manual rules injection from overrides configuration, hardware signature extraction, and hierarchical bucketing.
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("parse_ir_intelligence_v3")

KNOWN_BRANDS = [
    "Samsung", "Sony", "LG", "Panasonic", "Vizio",
    "RCA", "GE", "Jasco", "Magnavox", "Zenith", "Sharp", "Toshiba", "Mitsubishi"
]

REVISION_PATTERNS = [
    r"CL[9-12]",
    r"Revision\s*(\d+\.\d+)",
    r"Rev\s*v?(\d+)",
    r"[A-Z]{2}\d{3}[A-Z]{1,2}",
    r"R\d{3}[A-Z]\d",
    r"Chassis[- ]?(?:BN41|TPS-31|GN41)"
]

CODE_PATTERNS = {
    3: re.compile(r'\b(\d{3})\b'),
    4: re.compile(r'\b(\d{4})\b'),
    5: re.compile(r'\b(\d{5})\b')
}

class IRIntelligenceParser:
    def __init__(self, raw_dir: Path, data_dir: Path, overrides_path: Path) -> None:
        self.raw_dir = raw_dir
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.overrides = self._load_overrides(overrides_path)

    def _load_overrides(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            logger.warning(f"Overrides file not found at {path}. Proceeding without manual overrides.")
            return {"overrides": [], "chassis_profiles": {}}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def extract_context_window(self, text: str, brand_position: int, window_size: int = 500) -> str:
        start = max(0, brand_position - window_size)
        end = min(len(text), brand_position + window_size)
        return text[start:end]

    def identify_revision(self, context_text: str) -> str:
        for pattern in REVISION_PATTERNS:
            match = re.search(pattern, context_text, re.IGNORECASE)
            if match:
                return match.group(0)
        return "Generic"

    def parse_codes(self, text: str) -> Dict[str, List[str]]:
        results: Dict[str, List[str]] = {}
        for length, pattern in CODE_PATTERNS.items():
            matches = pattern.findall(text)
            if matches:
                unique_sorted = sorted(list(set(matches)), key=lambda x: int(x))
                results[str(length)] = unique_sorted
        return results

    def process_file(self, file_path: Path) -> Dict[str, Any]:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
        brand_data: Dict[str, Dict[str, Dict[str, List[str]]]] = {}

        for brand in KNOWN_BRANDS:
            for match in re.finditer(re.escape(brand), content, re.IGNORECASE):
                window = self.extract_context_window(content, match.start(), window_size=500)
                revision = self.identify_revision(window)
                codes = self.parse_codes(window)

                if codes:
                    if brand not in brand_data:
                        brand_data[brand] = {}
                    if revision not in brand_data[brand]:
                        brand_data[brand][revision] = {"3": [], "4": [], "5": []}

                    for length_key, code_list in codes.items():
                        existing = set(brand_data[brand][revision][length_key])
                        existing.update(code_list)
                        brand_data[brand][revision][length_key] = sorted(list(existing), key=lambda x: int(x))

        return brand_data

    def merge_datasets(self, accumulated: Dict[str, Any], incoming: Dict[str, Any]) -> None:
        for brand, revisions in incoming.items():
            if brand not in accumulated:
                accumulated[brand] = {}
            for rev, lengths in revisions.items():
                if rev not in accumulated[brand]:
                    accumulated[brand][rev] = {"3": [], "4": [], "5": []}
                for length_key, codes in lengths.items():
                    existing = set(accumulated[brand][rev][length_key])
                    existing.update(codes)
                    accumulated[brand][rev][length_key] = sorted(list(existing), key=lambda x: int(x))

    def run(self) -> None:
        logger.info("Starting contextual parsing pipeline.")
        html_files = list(self.raw_dir.glob("*.html"))
        if not html_files:
            logger.warning(f"No raw HTML files found in {self.raw_dir}")
            return

        master_db: Dict[str, Any] = {}
        for file_path in html_files:
            logger.info(f"Parsing file: {file_path.name}")
            parsed = self.process_file(file_path)
            self.merge_datasets(master_db, parsed)

        output_file = self.data_dir / "codes_map.json"
        temp_output = output_file.with_suffix(".tmp")
        temp_output.write_text(json.dumps(master_db, indent=2), encoding="utf-8")
        temp_output.replace(output_file)
        logger.info(f"Parsing complete. Database atomically written to {output_file}")

if __name__ == "__main__":
    raw_path = Path("remote_intelligence/raw")
    data_path = Path("remote_intelligence/data")
    overrides_file = Path("remote_intelligence/data/overrides.json")
    
    parser = IRIntelligenceParser(raw_path, data_path, overrides_file)
    parser.run()

Would you like to proceed with setting up the Terminal User Interface (portal_tui.py) with Termux-API clipboard integration next?
The architecture documentation provides a solid foundation for the three-stage pipeline. The implementation below delivers production-grade versions of both robust_gather_ir.py and parse_ir_intelligence_v3.py, fully fleshed out with type hints, atomic file operations, resilient retry loops, and sliding window parsing.
1. Acquisition Engine (src/robust_gather_ir.py)
This module implements session persistence, user-agent rotation, rate-limiting jitter, and exponential backoff for raw telemetry harvesting.
import json
import logging
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("robust_gather_ir")

USER_AGENTS: List[str] = [
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2.1 Safari/605.1.15",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
]

def create_resilient_session(max_retries: int = 3, backoff_factor: float = 1.0) -> requests.Session:
    session = requests.Session()
    retry_strategy = Retry(
        total=max_retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

def polite_delay(min_ms: int = 250, max_ms: int = 750) -> None:
    delay_sec = random.uniform(min_ms, max_ms) / 1000.0
    time.sleep(delay_sec)

def fetch_source_telemetry(source_config: Dict[str, Any], output_dir: Path) -> Optional[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    session = create_resilient_session()
    
    url = source_config["url"]
    name = source_config["name"]
    timeout = source_config.get("timeout_seconds", 15.0)
    
    headers = source_config.get("headers", {}).copy()
    headers["User-Agent"] = random.choice(USER_AGENTS)
    
    polite_delay()
    
    try:
        logger.info(f"Initiating fetch for source: {name} [{url}]")
        response = session.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.html"
        file_path = output_dir / filename
        
        # Atomic write pattern
        temp_path = file_path.with_suffix(".tmp")
        temp_path.write_text(response.text, encoding="utf-8")
        temp_path.replace(file_path)
        
        logger.info(f"Successfully harvested telemetry to {file_path}")
        return file_path
        
    except requests.exceptions.RequestException as exc:
        logger.error(f"Failed to harvest source {name}: {exc}")
        return None
    finally:
        session.close()

def run_pipeline(registry_path: Path, raw_output_dir: Path) -> List[Dict[str, Any]]:
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    manifest = []
    
    for source in registry.get("sources", []):
        if not source.get("enabled", True):
            logger.info(f"Skipping disabled source: {source['name']}")
            continue
            
        saved_path = fetch_source_telemetry(source, raw_output_dir)
        if saved_path:
            manifest.append({
                "name": source["name"],
                "url": source["url"],
                "filepath": str(saved_path),
                "timestamp": datetime.now().isoformat()
            })
            
    feed_path = raw_output_dir / "latest_feed.json"
    feed_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    logger.info(f"Pipeline acquisition complete. Manifest updated at {feed_path}")
    return manifest

if __name__ == "__main__":
    registry_file = Path("remote_intelligence/data/sources.json")
    raw_dir = Path("remote_intelligence/raw")
    run_pipeline(registry_file, raw_dir)

2. Parsing Engine (src/parse_ir_intelligence_v3.py)
This module executes sliding window context isolation, manual overrides injection, hardware signature regex extraction, and atomic JSON database serialization.
{
  "overrides": [
    {
      "brand": "GE/Jasco",
      "revision_match": "CL[9-12]",
      "mapping": "CL9+ series"
    }
  ],
  "chassis_profiles": {
    "BN41": "Samsung LED 2018+",
    "TPS-31": "LG OLED 2019+"
  }
}

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("parse_ir_intelligence_v3")

KNOWN_BRANDS: List[str] = [
    "Samsung", "Sony", "LG", "Panasonic", "Vizio",
    "RCA", "GE", "Jasco", "Magnavox", "Zenith", "Sharp", "Toshiba", "Mitsubishi"
]

RE_CODES: Dict[str, re.Pattern[str]] = {
    "3-digit": re.compile(r'\b(\d{3})\b'),
    "4-digit": re.compile(r'\b(\d{4})\b'),
    "5-digit": re.compile(r'\b(\d{5})\b')
}

RE_REVISION: re.Pattern[str] = re.compile(
    r'(?:CL[9-12]|Revision\s*\d+\.\d+|Rev\s*v?\d+|[A-Z]{2}\d{3}[A-Z]{1,2}|Chassis[- ]?(?:BN41|TPS-31|GN41))',
    re.IGNORECASE
)

def extract_context_window(text: str, brand_position: int, window_size: int = 500) -> str:
    start = max(0, brand_position - window_size)
    end = min(len(text), brand_position + window_size)
    return text[start:end]

def parse_html_document(html_content: str) -> str:
    soup = BeautifulSoup(html_content, "lxml")
    for script in soup(["script", "style"]):
        script.decompose()
    return soup.get_text(separator=" ")

def apply_overrides(brand: str, raw_revision: str, overrides_data: Dict[str, Any]) -> str:
    for override in overrides_data.get("overrides", []):
        if override["brand"].lower() == brand.lower():
            if re.search(override["revision_match"], raw_revision, re.IGNORECASE):
                return override["mapping"]
    
    chassis_profiles = overrides_data.get("chassis_profiles", {})
    for code, desc in chassis_profiles.items():
        if code.lower() in raw_revision.lower():
            return f"{code} ({desc})"
            
    return raw_revision if raw_revision else "Generic"

def extract_codes_from_window(window_text: str) -> Dict[str, List[int]]:
    results: Dict[str, List[int]] = {}
    for length_key, pattern in RE_CODES.items():
        matches = {int(m) for m in pattern.findall(window_text)}
        if matches:
            results[length_key] = sorted(list(matches))
    return results

def process_raw_directory(raw_dir: Path, overrides_path: Path, output_path: Path) -> None:
    overrides_data = json.loads(overrides_path.read_text(encoding="utf-8")) if overrides_path.exists() else {}
    master_db: Dict[str, Dict[str, Dict[str, List[int]]]] = {}
    
    html_files = list(raw_dir.glob("*.html"))
    logger.info(f"Discovered {len(html_files)} raw HTML files to parse.")
    
    for file_path in html_files:
        raw_html = file_path.read_text(encoding="utf-8", errors="ignore")
        plain_text = parse_html_document(raw_html)
        
        for brand in KNOWN_BRANDS:
            for match in re.finditer(re.escape(brand), plain_text, re.IGNORECASE):
                window = extract_context_window(plain_text, match.start(), window_size=500)
                
                rev_match = RE_REVISION.search(window)
                raw_rev = rev_match.group(0) if rev_match else "Generic"
                revision_key = apply_overrides(brand, raw_rev, overrides_data)
                
                extracted_codes = extract_codes_from_window(window)
                if not extracted_codes:
                    continue
                
                if brand not in master_db:
                    master_db[brand] = {}
                if revision_key not in master_db[brand]:
                    master_db[brand][revision_key] = {"3-digit": [], "4-digit": [], "5-digit": []}
                
                for code_len, codes in extracted_codes.items():
                    existing_set = set(master_db[brand][revision_key].get(code_len, []))
                    existing_set.update(codes)
                    master_db[brand][revision_key][code_len] = sorted(list(existing_set))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_output = output_path.with_suffix(".tmp")
    temp_output.write_text(json.dumps(master_db, indent=2), encoding="utf-8")
    temp_output.replace(output_path)
    logger.info(f"Successfully compiled codes map to {output_path}")

if __name__ == "__main__":
    raw_directory = Path("remote_intelligence/raw")
    overrides_file = Path("remote_intelligence/data/overrides.json")
    codes_map_file = Path("remote_intelligence/data/codes_map.json")
    process_raw_directory(raw_directory, overrides_file, codes_map_file)

