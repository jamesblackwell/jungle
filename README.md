# 🌿 Jungle - Git Worktree Manager

A mobile-friendly CLI tool for managing Git worktrees with ease. Perfect for developers who work with multiple feature branches simultaneously.

## ✨ Features

- **📱 Mobile-Friendly**: Compact display optimized for small screens
- **🌳 Smart Organization**: Auto-organizes worktrees in `./trees/` directory
- **🔍 Branch Discovery**: List recent branches by activity
- **🛡️ Safety Checks**: Warns before deleting unmerged branches
- **⚡ Quick Creation**: Creates branches and worktrees in one command
- **🎨 Rich Display**: Color-coded status indicators and clean formatting

## 🚀 Installation

```bash
pip install -e .
```

## 📖 Usage

### List Worktrees (Default)
```bash
jungle                    # Compact mobile-friendly list
jungle --table           # Traditional table format
```

### Create Worktree
```bash
jungle new feature/login  # Creates branch + worktree at ./trees/feature-login
jungle new existing-branch # Creates worktree for existing branch
jungle new branch --path ./custom  # Custom path
```

### Delete Worktree
```bash
jungle delete feature-login        # Safe delete with merge check
jungle remove branch --force       # Skip merge safety check
```

### Browse Branches
```bash
jungle branches              # Show 10 recent branches by activity
jungle branches --limit 5    # Show only 5 branches
```

## 📊 Status Indicators

- ✅ **Clean** - No changes
- ❗ **Modified** - Unstaged changes  
- 🔵 **Staged** - Staged changes
- ❓ **Untracked** - Untracked files
- 🔄 **Mixed** - Multiple types of changes

## 🌳 Branch Indicators

- 🌿 **Has worktree**
- 📍 **Local branch**
- 📡 **Remote branch**

## 🏗️ Organization

Jungle keeps your project clean by:
- Storing all worktrees in `./trees/` directory
- Using branch names as folder names (with `/` → `-`)
- Making it easy to add `trees/` to `.gitignore`

## 🔧 Commands

| Command | Description |
|---------|-------------|
| `jungle` | List all worktrees (default) |
| `jungle new <branch>` | Create worktree (creates branch if needed) |
| `jungle delete <name>` | Delete worktree with safety checks |
| `jungle branches` | List recent branches by activity |
| `jungle help` | Show help message |

## 🤝 Perfect For

- **Feature development** - Work on multiple features simultaneously
- **Code reviews** - Quick access to different branches
- **Bug fixes** - Isolate fixes without disrupting main work
- **Mobile development** - Clean, readable output on small screens
- **Team collaboration** - See what branches are active

## 🛡️ Safety Features

- **Merge detection** - Warns if deleting unmerged branches
- **Interactive confirmation** - Ask before destructive operations
- **Force override** - Skip checks when needed with `--force`
- **Protected main** - Cannot delete main worktree

---

*Made with ❤️ for developers who live in worktrees*