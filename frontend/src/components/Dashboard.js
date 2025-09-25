import React, {useState, useEffect} from 'react';
export default function Dashboard({token, user}){
  const [studentId, setStudentId] = useState('');
  const [attendance, setAttendance] = useState([]);
  const [marks, setMarks] = useState([]);
  async function fetchAttendance(sid){
    const res = await fetch(`http://localhost:8000/attendance/student/${sid}`, { headers: { Authorization: 'Bearer '+token }});
    if(res.ok){ setAttendance(await res.json()); } else { alert('Failed to fetch attendance'); }
  }
  async function fetchMarks(sid){
    const res = await fetch(`http://localhost:8000/marks/student/${sid}`, { headers: { Authorization: 'Bearer '+token }});
    if(res.ok){ setMarks(await res.json()); } else { alert('Failed to fetch marks'); }
  }
  return (
    <div>
      <div className='card'>
        <h3>Welcome, {user.username} ({user.role})</h3>
        <p>Use your numeric user id (from registration response) as student id to test student endpoints.</p>
      </div>

      <div className='card'>
        <h4>View Student Data</h4>
        <label>Student ID</label>
        <input value={studentId} onChange={e=>setStudentId(e.target.value)} />
        <button onClick={()=>{ fetchAttendance(studentId); fetchMarks(studentId); }}>Load</button>
        <h5>Attendance</h5>
        <pre>{JSON.stringify(attendance, null, 2)}</pre>
        <h5>Marks</h5>
        <pre>{JSON.stringify(marks, null, 2)}</pre>
      </div>

      {user.role === 'teacher' && (
        <div className='card'>
          <h4>Teacher Actions</h4>
          <MarkForm token={token} />
        </div>
      )}

      {user.role === 'admin' && (
        <div className='card'>
          <h4>Admin</h4>
          <p>Admin features are available via API directly for now.</p>
        </div>
      )}
    </div>
  );
}

function MarkForm({token}){
  const [sid, setSid] = useState('');
  const [status, setStatus] = useState('present');
  const [subject, setSubject] = useState('Math');
  const [marks, setMarks] = useState(80);
  async function mark(){
    const res = await fetch(`http://localhost:8000/attendance/mark?student_id=${sid}&status=${status}`, {
      method:'POST',
      headers:{ Authorization: 'Bearer '+token }
    });
    const d = await res.json();
    alert(JSON.stringify(d));
  }
  async function upload(){
    const res = await fetch(`http://localhost:8000/marks/upload?student_id=${sid}&subject=${encodeURIComponent(subject)}&marks=${marks}`, {
      method:'POST',
      headers:{ Authorization: 'Bearer '+token }
    });
    const d = await res.json();
    alert(JSON.stringify(d));
  }
  return (
    <div>
      <label>Student ID</label>
      <input value={sid} onChange={e=>setSid(e.target.value)} />
      <label>Status</label>
      <select value={status} onChange={e=>setStatus(e.target.value)}>
        <option value='present'>present</option>
        <option value='absent'>absent</option>
      </select>
      <button onClick={mark}>Mark Attendance</button>
      <hr />
      <label>Subject</label>
      <input value={subject} onChange={e=>setSubject(e.target.value)} />
      <label>Marks</label>
      <input type='number' value={marks} onChange={e=>setMarks(e.target.value)} />
      <button onClick={upload}>Upload Marks</button>
    </div>
  );
}
