import React, { useState } from 'react';
import { Button, TextField } from '@mui/material';
import api from '../services/api';

export default function Login() {
  const [username, setUsername] = useState<string>('');
  const [password, setPassword] = useState<string>('');

  const handleLogin = async () => {
    try {
      const res = await api.post('/auth/login/', { username, password });
      console.log('Login success:', res.data);
    } catch (err) {
      console.error('Login failed:', err);
    }
  };

  return (
    <div>
      <h2>Login Page</h2>
      <TextField 
        label="Username" 
        value={username}
        onChange={(e) => setUsername(e.target.value)} 
      />
      <br />
      <TextField 
        label="Password" 
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)} 
      />
      <br /><br />
      <Button variant="contained" onClick={handleLogin}>
        Login
      </Button>
    </div>
  );
}
