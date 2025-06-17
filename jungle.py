#!/usr/bin/env python3

import subprocess
import sys
import os
import argparse
import shutil
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.text import Text

class JungleWorktreeManager:
    def __init__(self):
        self.console = Console()
        self.status_symbols = {
            'Clean': ('✓', 'green'),
            'Modified': ('!', 'red'),
            'Staged': ('S', 'red'),
            'Untracked': ('?', 'yellow'),
            'Mixed': ('M', 'red'),
            'ERROR': ('✗', 'red')
        }
    
    def run(self, args):
        try:
            if args.command == 'help':
                self._show_help()
                return
            elif args.command == 'new':
                self._create_worktree(args.branch, args.path)
                return
            elif args.command in ['delete', 'remove']:
                self._delete_worktree(args.branch, args.force)
                return
            elif args.command == 'branches':
                self._list_recent_branches(args.limit)
                return
            elif args.command == 'switch':
                self._switch_worktree(args.branch)
                return
            elif args.command == 'status':
                self._show_status()
                return
            elif args.command == 'list' or args.command is None:
                git_root = self._find_git_root()
                worktrees = self._discover_worktrees(git_root)
                worktree_data = self._collect_worktree_data(worktrees)
                self._display_results(worktree_data, args.table)
        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)
    
    def _find_git_root(self):
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--show-toplevel'],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            raise Exception("Not in a Git repository.")
    
    def _discover_worktrees(self, git_root):
        worktrees = [git_root]  # Include main worktree
        
        try:
            result = subprocess.run(
                ['git', '-C', git_root, 'worktree', 'list', '--porcelain'],
                capture_output=True,
                text=True,
                check=True
            )
            
            for line in result.stdout.strip().split('\n'):
                if line.startswith('worktree '):
                    worktree_path = line.split('worktree ', 1)[1]
                    if worktree_path != git_root:
                        worktrees.append(worktree_path)
        except subprocess.CalledProcessError:
            pass
        
        return worktrees
    
    def _get_current_branch(self, worktree_path):
        try:
            result = subprocess.run(
                ['git', '-C', worktree_path, 'branch', '--show-current'],
                capture_output=True,
                text=True,
                check=True
            )
            branch = result.stdout.strip()
            return branch if branch else "DETACHED"
        except subprocess.CalledProcessError:
            return "UNKNOWN"
    
    def _get_worktree_status(self, worktree_path):
        try:
            result = subprocess.run(
                ['git', '-C', worktree_path, 'status', '--porcelain=v2'],
                capture_output=True,
                text=True,
                check=True
            )
            
            if not result.stdout.strip():
                return "Clean", "green"
            
            modified_count = 0
            staged_count = 0
            untracked_count = 0
            
            for line in result.stdout.strip().split('\n'):
                if line.startswith('1 '):  # Modified files
                    modified_count += 1
                elif line.startswith('2 '):  # Staged files
                    staged_count += 1
                elif line.startswith('? '):  # Untracked files
                    untracked_count += 1
            
            status_parts = []
            color = "green"
            
            if staged_count > 0:
                status_parts.append(f"Staged ({staged_count})")
                color = "red"
            
            if modified_count > 0:
                status_parts.append(f"Modified ({modified_count})")
                if color != "red":
                    color = "red"
            
            if untracked_count > 0:
                status_parts.append(f"Untracked ({untracked_count})")
                if color == "green":
                    color = "yellow"
            
            if len(status_parts) > 1:
                return "Mixed", "red"
            elif status_parts:
                if staged_count > 0:
                    return "Staged", "red"
                elif modified_count > 0:
                    return "Modified", "red"
                else:
                    return "Untracked", "yellow"
            else:
                return "Clean", "green"
                
        except subprocess.CalledProcessError:
            return "ERROR", "red"
    
    def _collect_worktree_data(self, worktrees):
        data = []
        git_root = worktrees[0] if worktrees else ""
        
        for worktree_path in worktrees:
            # Compact path display - mobile friendly
            if worktree_path == git_root:
                display_path = "."
                display_name = "main"
            else:
                # Use basename for compact display
                display_name = os.path.basename(worktree_path)
                # Show relative path if possible
                try:
                    rel_path = os.path.relpath(worktree_path, os.getcwd())
                    if not rel_path.startswith('..'):
                        display_path = f"./{rel_path}"
                    else:
                        display_path = worktree_path
                except ValueError:
                    display_path = worktree_path
            
            branch = self._get_current_branch(worktree_path)
            status, color = self._get_worktree_status(worktree_path)
            
            data.append({
                'path': display_path,
                'name': display_name,
                'branch': branch,
                'status': status,
                'status_color': color
            })
        
        return data
    
    def _display_results(self, worktree_data, table_format=False):
        if table_format:
            self._display_table(worktree_data)
        else:
            self._display_compact(worktree_data)
    
    def _display_compact(self, worktree_data):
        for item in worktree_data:
            symbol, symbol_color = self.status_symbols.get(item['status'], ('?', 'white'))
            
            # Compact mobile-friendly format
            self.console.print(
                f"🌿 [{symbol_color}]{symbol}[/{symbol_color}] "
                f"[blue]{item['branch']}[/blue] "
                f"[dim]({item['name']})[/dim]"
            )
    
    def _display_table(self, worktree_data):
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("WORKTREE PATH", style="cyan", no_wrap=True)
        table.add_column("BRANCH", style="blue")
        table.add_column("STATUS", style="white")
        
        for item in worktree_data:
            status_text = Text(item['status'], style=item['status_color'])
            table.add_row(item['path'], item['branch'], status_text)
        
        self.console.print(table)

    def _create_worktree(self, branch_name, path=None):
        try:
            git_root = self._find_git_root()
            
            if not path:
                # Create trees directory if it doesn't exist
                trees_dir = "./trees"
                os.makedirs(trees_dir, exist_ok=True)
                path = f"{trees_dir}/{branch_name.replace('/', '-')}"
            
            # Check if branch exists locally
            branch_exists = self._check_branch_exists(git_root, branch_name)
            
            if branch_exists:
                # Branch exists, create worktree normally
                result = subprocess.run(
                    ['git', '-C', git_root, 'worktree', 'add', path, branch_name],
                    capture_output=True,
                    text=True,
                    check=True
                )
                self.console.print(f"[green]✓[/green] Created worktree for existing branch [blue]{branch_name}[/blue] at [cyan]{path}[/cyan]")
            else:
                # Branch doesn't exist, create it with worktree
                result = subprocess.run(
                    ['git', '-C', git_root, 'worktree', 'add', '-b', branch_name, path],
                    capture_output=True,
                    text=True,
                    check=True
                )
                self.console.print(f"[green]✓[/green] Created new branch [blue]{branch_name}[/blue] with worktree at [cyan]{path}[/cyan]")
            
            # Copy .env file if it exists
            self._copy_env_file(git_root, path)
            
            # Show updated list
            worktrees = self._discover_worktrees(git_root)
            worktree_data = self._collect_worktree_data(worktrees)
            self.console.print("\n[bold]Updated worktrees:[/bold]")
            self._display_compact(worktree_data)
            
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else str(e)
            self.console.print(f"[red]Error creating worktree: {error_msg}[/red]")
            sys.exit(1)
    
    def _check_branch_exists(self, git_root, branch_name):
        """Check if a branch exists locally or remotely"""
        try:
            # Check local branches
            result = subprocess.run(
                ['git', '-C', git_root, 'branch', '--list', branch_name],
                capture_output=True,
                text=True,
                check=True
            )
            if result.stdout.strip():
                return True
            
            # Check remote branches
            result = subprocess.run(
                ['git', '-C', git_root, 'branch', '-r', '--list', f"origin/{branch_name}"],
                capture_output=True,
                text=True,
                check=True
            )
            if result.stdout.strip():
                return True
            
            return False
            
        except subprocess.CalledProcessError:
            return False
    
    def _copy_env_file(self, git_root, worktree_path):
        """Copy .env file from git root to new worktree if it exists"""
        try:
            env_source = os.path.join(git_root, '.env')
            env_dest = os.path.join(worktree_path, '.env')
            
            if os.path.exists(env_source):
                shutil.copy2(env_source, env_dest)
                self.console.print(f"[dim]📄 Copied .env to worktree[/dim]")
            
        except Exception as e:
            # Don't fail worktree creation if .env copy fails
            self.console.print(f"[yellow]⚠️  Could not copy .env file: {e}[/yellow]")
    
    def _delete_worktree(self, worktree_name, force=False):
        try:
            git_root = self._find_git_root()
            worktrees = self._discover_worktrees(git_root)
            
            # Find the worktree to delete
            target_worktree = None
            for worktree_path in worktrees:
                if worktree_path == git_root:
                    continue  # Can't delete main worktree
                
                # Match by name or path
                worktree_basename = os.path.basename(worktree_path)
                if worktree_name in [worktree_basename, worktree_path]:
                    target_worktree = worktree_path
                    break
            
            if not target_worktree:
                self.console.print(f"[red]Error: Worktree '{worktree_name}' not found[/red]")
                return
            
            if target_worktree == git_root:
                self.console.print("[red]Error: Cannot delete main worktree[/red]")
                return
            
            # Get branch info for safety check
            branch = self._get_current_branch(target_worktree)
            
            # Check if branch is merged (unless force is used)
            if not force and branch != "DETACHED" and branch != "UNKNOWN":
                try:
                    # Check if branch is merged into main/master
                    main_branches = ['main', 'master', 'develop']
                    is_merged = False
                    
                    for main_branch in main_branches:
                        try:
                            result = subprocess.run(
                                ['git', '-C', git_root, 'branch', '--merged', main_branch],
                                capture_output=True,
                                text=True,
                                check=True
                            )
                            if f"  {branch}" in result.stdout or f"* {branch}" in result.stdout:
                                is_merged = True
                                break
                        except subprocess.CalledProcessError:
                            continue
                    
                    if not is_merged:
                        self.console.print(f"[yellow]⚠️  Warning: Branch '{branch}' may not be merged![/yellow]")
                        self.console.print(f"[yellow]   Deleting worktree at: {target_worktree}[/yellow]")
                        self.console.print(f"[dim]   Use --force to skip this check[/dim]")
                        
                        # Ask for confirmation
                        response = input("Continue anyway? [y/N]: ").lower().strip()
                        if response not in ['y', 'yes']:
                            self.console.print("[dim]Cancelled[/dim]")
                            return
                
                except Exception:
                    # If we can't check merge status, warn but allow
                    self.console.print(f"[yellow]⚠️  Could not verify if '{branch}' is merged[/yellow]")
            
            # Remove the worktree
            try:
                subprocess.run(
                    ['git', '-C', git_root, 'worktree', 'remove', target_worktree],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                self.console.print(f"[green]✓[/green] Deleted worktree [blue]{branch}[/blue] at [cyan]{target_worktree}[/cyan]")
                
                # Show updated list
                worktrees = self._discover_worktrees(git_root)
                worktree_data = self._collect_worktree_data(worktrees)
                self.console.print("\n[bold]Remaining worktrees:[/bold]")
                self._display_compact(worktree_data)
                
            except subprocess.CalledProcessError as e:
                # Try force removal if regular removal fails
                try:
                    subprocess.run(
                        ['git', '-C', git_root, 'worktree', 'remove', '--force', target_worktree],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    self.console.print(f"[green]✓[/green] Force deleted worktree [blue]{branch}[/blue] at [cyan]{target_worktree}[/cyan]")
                except subprocess.CalledProcessError as e2:
                    error_msg = e2.stderr.strip() if e2.stderr else str(e2)
                    self.console.print(f"[red]Error deleting worktree: {error_msg}[/red]")
                    sys.exit(1)
        
        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)
    
    def _list_recent_branches(self, limit=10):
        try:
            git_root = self._find_git_root()
            
            # Get all branches sorted by last commit date
            result = subprocess.run(
                ['git', '-C', git_root, 'for-each-ref', 
                 '--sort=-committerdate', 
                 '--format=%(refname:short)|%(committerdate:relative)|%(authorname)|%(subject)',
                 'refs/heads/', 'refs/remotes/origin/'],
                capture_output=True,
                text=True,
                check=True
            )
            
            if not result.stdout.strip():
                self.console.print("[yellow]No branches found[/yellow]")
                return
            
            branches = []
            seen_branches = set()
            current_worktrees = self._discover_worktrees(git_root)
            worktree_branches = set()
            
            # Get branches that have worktrees
            for worktree_path in current_worktrees:
                branch = self._get_current_branch(worktree_path)
                if branch not in ["DETACHED", "UNKNOWN"]:
                    worktree_branches.add(branch)
            
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                
                parts = line.split('|', 3)
                if len(parts) != 4:
                    continue
                
                branch_name, last_activity, author, subject = parts
                
                # Skip remote tracking duplicates and HEAD
                if branch_name.startswith('origin/'):
                    local_name = branch_name.replace('origin/', '')
                    if local_name in seen_branches or branch_name.endswith('/HEAD'):
                        continue
                    branch_name = f"origin/{local_name}"
                else:
                    seen_branches.add(branch_name)
                
                # Check if branch has worktree
                has_worktree = branch_name in worktree_branches or branch_name.replace('origin/', '') in worktree_branches
                
                branches.append({
                    'name': branch_name,
                    'last_activity': last_activity,
                    'author': author,
                    'subject': subject[:50] + '...' if len(subject) > 50 else subject,
                    'has_worktree': has_worktree,
                    'is_remote': branch_name.startswith('origin/')
                })
                
                if len(branches) >= limit:
                    break
            
            self._display_branches(branches)
            
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else str(e)
            self.console.print(f"[red]Error listing branches: {error_msg}[/red]")
            sys.exit(1)
    
    def _display_branches(self, branches):
        self.console.print(f"[bold cyan]📅 Recent Branches (by activity)[/bold cyan]\n")
        
        for i, branch in enumerate(branches, 1):
            # Status indicators
            status_indicators = []
            
            if branch['has_worktree']:
                status_indicators.append("[green]🌿[/green]")  # Has worktree
            
            if branch['is_remote']:
                status_indicators.append("[blue]📡[/blue]")  # Remote branch
            else:
                status_indicators.append("[cyan]📍[/cyan]")  # Local branch
            
            status = " ".join(status_indicators)
            
            # Format branch display
            branch_display = f"[bold]{branch['name']}[/bold]" if not branch['is_remote'] else f"[dim]{branch['name']}[/dim]"
            
            self.console.print(
                f"{i:2}. {status} {branch_display}\n"
                f"    [dim]{branch['last_activity']} • {branch['author']}[/dim]\n"
                f"    [dim italic]\"{branch['subject']}\"[/dim italic]\n"
            )
        
        # Legend
        self.console.print("[dim]Legend: 🌿 Has worktree  📍 Local  📡 Remote[/dim]")
    
    def _switch_worktree(self, worktree_name):
        try:
            git_root = self._find_git_root()
            worktrees = self._discover_worktrees(git_root)
            
            # Find the target worktree
            target_worktree = None
            for worktree_path in worktrees:
                # Match by branch name or directory name
                branch = self._get_current_branch(worktree_path)
                worktree_basename = os.path.basename(worktree_path)
                
                if worktree_name in [branch, worktree_basename, worktree_path]:
                    target_worktree = worktree_path
                    break
                
                # Also try matching without the trees/ prefix
                if worktree_path.endswith(f"/{worktree_name}"):
                    target_worktree = worktree_path
                    break
            
            if not target_worktree:
                self.console.print(f"[red]Error: Worktree '{worktree_name}' not found[/red]")
                self.console.print("\n[dim]Available worktrees:[/dim]")
                worktree_data = self._collect_worktree_data(worktrees)
                self._display_compact(worktree_data)
                return
            
            # Get absolute path
            abs_path = os.path.abspath(target_worktree)
            branch = self._get_current_branch(target_worktree)
            
            # Since we can't change the parent shell's directory from Python,
            # we'll provide instructions and copy the path to clipboard if possible
            self.console.print(f"[green]🌿[/green] Switch to worktree: [blue]{branch}[/blue]")
            self.console.print(f"[cyan]📁 Path: {abs_path}[/cyan]\n")
            
            # Try to copy to clipboard
            try:
                if sys.platform == "darwin":  # macOS
                    subprocess.run(['pbcopy'], input=f"cd '{abs_path}'", text=True, check=True)
                    self.console.print("[dim]💾 Command copied to clipboard![/dim]")
                elif sys.platform.startswith("linux"):  # Linux
                    subprocess.run(['xclip', '-selection', 'clipboard'], input=f"cd '{abs_path}'", text=True, check=True)
                    self.console.print("[dim]💾 Command copied to clipboard![/dim]")
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass
            
            # Show the command to run
            self.console.print(f"[bold]Run this command:[/bold]")
            self.console.print(f"[yellow]cd '{abs_path}'[/yellow]")
            
            # Show additional helpful commands
            self.console.print(f"\n[dim]Quick commands for this worktree:[/dim]")
            self.console.print(f"[dim]  git status[/dim]")
            self.console.print(f"[dim]  git log --oneline -5[/dim]")
            
        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)
    
    def _show_status(self):
        """Display comprehensive debug information about the Git repository and environment"""
        try:
            self.console.print("[bold cyan]🔍 Jungle Status - Debug Information[/bold cyan]\n")
            
            # System Information
            self.console.print("[bold yellow]📱 System Information[/bold yellow]")
            self.console.print(f"  Platform: {sys.platform}")
            self.console.print(f"  Python: {sys.version.split()[0]}")
            self.console.print(f"  Current Directory: {os.getcwd()}")
            self.console.print(f"  User: {os.getenv('USER', 'unknown')}")
            self.console.print(f"  Home: {os.getenv('HOME', 'unknown')}")
            self.console.print()
            
            # Git Repository Information
            git_root = self._find_git_root()
            self.console.print("[bold yellow]🌿 Git Repository Information[/bold yellow]")
            self.console.print(f"  Git Root: {git_root}")
            self.console.print(f"  Relative Path: {os.path.relpath(git_root, os.getcwd())}")
            
            # Git configuration
            try:
                result = subprocess.run(['git', '-C', git_root, 'config', '--get', 'user.name'], 
                                      capture_output=True, text=True, check=True)
                git_user = result.stdout.strip()
            except subprocess.CalledProcessError:
                git_user = "Not set"
            
            try:
                result = subprocess.run(['git', '-C', git_root, 'config', '--get', 'user.email'], 
                                      capture_output=True, text=True, check=True)
                git_email = result.stdout.strip()
            except subprocess.CalledProcessError:
                git_email = "Not set"
            
            self.console.print(f"  Git User: {git_user}")
            self.console.print(f"  Git Email: {git_email}")
            
            # Remote information
            try:
                result = subprocess.run(['git', '-C', git_root, 'remote', '-v'], 
                                      capture_output=True, text=True, check=True)
                if result.stdout.strip():
                    self.console.print("  Remotes:")
                    for line in result.stdout.strip().split('\n'):
                        self.console.print(f"    {line}")
                else:
                    self.console.print("  Remotes: None")
            except subprocess.CalledProcessError:
                self.console.print("  Remotes: Error retrieving")
            
            self.console.print()
            
            # Current Branch and HEAD Information
            self.console.print("[bold yellow]🎯 Current Context[/bold yellow]")
            current_branch = self._get_current_branch(os.getcwd())
            self.console.print(f"  Current Branch: {current_branch}")
            
            try:
                result = subprocess.run(['git', '-C', git_root, 'rev-parse', 'HEAD'], 
                                      capture_output=True, text=True, check=True)
                head_sha = result.stdout.strip()
                self.console.print(f"  HEAD SHA: {head_sha[:12]}...")
            except subprocess.CalledProcessError:
                self.console.print("  HEAD SHA: Unable to retrieve")
            
            try:
                result = subprocess.run(['git', '-C', git_root, 'describe', '--tags', '--always'], 
                                      capture_output=True, text=True, check=True)
                description = result.stdout.strip()
                self.console.print(f"  Description: {description}")
            except subprocess.CalledProcessError:
                self.console.print("  Description: No tags found")
            
            self.console.print()
            
            # Worktree Information
            worktrees = self._discover_worktrees(git_root)
            self.console.print(f"[bold yellow]🌳 Worktree Information[/bold yellow]")
            self.console.print(f"  Total Worktrees: {len(worktrees)}")
            self.console.print(f"  Main Worktree: {git_root}")
            
            if len(worktrees) > 1:
                self.console.print("  Additional Worktrees:")
                for worktree in worktrees[1:]:
                    branch = self._get_current_branch(worktree)
                    status, color = self._get_worktree_status(worktree)
                    self.console.print(f"    {worktree}")
                    self.console.print(f"      Branch: {branch}")
                    self.console.print(f"      Status: [{color}]{status}[/{color}]")
            else:
                self.console.print("  Additional Worktrees: None")
            
            self.console.print()
            
            # Trees Directory Information
            self.console.print("[bold yellow]📁 Trees Directory[/bold yellow]")
            trees_dir = os.path.join(os.getcwd(), "trees")
            trees_abs = os.path.abspath(trees_dir)
            self.console.print(f"  Trees Path: {trees_abs}")
            self.console.print(f"  Exists: {os.path.exists(trees_dir)}")
            
            if os.path.exists(trees_dir):
                try:
                    entries = os.listdir(trees_dir)
                    self.console.print(f"  Entries: {len(entries)}")
                    if entries:
                        self.console.print("  Contents:")
                        for entry in sorted(entries)[:10]:  # Show first 10
                            entry_path = os.path.join(trees_dir, entry)
                            if os.path.isdir(entry_path):
                                self.console.print(f"    📁 {entry}")
                            else:
                                self.console.print(f"    📄 {entry}")
                        if len(entries) > 10:
                            self.console.print(f"    ... and {len(entries) - 10} more")
                except PermissionError:
                    self.console.print("  Contents: Permission denied")
            
            self.console.print()
            
            # Branch Statistics
            self.console.print("[bold yellow]📊 Branch Statistics[/bold yellow]")
            try:
                # Count local branches
                result = subprocess.run(['git', '-C', git_root, 'branch', '--list'], 
                                      capture_output=True, text=True, check=True)
                local_branches = len([line for line in result.stdout.strip().split('\n') if line.strip()])
                self.console.print(f"  Local Branches: {local_branches}")
            except subprocess.CalledProcessError:
                self.console.print("  Local Branches: Error counting")
            
            try:
                # Count remote branches
                result = subprocess.run(['git', '-C', git_root, 'branch', '-r', '--list'], 
                                      capture_output=True, text=True, check=True)
                remote_branches = len([line for line in result.stdout.strip().split('\n') if line.strip() and not 'HEAD' in line])
                self.console.print(f"  Remote Branches: {remote_branches}")
            except subprocess.CalledProcessError:
                self.console.print("  Remote Branches: Error counting")
            
            try:
                # Count stashes
                result = subprocess.run(['git', '-C', git_root, 'stash', 'list'], 
                                      capture_output=True, text=True, check=True)
                stashes = len([line for line in result.stdout.strip().split('\n') if line.strip()])
                self.console.print(f"  Stashes: {stashes}")
            except subprocess.CalledProcessError:
                self.console.print("  Stashes: 0")
            
            self.console.print()
            
            # File System Information
            self.console.print("[bold yellow]💾 File System[/bold yellow]")
            
            # Check for common files
            common_files = ['.env', '.gitignore', 'package.json', 'requirements.txt', 'Cargo.toml', 'pom.xml', 'go.mod']
            found_files = []
            for file in common_files:
                if os.path.exists(os.path.join(git_root, file)):
                    found_files.append(file)
            
            if found_files:
                self.console.print(f"  Project Files: {', '.join(found_files)}")
            else:
                self.console.print("  Project Files: None detected")
            
            # Check .env file specifically (since jungle copies it)
            env_file = os.path.join(git_root, '.env')
            if os.path.exists(env_file):
                try:
                    stat = os.stat(env_file)
                    import datetime
                    mod_time = datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                    self.console.print(f"  .env File: Exists (modified {mod_time})")
                except:
                    self.console.print("  .env File: Exists")
            else:
                self.console.print("  .env File: Not found")
            
            # Git ignore info
            gitignore_file = os.path.join(git_root, '.gitignore')
            if os.path.exists(gitignore_file):
                try:
                    with open(gitignore_file, 'r') as f:
                        content = f.read()
                        if 'trees' in content.lower():
                            self.console.print("  .gitignore: Contains 'trees' pattern ✓")
                        else:
                            self.console.print("  .gitignore: No 'trees' pattern found")
                except:
                    self.console.print("  .gitignore: Exists but unreadable")
            else:
                self.console.print("  .gitignore: Not found")
            
            self.console.print()
            
            # Recent Activity
            self.console.print("[bold yellow]⏰ Recent Activity[/bold yellow]")
            try:
                result = subprocess.run(['git', '-C', git_root, 'log', '--oneline', '-5', '--all'], 
                                      capture_output=True, text=True, check=True)
                if result.stdout.strip():
                    self.console.print("  Recent Commits:")
                    for line in result.stdout.strip().split('\n'):
                        self.console.print(f"    {line}")
                else:
                    self.console.print("  Recent Commits: None")
            except subprocess.CalledProcessError:
                self.console.print("  Recent Commits: Error retrieving")
            
            self.console.print()
            
            # Performance/Health Checks
            self.console.print("[bold yellow]⚡ Health Checks[/bold yellow]")
            
            # Check if git is working
            try:
                subprocess.run(['git', '--version'], capture_output=True, check=True)
                self.console.print("  Git Command: [green]✓ Working[/green]")
            except:
                self.console.print("  Git Command: [red]✗ Not working[/red]")
            
            # Check repository integrity
            try:
                subprocess.run(['git', '-C', git_root, 'fsck', '--no-progress'], 
                              capture_output=True, check=True, timeout=5)
                self.console.print("  Repository Integrity: [green]✓ OK[/green]")
            except subprocess.TimeoutExpired:
                self.console.print("  Repository Integrity: [yellow]⏳ Check timeout[/yellow]")
            except subprocess.CalledProcessError:
                self.console.print("  Repository Integrity: [red]✗ Issues found[/red]")
            except:
                self.console.print("  Repository Integrity: [yellow]? Unable to check[/yellow]")
            
            # Check worktree list command
            try:
                subprocess.run(['git', '-C', git_root, 'worktree', 'list'], 
                              capture_output=True, check=True)
                self.console.print("  Worktree Command: [green]✓ Working[/green]")
            except:
                self.console.print("  Worktree Command: [red]✗ Not working[/red]")
            
        except Exception as e:
            self.console.print(f"[red]Error generating status: {e}[/red]")

    def _show_help(self):
        help_text = """
[bold cyan]🌿 Jungle - Git Worktree Manager[/bold cyan]

[bold]USAGE:[/bold]
  jungle [COMMAND] [OPTIONS]

[bold]COMMANDS:[/bold]
  [cyan]list[/cyan] (default)     List all worktrees with status
  [cyan]new[/cyan] <branch>      Create worktree (creates branch if needed)
  [cyan]delete[/cyan] <name>     Delete worktree (with merge safety check)
  [cyan]remove[/cyan] <name>     Same as delete
  [cyan]switch[/cyan] <name>     Switch to worktree directory
  [cyan]branches[/cyan]          List recent branches by activity
  [cyan]status[/cyan]            Show comprehensive debug information
  [cyan]help[/cyan]              Show this help message

[bold]OPTIONS:[/bold]
  [yellow]--table[/yellow]           Use table format instead of compact
  [yellow]--path[/yellow] <path>     Custom path for new worktree
  [yellow]--force[/yellow]           Skip merge safety check when deleting
  [yellow]--limit[/yellow] <n>       Number of branches to show (default: 10)

[bold]EXAMPLES:[/bold]
  [dim]jungle[/dim]                    # List all worktrees (compact)
  [dim]jungle --table[/dim]            # List worktrees in table format
  [dim]jungle new feature/login[/dim]   # Create branch + worktree at ./trees/feature-login
  [dim]jungle new bugfix --path ./fix[/dim]  # Create worktree at custom path
  [dim]jungle delete feature-login[/dim]    # Delete worktree (with safety check)
  [dim]jungle remove bugfix --force[/dim]   # Force delete without merge check
  [dim]jungle switch feature-login[/dim]    # Switch to worktree (copies cd command)
  [dim]jungle branches[/dim]           # Show recent branches by activity
  [dim]jungle branches --limit 5[/dim]     # Show only 5 most recent branches
  [dim]jungle status[/dim]             # Show comprehensive debug information

[bold]STATUS SYMBOLS:[/bold]
  [green]✓[/green] Clean       [yellow]?[/yellow] Untracked files
  [red]![/red] Modified     [red]S[/red] Staged changes
  [red]M[/red] Mixed        [red]✗[/red] Error

[bold]ORGANIZATION:[/bold]
  • New worktrees default to ./trees/ directory
  • Clean separation from main project files
  • Easy to .gitignore the entire trees/ folder

[bold]MOBILE-FRIENDLY:[/bold]
  • Compact format by default for small screens
  • Short paths and status symbols
  • Essential info only

[dim]Made with ❤️ for developers who live in worktrees[/dim]
        """
        self.console.print(help_text)

