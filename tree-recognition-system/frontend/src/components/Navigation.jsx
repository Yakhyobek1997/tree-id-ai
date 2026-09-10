import React from 'react';
import { Link } from 'react-router-dom';
import '../App.css';

function Navigation() {
  return (
    <nav>
      <ul>
        <li className="logo">🌳 Daraxt Tizimi</li>
        <li><Link to="/">Bosh Sahifa</Link></li>
        <li><Link to="/register">Qo'shish</Link></li>
        <li><Link to="/identify">Tanish</Link></li>
        <li><Link to="/trees">Ro'yxat</Link></li>
      </ul>
    </nav>
  );
}

export default Navigation;
