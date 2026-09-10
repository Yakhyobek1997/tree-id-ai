import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Navbar from './components/Navbar';
import HomePage from './pages/HomePage';
import ScanPage from './pages/AnalysisPage';
import TreeDetailPage from './pages/TreeDetailPage';
import TreeListPage from './pages/TreeListPage';
import TreeRegisterPage from './pages/TreeRegisterPage';
import TreeIdentifyPage from './pages/TreeIdentifyPage';
import StatsPage from './pages/StatsPage';
export default function App(){return <Router><div className="app-root"><Navbar/><main><Routes><Route path="/" element={<HomePage/>}/><Route path="/scan" element={<ScanPage/>}/><Route path="/register" element={<TreeRegisterPage/>}/><Route path="/identify" element={<TreeIdentifyPage/>}/><Route path="/trees" element={<TreeListPage/>}/><Route path="/tree/:treeId" element={<TreeDetailPage/>}/><Route path="/stats" element={<StatsPage/>}/></Routes></main><Toaster position="top-right"/></div></Router>}
