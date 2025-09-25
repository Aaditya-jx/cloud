import React, {useState} from 'react';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
export default function App(){
  const [token, setToken] = useState(null);
  const [user, setUser] = useState(null);
  if(!token){
    return <Login onAuth={(t,u)=>{setToken(t); setUser(u);}} />
  }
  return <Dashboard token={token} user={user} />
}
