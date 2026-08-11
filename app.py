import os
import re
from copy import deepcopy
import streamlit as st

try:
    from groq import Groq
except ImportError:
    Groq = None

st.set_page_config(page_title='CyberStart Lab', page_icon='🛡️', layout='wide')
MODEL = 'llama-3.3-70b-versatile'


def linux_fs():
    return {'/': {'type': 'dir', 'children': {
        'home': {'type': 'dir', 'children': {'student': {'type': 'dir', 'children': {
            'Documents': {'type': 'dir', 'children': {
                'notes.txt': {'type': 'file', 'content': 'Linux is fun!\nRemember: pwd tells you where you are.\n'},
                'commands.txt': {'type': 'file', 'content': 'pwd\nls\ncd\ncat\nmkdir\ntouch\n'}
            }},
            'Downloads': {'type': 'dir', 'children': {'readme.txt': {'type': 'file', 'content': 'Welcome to CyberStart Lab.\n'}}},
            '.hidden_note': {'type': 'file', 'content': 'Hidden files are shown with ls -a.\n'},
            'notes.txt': {'type': 'file', 'content': 'Practice Linux every day.\n'},
            'secret.txt': {'type': 'file', 'content': 'FLAG{linux_file_hunter}\n'}
        }}}},
        'etc': {'type': 'dir', 'children': {
            'hostname': {'type': 'file', 'content': 'cyberstart-linux\n'},
            'hosts': {'type': 'file', 'content': '127.0.0.1 localhost\n127.0.1.1 cyberstart-linux\n'}
        }},
        'tmp': {'type': 'dir', 'children': {}},
        'var': {'type': 'dir', 'children': {'log': {'type': 'dir', 'children': {
            'system.log': {'type': 'file', 'content': 'INFO System started\nINFO User student logged in\n'}
        }}}}
    }}}


def windows_fs():
    return {'C:\\': {'type': 'dir', 'children': {
        'Users': {'type': 'dir', 'children': {'Student': {'type': 'dir', 'children': {
            'Desktop': {'type': 'dir', 'children': {}},
            'Documents': {'type': 'dir', 'children': {'notes.txt': {'type': 'file', 'content': 'Windows command practice.\n'}}},
            'Downloads': {'type': 'dir', 'children': {'readme.txt': {'type': 'file', 'content': 'Welcome to CyberStart Lab.\n'}}},
            'secret.txt': {'type': 'file', 'content': 'FLAG{windows_file_hunter}\n'}
        }}}},
        'Windows': {'type': 'dir', 'children': {'System32': {'type': 'dir', 'children': {}}}},
        'Program Files': {'type': 'dir', 'children': {}},
        'Temp': {'type': 'dir', 'children': {}}
    }}}


