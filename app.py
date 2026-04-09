from flask import Flask, request, jsonify, render_template_string
import sqlite3
from datetime import datetime, date
import os

app = Flask(__name__)
DB_PATH = "tasks.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            assigned_to TEXT NOT NULL,
            deadline TEXT NOT NULL,
            priority TEXT NOT NULL DEFAULT 'medium',
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def compute_status(row_status, deadline_str):
    if row_status == 'completed':
        return 'completed'
    try:
        dl = datetime.strptime(deadline_str, "%Y-%m-%d").date()
        if dl < date.today():
            return 'overdue'
    except:
        pass
    return 'pending'

HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ResultsHub — Team Task Manager</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f0f2f5; color: #2c2c2c; font-size: 14px; }

/* HEADER */
.header { background: #1e3a5f; color: white; padding: 14px 28px; display: flex; align-items: center; justify-content: space-between; box-shadow: 0 2px 6px rgba(0,0,0,0.2); }
.header h1 { font-size: 1.2rem; font-weight: 700; }
.header p  { font-size: 0.7rem; opacity: 0.6; margin-top: 2px; letter-spacing: 1px; text-transform: uppercase; }
.header-date { font-size: 0.78rem; opacity: 0.6; }

/* STATS */
.stats-bar { background: white; border-bottom: 1px solid #dde1e7; display: flex; }
.stat-box  { flex: 1; padding: 16px 20px; border-right: 1px solid #eee; text-align: center; }
.stat-box:last-child { border-right: none; }
.stat-num   { font-size: 1.7rem; font-weight: 700; line-height: 1; margin-bottom: 3px; }
.stat-label { font-size: 0.68rem; color: #888; text-transform: uppercase; letter-spacing: 0.8px; }
.s-blue   { color: #1e3a5f; }
.s-green  { color: #27a85f; }
.s-red    { color: #e05252; }
.s-orange { color: #e07f28; }

/* PROGRESS */
.progress-wrap  { background: white; padding: 12px 28px; border-bottom: 1px solid #dde1e7; display: flex; align-items: center; gap: 14px; }
.progress-label { font-size: 0.78rem; color: #666; white-space: nowrap; }
.progress-track { flex: 1; height: 10px; background: #e8eaed; border-radius: 10px; overflow: hidden; }
.progress-fill  { height: 100%; background: linear-gradient(90deg, #1e3a5f, #3a7bd5); border-radius: 10px; transition: width 0.4s; }
.progress-pct   { font-size: 0.85rem; font-weight: 700; color: #1e3a5f; white-space: nowrap; }

/* LAYOUT */
.page-body { display: flex; min-height: calc(100vh - 130px); }

/* SIDEBAR */
.sidebar { width: 290px; flex-shrink: 0; background: white; border-right: 1px solid #dde1e7; padding: 20px 18px; }
.section-title { font-size: 0.68rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: #888; margin-bottom: 12px; padding-bottom: 6px; border-bottom: 1px solid #eee; }

/* FORM */
.form-group { margin-bottom: 11px; }
.form-group label { display: block; font-size: 0.73rem; font-weight: 600; color: #555; margin-bottom: 4px; }
.form-group input, .form-group select { width: 100%; padding: 8px 10px; border: 1px solid #ccc; border-radius: 5px; font-size: 0.84rem; font-family: inherit; background: #fafafa; color: #2c2c2c; outline: none; transition: border-color 0.15s; }
.form-group input:focus, .form-group select:focus { border-color: #1e3a5f; background: white; }

.priority-group { display: flex; gap: 6px; }
.p-btn { flex: 1; padding: 7px 0; border: 1px solid #ccc; border-radius: 5px; cursor: pointer; font-size: 0.73rem; font-weight: 600; color: #888; background: white; text-align: center; transition: all 0.15s; font-family: inherit; }
.p-btn.sel-low    { border-color: #27a85f; background: #f0fdf4; color: #27a85f; }
.p-btn.sel-medium { border-color: #e07f28; background: #fff8f0; color: #e07f28; }
.p-btn.sel-high   { border-color: #e05252; background: #fff5f5; color: #e05252; }

.btn-submit { width: 100%; padding: 10px; background: #1e3a5f; color: white; border: none; border-radius: 5px; font-size: 0.88rem; font-weight: 600; cursor: pointer; margin-top: 6px; font-family: inherit; transition: background 0.15s; }
.btn-submit:hover { background: #2a5490; }

/* MEMBERS */
.member-list { margin-top: 22px; }
.member-item { display: flex; align-items: center; gap: 9px; padding: 7px 0; border-bottom: 1px solid #f2f2f2; font-size: 0.82rem; }
.member-item:last-child { border-bottom: none; }
.avatar { width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.65rem; font-weight: 700; color: white; flex-shrink: 0; }
.m-name  { font-weight: 600; color: #333; font-size: 0.82rem; }
.m-count { font-size: 0.7rem; color: #999; }
.m-info  { flex: 1; }
.btn-remove-member { margin-left: auto; background: none; border: 1px solid #f5bcbc; border-radius: 4px; color: #e05252; font-size: 0.7rem; cursor: pointer; padding: 2px 7px; font-family: inherit; transition: all 0.15s; flex-shrink: 0; }
.btn-remove-member:hover { background: #fff5f5; }

.add-member-row { display: flex; gap: 6px; margin-top: 10px; }
.add-member-row input { flex: 1; padding: 7px 10px; border: 1px solid #ccc; border-radius: 5px; font-size: 0.82rem; font-family: inherit; outline: none; }
.add-member-row input:focus { border-color: #1e3a5f; }
.btn-sm { padding: 7px 12px; background: #1e3a5f; color: white; border: none; border-radius: 5px; font-size: 0.78rem; cursor: pointer; font-family: inherit; white-space: nowrap; }

/* MAIN */
.main-content { flex: 1; padding: 20px 24px; }

/* FILTER TABS */
.filter-tabs { display: flex; gap: 6px; margin-bottom: 14px; flex-wrap: wrap; }
.ftab { padding: 5px 13px; border: 1px solid #ccc; border-radius: 4px; font-size: 0.76rem; font-weight: 600; color: #555; background: white; cursor: pointer; font-family: inherit; transition: all 0.15s; }
.ftab:hover { border-color: #1e3a5f; color: #1e3a5f; }
.ftab.active { background: #1e3a5f; color: white; border-color: #1e3a5f; }

/* ALERT */
.alert { padding: 9px 14px; border-radius: 5px; font-size: 0.82rem; font-weight: 600; margin-bottom: 12px; display: none; }
.alert.show { display: block; }
.alert-success { background: #e8f9ef; color: #27a85f; border: 1px solid #b7e8cb; }
.alert-error   { background: #feecec; color: #e05252; border: 1px solid #f5bcbc; }

.task-info { font-size: 0.75rem; color: #888; margin-bottom: 8px; }

/* TABLE */
.task-table { width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,0.08); }
.task-table thead tr { background: #f5f7fa; border-bottom: 2px solid #e0e4ea; }
.task-table th { padding: 11px 14px; text-align: left; font-size: 0.68rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.8px; color: #666; }
.task-table tbody tr { border-bottom: 1px solid #f0f2f5; transition: background 0.1s; }
.task-table tbody tr:last-child { border-bottom: none; }
.task-table tbody tr:hover { background: #fafbfc; }
.task-table td { padding: 11px 14px; vertical-align: middle; }

.task-title      { font-weight: 600; font-size: 0.88rem; color: #222; }
.task-title.done { text-decoration: line-through; color: #bbb; }

.badge { display: inline-block; padding: 2px 8px; border-radius: 3px; font-size: 0.68rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.4px; }
.b-low       { background: #e8f9ef; color: #27a85f; }
.b-medium    { background: #fff4e6; color: #e07f28; }
.b-high      { background: #feecec; color: #e05252; }
.b-pending   { background: #eef2ff; color: #4a6cf7; }
.b-completed { background: #e8f9ef; color: #27a85f; }

.act-btn { padding: 4px 9px; border: 1px solid #ccc; border-radius: 4px; font-size: 0.72rem; font-weight: 600; cursor: pointer; background: white; font-family: inherit; transition: all 0.15s; margin-right: 3px; color: #444; }
.act-btn.done-btn { border-color: #27a85f; color: #27a85f; }
.act-btn.done-btn:hover { background: #f0fdf4; }
.act-btn.open-btn { border-color: #e07f28; color: #e07f28; }
.act-btn.open-btn:hover { background: #fff8f0; }
.act-btn.del-btn  { border-color: #e05252; color: #e05252; }
.act-btn.del-btn:hover  { background: #fff5f5; }

.dl-cell        { font-size: 0.8rem; color: #666; }
.dl-cell.overdue{ color: #e05252; font-weight: 600; }

.empty-state { text-align: center; padding: 50px 20px; color: #bbb; background: white; border-radius: 8px; box-shadow: 0 1px 4px rgba(0,0,0,0.06); }
.empty-state h3 { font-size: 1rem; margin-bottom: 6px; }
.empty-state p  { font-size: 0.82rem; }

@media (max-width: 768px) {
    .page-body { flex-direction: column; }
    .sidebar   { width: 100%; border-right: none; border-bottom: 1px solid #dde1e7; }
    .stats-bar { flex-wrap: wrap; }
    .stat-box  { min-width: 50%; }
}
</style>
</head>
<body>

<div class="header">
    <div>
        <h1>ResultsHub</h1>
        <p>Team Task Manager</p>
    </div>
    <div class="header-date" id="dateDisplay"></div>
</div>

<div class="stats-bar">
    <div class="stat-box"><div class="stat-num s-blue"  id="sTotal">0</div><div class="stat-label">Total Tasks</div></div>
    <div class="stat-box"><div class="stat-num s-green" id="sDone">0</div><div class="stat-label">Completed</div></div>
    <div class="stat-box"><div class="stat-num s-red"   id="sPending">0</div><div class="stat-label">Pending</div></div>
    <div class="stat-box"><div class="stat-num s-orange" id="sPct">0%</div><div class="stat-label">Progress</div></div>
</div>

<div class="progress-wrap">
    <span class="progress-label">Team Progress</span>
    <div class="progress-track"><div class="progress-fill" id="progBar" style="width:0%"></div></div>
    <span class="progress-pct" id="progText">0 / 0 done</span>
</div>

<div class="page-body">

    <div class="sidebar">
        <div class="section-title">➕ Add New Task</div>
        <div class="alert" id="alertBox"></div>

        <div class="form-group">
            <label>Task Title *</label>
            <input type="text" id="taskTitle" placeholder="Enter task title..." />
        </div>
        <div class="form-group">
            <label>Assign To</label>
            <select id="taskMember"><option value="">— Select member —</option></select>
        </div>
        <div class="form-group">
            <label>Deadline</label>
            <input type="date" id="taskDeadline" />
        </div>
        <div class="form-group">
            <label>Priority</label>
            <div class="priority-group">
                <button class="p-btn sel-low" onclick="setPri('low',this)">🟢 Low</button>
                <button class="p-btn"         onclick="setPri('medium',this)">🟡 Med</button>
                <button class="p-btn"         onclick="setPri('high',this)">🔴 High</button>
            </div>
        </div>
        <button class="btn-submit" onclick="addTask()">+ Add Task</button>

        <div class="member-list">
            <div class="section-title" style="margin-top:22px">👥 Team Members</div>
            <div id="membersList"></div>
            <div class="add-member-row">
                <input type="text" id="newMemberInput" placeholder="Add member name..." />
                <button class="btn-sm" onclick="addMember()">Add</button>
            </div>
        </div>
    </div>

    <div class="main-content">
        <div class="filter-tabs">
            <button class="ftab active" onclick="setFilter('all',this)">All Tasks</button>
            <button class="ftab" onclick="setFilter('pending',this)">⏳ Pending</button>
            <button class="ftab" onclick="setFilter('completed',this)">✅ Completed</button>
            <button class="ftab" onclick="setFilter('high',this)">🔴 High</button>
            <button class="ftab" onclick="setFilter('medium',this)">🟡 Medium</button>
            <button class="ftab" onclick="setFilter('low',this)">🟢 Low</button>
        </div>
        <div class="task-info" id="taskInfo"></div>
        <div id="taskArea"></div>
    </div>
</div>

<script>
let tasks = [];
let members = ['Devi R','Divya Sri','Jasvin G','Jayanthi M','Rathisha A'];
let selPriority = 'low';
let currentFilter = 'all';
let taskId = 1;
const avatarColors = ['#1e3a5f','#27a85f','#e05252','#e07f28','#6a5acd','#2196f3'];

window.onload = function() {
    const d = new Date();
    document.getElementById('dateDisplay').textContent =
        d.toLocaleDateString('en-IN', {day:'2-digit',month:'short',year:'numeric',weekday:'short'});


    render(); 
};
function setPri(p, el) {
    selPriority = p;
    document.querySelectorAll('.p-btn').forEach(b => b.classList.remove('sel-low','sel-medium','sel-high'));
    el.classList.add('sel-' + p);
}

function addTask() {
    const title = document.getElementById('taskTitle').value.trim();
    if (!title) { showAlert('error','⚠️ Task title cannot be empty!'); return; }
    tasks.unshift({
        id: taskId++, title,
        member:   document.getElementById('taskMember').value,
        deadline: document.getElementById('taskDeadline').value,
        priority: selPriority,
        status:   'pending'
    });
    document.getElementById('taskTitle').value = '';
    document.getElementById('taskMember').value = '';
    document.getElementById('taskDeadline').value = '';
    setPri('low', document.querySelectorAll('.p-btn')[0]);
    render();
    showAlert('success','✅ Task added successfully!');
}

function toggleTask(id) {
    const t = tasks.find(x => x.id === id);
    if (t) { t.status = t.status === 'pending' ? 'completed' : 'pending'; render(); }
}

function deleteTask(id) {
    if (!confirm('Delete this task?')) return;
    tasks = tasks.filter(x => x.id !== id);
    render();
}

function setFilter(f, el) {
    currentFilter = f;
    document.querySelectorAll('.ftab').forEach(b => b.classList.remove('active'));
    el.classList.add('active');
    render();
}

function getFiltered() {
    if (currentFilter === 'all')       return tasks;
    if (currentFilter === 'pending')   return tasks.filter(t => t.status === 'pending');
    if (currentFilter === 'completed') return tasks.filter(t => t.status === 'completed');
    return tasks.filter(t => t.priority === currentFilter);
}

function addMember() {
    const name = document.getElementById('newMemberInput').value.trim();
    if (!name || members.includes(name)) return;
    members.push(name);
    document.getElementById('newMemberInput').value = '';
    render();
}

function removeMember(name) {
    if (!confirm('Remove "' + name + '" from the team?\n(Their assigned tasks will become unassigned)')) return;
    members = members.filter(m => m !== name);
    tasks.forEach(t => { if (t.member === name) t.member = ''; });
    render();
    showAlert('success', '🗑️ ' + name + ' removed from team!');
}

function fmtDate(d) {
    if (!d) return '—';
    const [y,m,day] = d.split('-');
    return day + ' ' + ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][parseInt(m)-1] + ' ' + y;
}
function isOverdue(d) { return d && new Date(d) < new Date(new Date().toDateString()); }
function esc(s) { return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
function cap(s) { return s.charAt(0).toUpperCase() + s.slice(1); }

function render() {
    // Stats
    const total = tasks.length, done = tasks.filter(t => t.status==='completed').length;
    const pct = total > 0 ? Math.round(done/total*100) : 0;
    document.getElementById('sTotal').textContent   = total;
    document.getElementById('sDone').textContent    = done;
    document.getElementById('sPending').textContent = total - done;
    document.getElementById('sPct').textContent     = pct + '%';
    document.getElementById('progBar').style.width  = pct + '%';
    document.getElementById('progText').textContent = done + ' / ' + total + ' done';

    // Members
    document.getElementById('membersList').innerHTML = members.map((name, i) => {
        const init  = name.split(' ').map(w=>w[0]).join('').toUpperCase().slice(0,2);
        const color = avatarColors[i % avatarColors.length];
        const mc = tasks.filter(t=>t.member===name).length;
        const md = tasks.filter(t=>t.member===name && t.status==='completed').length;
        return `<div class="member-item">
            <div class="avatar" style="background:${color}">${init}</div>
            <div class="m-info"><div class="m-name">${name}</div><div class="m-count">${md}/${mc} tasks done</div></div>
            <button class="btn-remove-member" onclick="removeMember('${name}')">✕ Remove</button>
        </div>`;
    }).join('');

    // Select options
    const sel = document.getElementById('taskMember');
    const cur = sel.value;
    sel.innerHTML = '<option value="">— Select member —</option>' +
        members.map(m=>`<option value="${m}"${m===cur?' selected':''}>${m}</option>`).join('');

    // Tasks
    const filtered = getFiltered();
    document.getElementById('taskInfo').innerHTML =
        'Showing <strong>' + filtered.length + '</strong> task' + (filtered.length!==1?'s':'') +
        (currentFilter!=='all' ? ' — filtered by <strong>' + currentFilter + '</strong>' : '');

    if (filtered.length === 0) {
        document.getElementById('taskArea').innerHTML =
            `<div class="empty-state"><h3>No tasks found</h3><p>Add a task using the form on the left.</p></div>`;
        return;
    }

    const rows = filtered.map((t, i) => {
        const isDone   = t.status === 'completed';
        const overdue  = !isDone && isOverdue(t.deadline);
        return `<tr>
            <td style="color:#bbb;font-size:0.72rem">${i+1}</td>
            <td><div class="task-title ${isDone?'done':''}">${esc(t.title)}</div></td>
            <td style="font-size:0.82rem;color:#444">${t.member||'<span style="color:#ccc">—</span>'}</td>
            <td><span class="dl-cell ${overdue?'overdue':''}">${fmtDate(t.deadline)}${overdue?' ⚠':''}</span></td>
            <td><span class="badge b-${t.priority}">${cap(t.priority)}</span></td>
            <td><span class="badge ${isDone?'b-completed':'b-pending'}">${isDone?'Done':'Pending'}</span></td>
            <td>
                ${isDone
                    ? `<button class="act-btn open-btn" onclick="toggleTask(${t.id})">↩ Reopen</button>`
                    : `<button class="act-btn done-btn" onclick="toggleTask(${t.id})">✓ Done</button>`}
                <button class="act-btn del-btn" onclick="deleteTask(${t.id})">✕ Del</button>
            </td>
        </tr>`;
    }).join('');

    document.getElementById('taskArea').innerHTML = `
    <table class="task-table">
        <thead><tr>
            <th>#</th><th>Task Title</th><th>Assigned To</th>
            <th>Deadline</th><th>Priority</th><th>Status</th><th>Actions</th>
        </tr></thead>
        <tbody>${rows}</tbody>
    </table>`;
}

function showAlert(type, msg) {
    const el = document.getElementById('alertBox');
    el.className = 'alert alert-' + type + ' show';
    el.textContent = msg;
    setTimeout(() => el.classList.remove('show'), 3000);
}
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/api/tasks", methods=["GET"])
def get_tasks():
    conn = get_db()
    rows = conn.execute("SELECT * FROM tasks").fetchall()
    conn.close()

    tasks=[]
    for r in rows:
        d=dict(r)
        d["status"]=compute_status(d["status"],d["deadline"])
        tasks.append(d)

    return jsonify(tasks)

@app.route("/api/tasks", methods=["POST"])
def add_task():
    data=request.get_json()

    conn=get_db()
    conn.execute(
        "INSERT INTO tasks (title,assigned_to,deadline,priority,status,created_at) VALUES (?,?,?,?, 'pending',?)",
        (data["title"],data["assigned_to"],data["deadline"],data["priority"],datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

    return jsonify({"ok":True})

if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)