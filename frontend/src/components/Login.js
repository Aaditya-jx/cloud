import React, {useState} from 'react';
export default function Login({onAuth}){
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('student');
  const [mode, setMode] = useState('login'); // or register
  async function submit(e){
    e.preventDefault();
    if(mode==='register'){
      // register first
      const res = await fetch('http://localhost:8000/users/register', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({username, password, role, full_name: username})
      });
      const data = await res.json();
      alert(JSON.stringify(data));
      setMode('login');
      return;
    }
    // login
    const fd = new URLSearchParams();
    fd.append('username', username);
    fd.append('password', password);
    const res = await fetch('http://localhost:8000/token', {
      method:'POST',
      headers:{'Content-Type':'application/x-www-form-urlencoded'},
      body: fd.toString()
    });
    if(!res.ok){ alert('login failed'); return; }
    const data = await res.json();
    const token = data.access_token;
    // decode role from token (quick and dirty)
    const payload = JSON.parse(atob(token.split('.')[1]));
    onAuth(token, {username, role: payload.role});
  }
  return (
    <div className='card'>
      <h3>{mode==='login' ? 'Login' : 'Register'}</h3>
      <form onSubmit={submit}>
        <label>Username</label>
        <input value={username} onChange={e=>setUsername(e.target.value)} />
        <label>Password</label>
        <input type='password' value={password} onChange={e=>setPassword(e.target.value)} />
        {mode==='register' && <>
          <label>Role</label>
          <select value={role} onChange={e=>setRole(e.target.value)}>
            <option value='student'>Student</option>
            <option value='teacher'>Teacher</option>
            <option value='admin'>Admin</option>
          </select>
        </>}
        <button type='submit'>{mode==='login' ? 'Login' : 'Register'}</button>
      </form>
      <hr />
      <button onClick={()=>setMode(mode==='login'?'register':'login')}>{mode==='login' ? 'Create an account' : 'Back to login'}</button>
    </div>
  );
}