def init_state():
    defaults = {
        'xp': 0,
        'linux_cwd': '/home/student',
        'windows_cwd': r'C:\Users\Student',
        'linux_output': [],
        'windows_output': [],
        'completed_missions': [],
        'completed_quizzes': [],
        'achievements': [],
        'linux_tree': None,
        'windows_tree': None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = deepcopy(value)
    if st.session_state.linux_tree is None:
        st.session_state.linux_tree = linux_fs()
    if st.session_state.windows_tree is None:
        st.session_state.windows_tree = windows_fs()


init_state()


def level_info():
    levels = [(0, 'Newbie'), (100, 'Terminal Explorer'), (250, 'File Hunter'), (500, 'Command Apprentice'), (800, 'System Explorer'), (1200, 'Cyber Beginner'), (1800, 'Cyber Learner'), (2500, 'Lab Master')]
    current = levels[0]
    nxt = None
    for item in levels:
        if st.session_state.xp >= item[0]:
            current = item
    for item in levels:
        if item[0] > st.session_state.xp:
            nxt = item
            break
    return current, nxt


def add_xp(amount):
    before = level_info()[0]
    st.session_state.xp += amount
    after = level_info()[0]
    if after[0] > before[0]:
        st.toast('🎉 Level up: ' + after[1], icon='🏆')


def check_achievements():
    checks = [
        ('first', st.session_state.xp >= 50, '🥇 First Steps'),
        ('missions', len(st.session_state.completed_missions) >= 3, '🎯 Mission Runner'),
        ('quiz', len(st.session_state.completed_quizzes) >= 3, '🧠 Quiz Master'),
        ('beginner', st.session_state.xp >= 500, '🛡️ Cyber Beginner'),
    ]
    for ident, condition, title in checks:
        if condition and ident not in st.session_state.achievements:
            st.session_state.achievements.append(ident)
            st.toast('Achievement unlocked: ' + title)


def linux_path(path, cwd):
    if not path:
        return cwd
    if not path.startswith('/'):
        path = cwd.rstrip('/') + '/' + path
    parts = []
    for item in path.split('/'):
        if item in ('', '.'):
            continue
        if item == '..':
            if parts:
                parts.pop()
        else:
            parts.append(item)
    return '/' + '/'.join(parts)


def linux_node(path):
    if path == '/':
        return st.session_state.linux_tree['/']
    node = st.session_state.linux_tree['/']
    for item in [x for x in path.split('/') if x]:
        if node.get('type') != 'dir':
            return None
        node = node.get('children', {}).get(item)
        if node is None:
            return None
    return node


def linux_parent(path):
    clean = path.rstrip('/')
    if clean in ('', '/'):
        return None
    parts = [x for x in clean.split('/') if x]
    return '/' if len(parts) <= 1 else '/' + '/'.join(parts[:-1])


def linux_ls(args):
    cwd = st.session_state.linux_cwd
    hidden = any(x in args for x in ('-a', '-la', '-al'))
    long_mode = any(x in args for x in ('-l', '-la', '-al'))
    paths = [x for x in args if not x.startswith('-')]
    target = linux_path(paths[0], cwd) if paths else cwd
    node = linux_node(target)
    if node is None:
        return "ls: cannot access '" + target + "': No such file or directory"
    if node['type'] == 'file':
        return target
    names = list(node.get('children', {}).keys())
    if not hidden:
        names = [x for x in names if not x.startswith('.')]
    if long_mode:
        out = []
        for name in names:
            perm = 'drwxr-xr-x' if node['children'][name]['type'] == 'dir' else '-rw-r--r--'
            out.append(perm + '  student  ' + name)
        return '\n'.join(out)
    return '  '.join(names)


def linux_find(args):
    start = args[0] if args and not args[0].startswith('-') else '.'
    start = linux_path(start, st.session_state.linux_cwd)
    node = linux_node(start)
    if node is None:
        return "find: '" + start + "': No such file or directory"
    pattern = None
    if '-name' in args:
        i = args.index('-name')
        if i + 1 < len(args):
            pattern = args[i + 1].strip("'\"")
    results = []
    def walk(current, current_node):
        if current_node['type'] != 'dir':
            return
        for name, child in current_node.get('children', {}).items():
            child_path = current.rstrip('/') + '/' + name
            matched = pattern is None
            if pattern is not None:
                regex = '^' + re.escape(pattern).replace(r'\*', '.*') + '$'
                matched = re.match(regex, name) is not None
            if matched:
                results.append(child_path)
            if child['type'] == 'dir':
                walk(child_path, child)
    walk(start, node)
    return '\n'.join(results)


def linux_grep(args):
    if len(args) < 2:
        return 'Usage: grep PATTERN FILE'
    pattern = args[0].strip("'\"")
    filename = args[-1].strip("'\"")
    node = linux_node(linux_path(filename, st.session_state.linux_cwd))
    if node is None or node['type'] != 'file':
        return 'grep: ' + filename + ': No such file or directory'
    return '\n'.join(line for line in node['content'].splitlines() if pattern.lower() in line.lower())


def run_linux(command):
    command = command.strip()
    if not command:
        return ''
    parts = command.split()
    cmd, args = parts[0], parts[1:]
    if cmd == 'help':
        return '\n'.join(['pwd', 'ls', 'cd', 'cat', 'mkdir', 'touch', 'rm', 'find', 'grep', 'whoami', 'id', 'uname', 'echo', 'man', 'clear'])
    if cmd == 'pwd': return st.session_state.linux_cwd
    if cmd == 'whoami': return 'student'
    if cmd == 'id': return 'uid=1000(student) gid=1000(student) groups=1000(student)'
    if cmd == 'uname': return 'Linux cyberstart 6.1.0 x86_64 GNU/Linux' if '-a' in args else 'Linux'
    if cmd == 'ls': return linux_ls(args)
    if cmd == 'find': return linux_find(args)
    if cmd == 'grep': return linux_grep(args)
    if cmd == 'echo': return ' '.join(args)
    if cmd == 'clear':
        st.session_state.linux_output = []
        return ''
    if cmd == 'cd':
        target = args[0] if args else '/home/student'
        new_path = linux_path(target, st.session_state.linux_cwd)
        node = linux_node(new_path)
        if node is None: return 'bash: cd: ' + target + ': No such file or directory'
        if node['type'] != 'dir': return 'bash: cd: ' + target + ': Not a directory'
        st.session_state.linux_cwd = new_path
        return ''
    if cmd == 'cat':
        if not args: return 'cat: missing file operand'
        node = linux_node(linux_path(args[0], st.session_state.linux_cwd))
        if node is None: return 'cat: ' + args[0] + ': No such file or directory'
        if node['type'] != 'file': return 'cat: ' + args[0] + ': Is a directory'
        return node['content']
    if cmd == 'mkdir':
        if not args: return 'mkdir: missing operand'
        name = args[-1]
        parent = linux_node(st.session_state.linux_cwd)
        if name in parent['children']: return "mkdir: cannot create directory '" + name + "': File exists"
        parent['children'][name] = {'type': 'dir', 'children': {}}
        return ''
    if cmd == 'touch':
        if not args: return 'touch: missing file operand'
        name = args[-1]
        parent = linux_node(st.session_state.linux_cwd)
        if name not in parent['children']: parent['children'][name] = {'type': 'file', 'content': ''}
        return ''
    if cmd == 'rm':
        if not args: return 'rm: missing operand'
        target = linux_path(args[-1], st.session_state.linux_cwd)
        if target == '/': return 'rm: cannot remove root'
        parent = linux_node(linux_parent(target))
        name = target.rstrip('/').split('/')[-1]
        if parent is None or name not in parent.get('children', {}): return "rm: cannot remove '" + args[-1] + "': No such file or directory"
        del parent['children'][name]
        return ''
    if cmd == 'man':
        manuals = {'ls': 'ls - list directory contents', 'cd': 'cd - change directory', 'pwd': 'pwd - print working directory', 'cat': 'cat - display file contents', 'find': 'find - search for files', 'grep': 'grep - search text', 'mkdir': 'mkdir - create directories'}
        return manuals.get(args[0] if args else '', 'No manual entry.')
    return 'bash: ' + cmd + ': command not found'


def windows_path(path, cwd):
    path = path.replace('/', '\\')
    absolute = path if len(path) >= 2 and path[1] == ':' else cwd.rstrip('\\') + '\\' + path
    drive = absolute[:2]
    parts = []
    for item in absolute[2:].split('\\'):
        if item in ('', '.'): continue
        if item == '..':
            if parts: parts.pop()
        else: parts.append(item)
    return drive + '\\' + '\\'.join(parts) if parts else drive + '\\'


def windows_node(path):
    path = path.replace('/', '\\')
    if path == 'C:\\': return st.session_state.windows_tree['C:\\']
    node = st.session_state.windows_tree['C:\\']
    for item in path.rstrip('\\')[3:].split('\\'):
        if not item: continue
        if node.get('type') != 'dir': return None
        node = node.get('children', {}).get(item)
        if node is None: return None
    return node


def windows_dir():
    node = windows_node(st.session_state.windows_cwd)
    if node is None: return 'The system cannot find the path specified.'
    lines = [' Directory of ' + st.session_state.windows_cwd, '']
    for name, child in node.get('children', {}).items():
        lines.append(('<DIR>          ' if child['type'] == 'dir' else '               ') + name)
    return '\n'.join(lines)


def run_windows(command):
    command = command.strip()
    if not command: return ''
    parts = command.split()
    cmd, args = parts[0].lower(), parts[1:]
    if cmd == 'help': return '\n'.join(['DIR', 'CD', 'TYPE', 'CLS', 'WHOAMI', 'HOSTNAME', 'IPCONFIG', 'PING', 'MKDIR', 'ECHO'])
    if cmd == 'cls':
        st.session_state.windows_output = []
        return ''
    if cmd == 'cd':
        if not args: return st.session_state.windows_cwd
        new_path = windows_path(args[0], st.session_state.windows_cwd)
        node = windows_node(new_path)
        if node is None: return 'The system cannot find the path specified.'
        if node['type'] != 'dir': return 'The directory name is invalid.'
        st.session_state.windows_cwd = new_path
        return ''
    if cmd == 'dir': return windows_dir()
    if cmd == 'type':
        if not args: return 'The syntax of the command is incorrect.'
        node = windows_node(windows_path(args[0], st.session_state.windows_cwd))
        if node is None or node['type'] != 'file': return 'The system cannot find the file specified.'
        return node['content']
    if cmd == 'whoami': return r'cyberstart\student'
    if cmd == 'hostname': return 'CYBERSTART-PC'
    if cmd == 'ipconfig': return 'Windows IP Configuration\n\nIPv4 Address: 192.168.1.25\nSubnet Mask: 255.255.255.0\nDefault Gateway: 192.168.1.1'
    if cmd == 'ping':
        target = args[0] if args else '127.0.0.1'
        return 'Pinging ' + target + ' with 32 bytes of data:\nReply from ' + target + ': bytes=32 time<1ms TTL=128\nReply from ' + target + ': bytes=32 time<1ms TTL=128\n\nPackets: Sent = 2, Received = 2, Lost = 0 (0% loss)'
    if cmd in ('mkdir', 'md'):
        if not args: return 'The syntax of the command is incorrect.'
        name = args[-1]
        parent = windows_node(st.session_state.windows_cwd)
        if name in parent['children']: return 'A subdirectory or file with that name already exists.'
        parent['children'][name] = {'type': 'dir', 'children': {}}
        return ''
    if cmd == 'echo': return ' '.join(args)
    return "'" + cmd + "' is not recognized as an internal or external command."


LINUX_LESSONS = {
    'What is Linux?': 'Linux is an operating-system family used on servers, cloud systems, embedded devices and security labs.\n\nA terminal lets you interact with the OS using text commands.',
    'pwd': 'pwd means Print Working Directory. It tells you where you currently are.\n\nExample:\n\n    pwd',
    'ls': 'ls lists files and directories.\n\nExamples:\n\n    ls\n    ls -l\n    ls -a\n    ls -la',
    'cd': 'cd means change directory.\n\nExamples:\n\n    cd Documents\n    cd ..\n    cd /home/student',
    'cat': 'cat displays the contents of a text file.\n\nExample:\n\n    cat notes.txt',
    'find': 'find searches for files and directories.\n\nExample:\n\n    find /home/student -name secret.txt',
    'grep': 'grep searches text inside files.\n\nExample:\n\n    grep password notes.txt',
}

WINDOWS_LESSONS = {
    'Windows Filesystem': 'Common Windows locations include C:\\Windows, C:\\Users, C:\\Program Files and C:\\Temp.\n\nPersonal files normally live below C:\\Users\\Student.',
    'dir': 'DIR lists files and folders.\n\nExample:\n\n    dir',
    'cd': 'CD changes directories.\n\nExamples:\n\n    cd Documents\n    cd ..\n    cd',
    'type': 'TYPE displays a text file.\n\nExample:\n\n    type notes.txt',
    'whoami': 'WHOAMI shows the current Windows user.\n\nExample:\n\n    whoami',
    'ipconfig': 'IPCONFIG displays Windows network configuration.\n\nExample:\n\n    ipconfig',
    'ping': 'PING tests basic network connectivity.\n\nExample:\n\n    ping 127.0.0.1',
}

MISSIONS = [
    {'id': 'l1', 'os': 'Linux', 'title': '📍 Where Am I?', 'objective': 'Print your current Linux directory.', 'answers': ['pwd'], 'xp': 50, 'hint': 'The command begins with p.'},
    {'id': 'l2', 'os': 'Linux', 'title': '📂 Explore', 'objective': 'List the current directory.', 'answers': ['ls', 'ls -a', 'ls -la', 'ls -al'], 'xp': 50, 'hint': 'Think about the command meaning list.'},
    {'id': 'l3', 'os': 'Linux', 'title': '🕵️ Find the Secret', 'objective': 'Find secret.txt below /home/student.', 'answers': ['find /home/student -name secret.txt', "find /home/student -name 'secret.txt'", 'find /home/student -name "secret.txt"'], 'xp': 100, 'hint': 'Use find with -name.'},
    {'id': 'l4', 'os': 'Linux', 'title': '📖 Read the Secret', 'objective': 'Display /home/student/secret.txt.', 'answers': ['cat secret.txt', 'cat /home/student/secret.txt'], 'xp': 100, 'hint': 'The command used to display a file is cat.'},
    {'id': 'l5', 'os': 'Linux', 'title': '🔎 Find Logs', 'objective': 'Find system.log below /var.', 'answers': ['find /var -name system.log', "find /var -name 'system.log'", 'find /var -name "system.log"'], 'xp': 100, 'hint': 'Search below /var using find.'},
    {'id': 'w1', 'os': 'Windows', 'title': '📍 Find Your Location', 'objective': 'Show your current Windows directory.', 'answers': ['cd'], 'xp': 50, 'hint': 'In CMD, CD without a path shows the current directory.'},
    {'id': 'w2', 'os': 'Windows', 'title': '📂 List Files', 'objective': 'List files and folders.', 'answers': ['dir'], 'xp': 50, 'hint': 'The classic Windows command is DIR.'},
    {'id': 'w3', 'os': 'Windows', 'title': '🕵️ Read the Secret', 'objective': 'Display secret.txt.', 'answers': ['type secret.txt'], 'xp': 100, 'hint': 'Windows CMD uses TYPE to display text files.'},
    {'id': 'w4', 'os': 'Windows', 'title': '🌐 Check Network', 'objective': 'Display network configuration.', 'answers': ['ipconfig'], 'xp': 100, 'hint': 'The command starts with ip.'},
]

QUIZZES = [
    {'id': 'q1', 'q': 'Which Linux command shows your current directory?', 'options': ['ls', 'pwd', 'cd', 'cat'], 'answer': 'pwd', 'xp': 25},
    {'id': 'q2', 'q': 'Which Linux command lists directory contents?', 'options': ['ls', 'pwd', 'mkdir', 'whoami'], 'answer': 'ls', 'xp': 25},
    {'id': 'q3', 'q': 'Which Linux command displays a text file?', 'options': ['cat', 'cd', 'mkdir', 'ps'], 'answer': 'cat', 'xp': 25},
    {'id': 'q4', 'q': 'Which Windows CMD command lists files?', 'options': ['ls', 'dir', 'cat', 'pwd'], 'answer': 'dir', 'xp': 25},
    {'id': 'q5', 'q': 'Which Windows command shows network configuration?', 'options': ['ipconfig', 'dir', 'type', 'hostname'], 'answer': 'ipconfig', 'xp': 25},
]


def ask_ai(question):
    key = None
    try:
        key = st.secrets.get('GROQ_API_KEY')
    except Exception:
        pass
    key = key or os.getenv('GROQ_API_KEY')
    if not key or Groq is None:
        return '🤖 AI Mentor is not configured. Add GROQ_API_KEY to Streamlit Secrets.'
    client = Groq(api_key=key)
    system = 'You are CyberStart Lab beginner mentor. Teach Linux, Windows, filesystems, commands and safe introductory cybersecurity. Explain commands and why they work. Prefer hints over simply giving mission answers. Never claim to execute commands on a real machine.'
    try:
        response = client.chat.completions.create(model=MODEL, messages=[{'role': 'system', 'content': system}, {'role': 'user', 'content': question}], temperature=0.4)
        return response.choices[0].message.content
    except Exception as exc:
        return 'AI error: ' + str(exc)


current_level, next_level = level_info()
with st.sidebar:
    st.title('🛡️ CyberStart Lab')
    st.metric('XP', st.session_state.xp)
    st.write('**Level:** ' + current_level[1])
    if next_level:
        st.caption(str(next_level[0] - st.session_state.xp) + ' XP to ' + next_level[1])
    st.divider()
    page = st.radio('Learning', ['🏠 Dashboard', '🐧 Linux', '🪟 Windows', '🎯 Missions', '🧩 Quiz', '🤖 AI Mentor', '🏆 Achievements'])
    st.divider()
    st.caption('All terminals are simulated. No real shell commands are executed.')


if page == '🏠 Dashboard':
    st.title('🛡️ CyberStart Lab')
    st.subheader('Learn Linux and Windows by doing.')
    a, b, c = st.columns(3)
    a.metric('XP', st.session_state.xp)
    b.metric('Missions', len(st.session_state.completed_missions))
    c.metric('Achievements', len(st.session_state.achievements))
    st.divider()
    left, right = st.columns(2)
    with left:
        st.header('🐧 Linux')
        st.write('Learn terminal basics, navigation, files, directories and searching.')
        st.code('pwd\nls\ncd Documents\ncat notes.txt\nfind /home/student -name secret.txt')
    with right:
        st.header('🪟 Windows')
        st.write('Learn CMD, Windows paths, files and basic networking.')
        st.code('cd\ndir\ncd Documents\ntype notes.txt\nipconfig')
    st.divider()
    st.header('🚀 Learning loop')
    st.write('📚 Learn → 💻 Practice → 🎯 Solve missions → 🏆 Earn XP → 🤖 Ask the mentor')

elif page == '🐧 Linux':
    st.title('🐧 Linux Fundamentals')
    tab1, tab2, tab3 = st.tabs(['📚 Lessons', '💻 Terminal', '🗂️ Filesystem'])
    with tab1:
        lesson = st.selectbox('Choose a lesson', list(LINUX_LESSONS.keys()))
        st.markdown(LINUX_LESSONS[lesson])
    with tab2:
        st.info('Safe simulated Linux terminal.')
        for item in st.session_state.linux_output:
            if item['kind'] == 'command': st.code('student@cyberlab:' + item['cwd'] + '$ ' + item['command'])
            elif item['text']: st.code(item['text'])
        command = st.text_input('Command', placeholder='Try: pwd', key='linux_cmd')
        x, y = st.columns(2)
        if x.button('▶ Run', key='linux_run', type='primary'):
            output = run_linux(command)
            st.session_state.linux_output.append({'kind': 'command', 'cwd': st.session_state.linux_cwd, 'command': command})
            st.session_state.linux_output.append({'kind': 'output', 'text': output})
            st.rerun()
        if y.button('🧹 Clear', key='linux_clear'):
            st.session_state.linux_output = []
            st.rerun()
        st.subheader('Try these')
        st.code('pwd\nls\nls -la\ncd Documents\ncat notes.txt\nfind /home/student -name secret.txt\nwhoami\nid')
    with tab3:
        st.code('/\n├── home/\n│   └── student/\n│       ├── Documents/\n│       ├── Downloads/\n│       ├── .hidden_note\n│       ├── notes.txt\n│       └── secret.txt\n├── etc/\n├── tmp/\n└── var/\n    └── log/\n        └── system.log')

elif page == '🪟 Windows':
    st.title('🪟 Windows Fundamentals')
    tab1, tab2, tab3 = st.tabs(['📚 Lessons', '💻 CMD', '🗂️ Filesystem'])
    with tab1:
        lesson = st.selectbox('Choose a lesson', list(WINDOWS_LESSONS.keys()))
        st.markdown(WINDOWS_LESSONS[lesson])
    with tab2:
        st.info('Safe simulated Windows CMD.')
        for item in st.session_state.windows_output:
            if item['kind'] == 'command': st.code(item['cwd'] + '> ' + item['command'])
            elif item['text']: st.code(item['text'])
        command = st.text_input('Command', placeholder='Try: dir', key='windows_cmd')
        x, y = st.columns(2)
        if x.button('▶ Run', key='windows_run', type='primary'):
            output = run_windows(command)
            st.session_state.windows_output.append({'kind': 'command', 'cwd': st.session_state.windows_cwd, 'command': command})
            st.session_state.windows_output.append({'kind': 'output', 'text': output})
            st.rerun()
        if y.button('🧹 Clear', key='windows_clear'):
            st.session_state.windows_output = []
            st.rerun()
        st.subheader('Try these')
        st.code('cd\ndir\ncd Documents\ntype notes.txt\nwhoami\nhostname\nipconfig\nping 127.0.0.1')
    with tab3:
        bs = chr(92)
        st.code(
            'C:' + bs + '\n'
            '├── Users' + bs + '\n'
            '│   └── Student' + bs + '\n'
            '│       ├── Desktop' + bs + '\n'
            '│       ├── Documents' + bs + '\n'
            '│       ├── Downloads' + bs + '\n'
            '│       └── secret.txt\n'
            '├── Windows' + bs + '\n'
            '│   └── System32' + bs + '\n'
            '├── Program Files' + bs + '\n'
            '└── Temp'
        )

elif page == '🎯 Missions':
    st.title('🎯 Missions')
    selected = st.selectbox('Mission category', ['Linux', 'Windows'])
    for mission in [m for m in MISSIONS if m['os'] == selected]:
        done = mission['id'] in st.session_state.completed_missions
        with st.container(border=True):
            st.subheader(('✅ ' if done else '🎯 ') + mission['title'])
            st.write(mission['objective'])
            st.caption('Reward: +' + str(mission['xp']) + ' XP')
            if done:
                st.success('Mission completed.')
            else:
                if st.button('💡 Hint', key='hint_' + mission['id']): st.info(mission['hint'])
                answer = st.text_input('Command', key='answer_' + mission['id'])
                if st.button('✅ Submit', key='submit_' + mission['id']):
                    if answer.strip().lower() in [x.lower() for x in mission['answers']]:
                        st.session_state.completed_missions.append(mission['id'])
                        add_xp(mission['xp'])
                        check_achievements()
                        st.success('Correct! +' + str(mission['xp']) + ' XP')
                        st.rerun()
                    else:
                        st.error('Not quite. Try again or use the hint.')

elif page == '🧩 Quiz':
    st.title('🧩 Command Quiz')
    for quiz in QUIZZES:
        done = quiz['id'] in st.session_state.completed_quizzes
        with st.container(border=True):
            st.subheader(quiz['q'])
            if done:
                st.success('✅ Completed')
                continue
            answer = st.radio('Choose:', quiz['options'], key='quiz_' + quiz['id'])
            if st.button('Check Answer', key='check_' + quiz['id']):
                if answer == quiz['answer']:
                    st.session_state.completed_quizzes.append(quiz['id'])
                    add_xp(quiz['xp'])
                    check_achievements()
                    st.success('🎉 Correct! +' + str(quiz['xp']) + ' XP')
                    st.rerun()
                else:
                    st.error('❌ Incorrect. Try again.')

elif page == '🤖 AI Mentor':
    st.title('🤖 AI Mentor')
    st.write('Ask about Linux, Windows, filesystems, commands or beginner cybersecurity.')
    st.info('AI is optional. The labs work without a Groq key.')
    question = st.text_area('Ask your mentor', placeholder='Explain what cd .. does in Linux.')
    if st.button('🤖 Ask Mentor', type='primary'):
        if not question.strip(): st.warning('Enter a question first.')
        else:
            with st.spinner('Mentor is thinking...'):
                st.markdown(ask_ai(question))

elif page == '🏆 Achievements':
    st.title('🏆 Achievements')
    items = [
        ('first', '🥇 First Steps', 'Earn 50 XP.'),
        ('missions', '🎯 Mission Runner', 'Complete 3 missions.'),
        ('quiz', '🧠 Quiz Master', 'Complete 3 quizzes.'),
        ('beginner', '🛡️ Cyber Beginner', 'Reach 500 XP.'),
    ]
    for ident, title, description in items:
        if ident in st.session_state.achievements: st.success(title + ' — ' + description)
        else: st.write('🔒 ' + title + ' — ' + description)

st.divider()
st.caption('CyberStart Lab V2 • Educational simulated environment • No real system commands are executed.')
