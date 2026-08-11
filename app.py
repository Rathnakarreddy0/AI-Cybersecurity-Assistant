import os
import re
from copy import deepcopy

import streamlit as st

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False


# ============================================================
# CONFIG
# ============================================================

st.set_page_config(
    page_title="CyberStart Lab",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

GROQ_MODEL = "llama-3.3-70b-versatile"


# ============================================================
# LEVELS
# ============================================================

LEVELS = [
    (0, "Newbie"),
    (100, "Terminal Explorer"),
    (250, "File Hunter"),
    (500, "Command Apprentice"),
    (800, "System Explorer"),
    (1200, "Cyber Beginner"),
    (1800, "Cyber Learner"),
    (2500, "Lab Master"),
]


# ============================================================
# LINUX FILESYSTEM
# ============================================================

def create_linux_fs():
    return {
        "/": {
            "type": "dir",
            "children": {
                "home": {
                    "type": "dir",
                    "children": {
                        "student": {
                            "type": "dir",
                            "children": {
                                "Documents": {
                                    "type": "dir",
                                    "children": {
                                        "notes.txt": {
                                            "type": "file",
                                            "content": (
                                                "Linux is fun!\n"
                                                "Remember: pwd tells you where you are.\n"
                                            ),
                                        },
                                        "commands.txt": {
                                            "type": "file",
                                            "content": (
                                                "pwd\n"
                                                "ls\n"
                                                "cd\n"
                                                "cat\n"
                                                "mkdir\n"
                                                "touch\n"
                                            ),
                                        },
                                    },
                                },
                                "Downloads": {
                                    "type": "dir",
                                    "children": {
                                        "readme.txt": {
                                            "type": "file",
                                            "content": (
                                                "Welcome to CyberStart Lab.\n"
                                            ),
                                        },
                                    },
                                },
                                ".hidden_note": {
                                    "type": "file",
                                    "content": (
                                        "Hidden files can be displayed with ls -a.\n"
                                    ),
                                },
                                "practice_notes.txt": {
                                    "type": "file",
                                    "content": (
                                        "I should practice Linux every day.\n"
                                    ),
                                },
                                "secret.txt": {
                                    "type": "file",
                                    "content": (
                                        "FLAG{linux_file_hunter}\n"
                                    ),
                                },
                            },
                        },
                    },
                },
                "etc": {
                    "type": "dir",
                    "children": {
                        "hostname": {
                            "type": "file",
                            "content": "cyberstart-linux\n",
                        },
                        "hosts": {
                            "type": "file",
                            "content": (
                                "127.0.0.1 localhost\n"
                                "127.0.1.1 cyberstart-linux\n"
                            ),
                        },
                    },
                },
                "tmp": {
                    "type": "dir",
                    "children": {},
                },
                "var": {
                    "type": "dir",
                    "children": {
                        "log": {
                            "type": "dir",
                            "children": {
                                "system.log": {
                                    "type": "file",
                                    "content": (
                                        "INFO System started\n"
                                        "INFO User student logged in\n"
                                    ),
                                },
                            },
                        },
                    },
                },
            },
        },
    }


# ============================================================
# WINDOWS FILESYSTEM
# ============================================================

def create_windows_fs():
    return {
        "C:\\": {
            "type": "dir",
            "children": {
                "Users": {
                    "type": "dir",
                    "children": {
                        "Student": {
                            "type": "dir",
                            "children": {
                                "Documents": {
                                    "type": "dir",
                                    "children": {
                                        "notes.txt": {
                                            "type": "file",
                                            "content": (
                                                "Windows command practice.\n"
                                            ),
                                        },
                                    },
                                },
                                "Downloads": {
                                    "type": "dir",
                                    "children": {
                                        "readme.txt": {
                                            "type": "file",
                                            "content": (
                                                "Welcome to CyberStart Lab.\n"
                                            ),
                                        },
                                    },
                                },
                                "Desktop": {
                                    "type": "dir",
                                    "children": {},
                                },
                                "secret.txt": {
                                    "type": "file",
                                    "content": (
                                        "FLAG{windows_file_hunter}\n"
                                    ),
                                },
                            },
                        },
                    },
                },
                "Windows": {
                    "type": "dir",
                    "children": {
                        "System32": {
                            "type": "dir",
                            "children": {},
                        },
                    },
                },
                "Program Files": {
                    "type": "dir",
                    "children": {},
                },
                "Temp": {
                    "type": "dir",
                    "children": {},
                },
            },
        },
    }


# ============================================================
# SESSION STATE
# ============================================================

def initialize_state():
    defaults = {
        "xp": 0,
        "completed_missions": [],
        "completed_quizzes": [],
        "achievements": [],
        "linux_cwd": "/home/student",
        "windows_cwd": r"C:\Users\Student",
        "linux_output": [],
        "windows_output": [],
        "linux_fs": None,
        "windows_fs": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = deepcopy(value)

    if st.session_state.linux_fs is None:
        st.session_state.linux_fs = create_linux_fs()

    if st.session_state.windows_fs is None:
        st.session_state.windows_fs = create_windows_fs()


initialize_state()


# ============================================================
# LINUX PATH FUNCTIONS
# ============================================================

def normalize_linux_path(path, cwd):
    if not path:
        return cwd

    if not path.startswith("/"):
        path = cwd.rstrip("/") + "/" + path

    parts = []

    for part in path.split("/"):
        if part in ("", "."):
            continue

        if part == "..":
            if parts:
                parts.pop()
        else:
            parts.append(part)

    return "/" + "/".join(parts)


def linux_get_node(path):
    if path == "/":
        return st.session_state.linux_fs["/"]

    node = st.session_state.linux_fs["/"]

    parts = [part for part in path.split("/") if part]

    for part in parts:
        if node.get("type") != "dir":
            return None

        node = node.get("children", {}).get(part)

        if node is None:
            return None

    return node


def linux_parent(path):
    path = path.rstrip("/")

    if path == "":
        return None

    parts = [part for part in path.split("/") if part]

    if len(parts) <= 1:
        return "/"

    return "/" + "/".join(parts[:-1])


# ============================================================
# WINDOWS PATH FUNCTIONS
# ============================================================

def normalize_windows_path(path, cwd):
    if not path:
        return cwd

    path = path.replace("/", "\\")

    if len(path) >= 2 and path[1] == ":":
        absolute = path
    else:
        absolute = cwd.rstrip("\\") + "\\" + path

    drive = absolute[:2]
    parts = []

    for part in absolute[2:].split("\\"):
        if part in ("", "."):
            continue

        if part == "..":
            if parts:
                parts.pop()
        else:
            parts.append(part)

    if parts:
        return drive + "\\" + "\\".join(parts)

    return drive + "\\"


def windows_get_node(path):
    path = path.replace("/", "\\")

    if path != "C:\\":
        path = path.rstrip("\\")

    if path == "C:\\":
        return st.session_state.windows_fs["C:\\"]

    node = st.session_state.windows_fs["C:\\"]
    remainder = path[3:]

    for part in remainder.split("\\"):
        if not part:
            continue

        if node.get("type") != "dir":
            return None

        node = node.get("children", {}).get(part)

        if node is None:
            return None

    return node


# ============================================================
# LINUX COMMANDS
# ============================================================

def linux_ls(args):
    cwd = st.session_state.linux_cwd

    show_hidden = any(option in args for option in ["-a", "-la", "-al"])
    long_format = any(option in args for option in ["-l", "-la", "-al"])

    paths = [arg for arg in args if not arg.startswith("-")]

    target = cwd
    if paths:
        target = normalize_linux_path(paths[0], cwd)

    node = linux_get_node(target)

    if node is None:
        return f"ls: cannot access '{target}': No such file or directory"

    if node["type"] == "file":
        return target

    names = list(node.get("children", {}).keys())

    if not show_hidden:
        names = [name for name in names if not name.startswith(".")]

    if long_format:
        lines = []
        for name in names:
            child = node["children"][name]
            if child["type"] == "dir":
                permissions = "drwxr-xr-x"
            else:
                permissions = "-rw-r--r--"
            lines.append(f"{permissions}  student  {name}")
        return "\n".join(lines)

    return "  ".join(names)


def linux_find(args):
    if not args:
        return "find: missing path"

    start = args[0]
    if start.startswith("-"):
        start = "."

    start = normalize_linux_path(start, st.session_state.linux_cwd)
    node = linux_get_node(start)

    if node is None:
        return f"find: '{start}': No such file or directory"

    pattern = None
    if "-name" in args:
        index = args.index("-name")
        if index + 1 < len(args):
            pattern = args[index + 1].strip("'\"")

    results = []

    def walk(current_path, current_node):
        if current_node["type"] != "dir":
            return

        for name, child in current_node.get("children", {}).items():
            child_path = current_path.rstrip("/") + "/" + name

            if pattern is None:
                results.append(child_path)
            else:
                regex = "^" + re.escape(pattern).replace(r"\*", ".*") + "$"
                if re.match(regex, name):
                    results.append(child_path)

            if child["type"] == "dir":
                walk(child_path, child)

    walk(start, node)
    return "\n".join(results)


def linux_grep(args):
    if len(args) < 2:
        return "Usage: grep PATTERN FILE"

    pattern = args[0].strip("'\"")
    filename = args[-1].strip("'\"")

    path = normalize_linux_path(filename, st.session_state.linux_cwd)
    node = linux_get_node(path)

    if node is None or node["type"] != "file":
        return f"grep: {filename}: No such file or directory"

    matches = []
    for line in node["content"].splitlines():
        if pattern.lower() in line.lower():
            matches.append(line)

    return "\n".join(matches)


def execute_linux(command):
    command = command.strip()
    if not command:
        return ""

    parts = command.split()
    cmd = parts[0]
    args = parts[1:]

    if cmd == "help":
        return (
            "Supported commands:\n"
            "pwd\nls\ncd\ncat\nmkdir\ntouch\nrm\n"
            "find\ngrep\nwhoami\nid\nuname\necho\nman\nclear"
        )

    if cmd == "pwd":
        return st.session_state.linux_cwd

    if cmd == "whoami":
        return "student"

    if cmd == "id":
        return "uid=1000(student) gid=1000(student) groups=1000(student)"

    if cmd == "uname":
        if "-a" in args:
            return "Linux cyberstart 6.1.0 x86_64 GNU/Linux"
        return "Linux"

    if cmd == "ls":
        return linux_ls(args)

    if cmd == "cd":
        target = args[0] if args else "/home/student"
        new_path = normalize_linux_path(target, st.session_state.linux_cwd)
        node = linux_get_node(new_path)

        if node is None:
            return f"bash: cd: {target}: No such file or directory"

        if node["type"] != "dir":
            return f"bash: cd: {target}: Not a directory"

        st.session_state.linux_cwd = new_path
        return ""

    if cmd == "cat":
        if not args:
            return "cat: missing file operand"

        path = normalize_linux_path(args[0], st.session_state.linux_cwd)
        node = linux_get_node(path)

        if node is None:
            return f"cat: {args[0]}: No such file or directory"

        if node["type"] != "file":
            return f"cat: {args[0]}: Is a directory"

        return node["content"]

    if cmd in ["head", "tail"]:
        if not args:
            return f"{cmd}: missing file"

        path = normalize_linux_path(args[-1], st.session_state.linux_cwd)
        node = linux_get_node(path)

        if node is None or node["type"] != "file":
            return f"{cmd}: file not found"

        lines = node["content"].splitlines()
        if cmd == "head":
            return "\n".join(lines[:10])

        return "\n".join(lines[-10:])

    if cmd == "mkdir":
        if not args:
            return "mkdir: missing operand"

        name = args[-1]
        parent = linux_get_node(st.session_state.linux_cwd)

        if name in parent["children"]:
            return f"mkdir: cannot create directory '{name}': File exists"

        parent["children"][name] = {"type": "dir", "children": {}}
        return ""

    if cmd == "touch":
        if not args:
            return "touch: missing file operand"

        name = args[-1]
        parent = linux_get_node(st.session_state.linux_cwd)

        if name not in parent["children"]:
            parent["children"][name] = {"type": "file", "content": ""}

        return ""

    if cmd == "rm":
        if not args:
            return "rm: missing operand"

        target = normalize_linux_path(args[-1], st.session_state.linux_cwd)
        if target == "/":
            return "rm: cannot remove root"

        parent_path = linux_parent(target)
        parent = linux_get_node(parent_path)
        name = target.rstrip("/").split("/")[-1]

        if parent is None or name not in parent.get("children", {}):
            return f"rm: cannot remove '{args[-1]}': No such file or directory"

        del parent["children"][name]
        return ""

    if cmd == "find":
        return linux_find(args)

    if cmd == "grep":
        return linux_grep(args)

    if cmd == "echo":
        return " ".join(args)

    if cmd == "man":
        manuals = {
            "ls": "ls - list directory contents",
            "cd": "cd - change the current directory",
            "pwd": "pwd - print working directory",
            "cat": "cat - display file contents",
            "find": "find - search for files",
            "grep": "grep - search text",
            "mkdir": "mkdir - create directories",
            "touch": "touch - create files",
        }
        topic = args[0] if args else ""
        return manuals.get(topic, "No manual entry.")

    if cmd == "clear":
        st.session_state.linux_output = []
        return ""

    return f"bash: {cmd}: command not found"


# ============================================================
# WINDOWS COMMANDS
# ============================================================

def windows_dir():
    node = windows_get_node(st.session_state.windows_cwd)

    if node is None:
        return "The system cannot find the path specified."

    lines = [f" Directory of {st.session_state.windows_cwd}", ""]

    for name, child in node.get("children", {}).items():
        if child["type"] == "dir":
            lines.append(f"<DIR>          {name}")
        else:
            lines.append(f"               {name}")

    return "\n".join(lines)


def execute_windows(command):
    command = command.strip()
    if not command:
        return ""

    parts = command.split()
    cmd = parts[0].lower()
    args = parts[1:]

    if cmd == "help":
        return (
            "Supported commands:\n"
            "DIR\nCD\nTYPE\nCLS\nWHOAMI\nHOSTNAME\nIPCONFIG\nPING\nMKDIR\nECHO"
        )

    if cmd == "cls":
        st.session_state.windows_output = []
        return ""

    if cmd == "cd":
        if not args:
            return st.session_state.windows_cwd

        new_path = normalize_windows_path(args[0], st.session_state.windows_cwd)
        node = windows_get_node(new_path)

        if node is None:
            return "The system cannot find the path specified."

        if node["type"] != "dir":
            return "The directory name is invalid."

        st.session_state.windows_cwd = new_path
        return ""

    if cmd == "dir":
        return windows_dir()

    if cmd == "type":
        if not args:
            return "The syntax of the command is incorrect."

        path = normalize_windows_path(args[0], st.session_state.windows_cwd)
        node = windows_get_node(path)

        if node is None:
            return "The system cannot find the file specified."

        if node["type"] != "file":
            return "The system cannot access the file."

        return node["content"]

    if cmd == "whoami":
        return r"cyberstart\student"

    if cmd == "hostname":
        return "CYBERSTART-PC"

    if cmd == "ipconfig":
        return (
            "Windows IP Configuration\n\n"
            "Ethernet adapter Ethernet:\n\n"
            "   IPv4 Address. . . . . . . . . . . : 192.168.1.25\n"
            "   Subnet Mask . . . . . . . . . . . : 255.255.255.0\n"
            "   Default Gateway . . . . . . . . . : 192.168.1.1"
        )

    if cmd == "ping":
        target = args[0] if args else "127.0.0.1"
        return (
            f"Pinging {target} with 32 bytes of data:\n\n"
            f"Reply from {target}: bytes=32 time<1ms TTL=128\n"
            f"Reply from {target}: bytes=32 time<1ms TTL=128\n\n"
            "Ping statistics:\n"
            "    Packets: Sent = 2, Received = 2, Lost = 0 (0% loss)"
        )

    if cmd in ["mkdir", "md"]:
        if not args:
            return "The syntax of the command is incorrect."

        name = args[-1]
        parent = windows_get_node(st.session_state.windows_cwd)

        if name in parent["children"]:
            return "A subdirectory or file with that name already exists."

        parent["children"][name] = {"type": "dir", "children": {}}
        return ""

    if cmd == "echo":
        return " ".join(args)

    return f"'{cmd}' is not recognized as an internal or external command."


# ============================================================
# LESSONS
# ============================================================

LINUX_LESSONS = {
    "What is Linux?": """
### What is Linux?

Linux is an operating-system family widely used
on servers, cloud systems, embedded devices and
security labs.

A terminal gives you a text-based way to interact
with the operating system.

You will work with:

- Files
- Directories
- Users
- Permissions
- Processes
- Networking
""",
    "pwd": """
### pwd

`pwd` means **Print Working Directory**.

It tells you where you currently are.

Example:

```bash
pwd