def main():
    parser = argparse.ArgumentParser(description='Git Worktree Manager', add_help=False)
    parser.add_argument('command', nargs='?', choices=['list', 'new', 'delete', 'remove', 'switch', 'branches', 'status', 'help'], default='list')
    parser.add_argument('branch', nargs='?', help='Branch/worktree name')
    parser.add_argument('--table', action='store_true', help='Use table format')
    parser.add_argument('--path', help='Custom path for new worktree')
    parser.add_argument('--force', action='store_true', help='Skip merge safety check when deleting')
    parser.add_argument('--limit', type=int, default=10, help='Number of branches to show')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.command == 'new' and not args.branch:
        print("Error: Branch name required for 'new' command")
        print("Usage: jungle new <branch> [--path <path>]")
        sys.exit(1)
    
    if args.command in ['delete', 'remove'] and not args.branch:
        print("Error: Worktree name required for 'delete/remove' command")
        print("Usage: jungle delete <worktree-name> [--force]")
        sys.exit(1)
    
    if args.command == 'switch' and not args.branch:
        print("Error: Worktree name required for 'switch' command")
        print("Usage: jungle switch <worktree-name>")
        sys.exit(1)
    
    jungle = JungleWorktreeManager()
    jungle.run(args)

if __name__ == "__main__":
    main()