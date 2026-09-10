// frontend/src/pages/StatsPage.jsx

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { TreeDeciduous, Scan, TrendingUp, Database } from 'lucide-react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, 
  Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell 
} from 'recharts';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

function StatsPage() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    fetchStats();
  }, []);
  
  const fetchStats = async () => {
    try {
      setLoading(true);
      // Get stats from API
      const response = await axios.get(`${API_URL}/stats`);
      const statsData = response.data;
      
      // Ensure species_breakdown exists
      if (!statsData.species_breakdown || statsData.species_breakdown.length === 0) {
        statsData.species_breakdown = [];
        statsData.total_scans = statsData.total_scans || 0;
        statsData.average_scans_per_tree = statsData.average_scans_per_tree || 0;
      }
      
      setStats(statsData);
    } catch (error) {
      console.error('Error fetching stats:', error);
      // Set empty stats on error
      setStats({
        total_trees: 0,
        total_scans: 0,
        average_scans_per_tree: 0,
        species_breakdown: [],
        trees_by_type: {}
      });
    } finally {
      setLoading(false);
    }
  };
  
  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-green-600"></div>
      </div>
    );
  }
  
  if (!stats) {
    return (
      <div className="text-center text-gray-600">
        Ma'lumotlarni yuklab bo'lmadi
      </div>
    );
  }
  
  const COLORS = ['#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#ef4444', '#ec4899'];
  
  return (
    <div className="max-w-7xl mx-auto">
      
      <h1 className="text-4xl font-bold text-gray-900 mb-8 text-center">
        📊 Tizim Statistikasi
      </h1>
      
      {/* Overview Cards */}
      <div className="grid md:grid-cols-3 gap-6 mb-8">
        
        <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-2xl shadow-lg p-6 text-white">
          <TreeDeciduous className="w-10 h-10 mb-3 opacity-80" />
          <p className="text-sm opacity-90 mb-1">Jami Daraxtlar</p>
          <p className="text-4xl font-bold mb-2">{stats.total_trees}</p>
          <p className="text-xs opacity-80">Faol ro'yxatda</p>
        </div>
        
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl shadow-lg p-6 text-white">
          <Scan className="w-10 h-10 mb-3 opacity-80" />
          <p className="text-sm opacity-90 mb-1">Jami Scan'lar</p>
          <p className="text-4xl font-bold mb-2">{stats.total_scans}</p>
          <p className="text-xs opacity-80">Barcha vaqtda</p>
        </div>
        
        <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-2xl shadow-lg p-6 text-white">
          <TrendingUp className="w-10 h-10 mb-3 opacity-80" />
          <p className="text-sm opacity-90 mb-1">O'rtacha Scan</p>
          <p className="text-4xl font-bold mb-2">{stats.average_scans_per_tree}</p>
          <p className="text-xs opacity-80">Har bir daraxt uchun</p>
        </div>
        
      </div>
      
      {/* Species Breakdown */}
      <div className="grid md:grid-cols-2 gap-6">
        
        {/* Bar Chart */}
        <div className="bg-white rounded-2xl shadow-lg p-6">
          <h3 className="text-xl font-bold text-gray-900 mb-4">
            🌳 Daraxt Turlari (Top 10)
          </h3>
          
          {stats.species_breakdown.length > 0 ? (
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={stats.species_breakdown}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="species" angle={-45} textAnchor="end" height={100} />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="count" fill="#10b981" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-500 text-center py-20">
              Hali ma'lumot yo'q
            </p>
          )}
        </div>
        
        {/* Pie Chart */}
        <div className="bg-white rounded-2xl shadow-lg p-6">
          <h3 className="text-xl font-bold text-gray-900 mb-4">
            📈 Taqsimot
          </h3>
          
          {stats.species_breakdown.length > 0 ? (
            <ResponsiveContainer width="100%" height={400}>
              <PieChart>
                <Pie
                  data={stats.species_breakdown}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  outerRadius={120}
                  fill="#8884d8"
                  dataKey="count"
                >
                  {stats.species_breakdown.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <p className="text-gray-500 text-center py-20">
              Hali ma'lumot yo'q
            </p>
          )}
        </div>
        
      </div>
      
      {/* Species List */}
      <div className="bg-white rounded-2xl shadow-lg p-6 mt-6">
        <h3 className="text-xl font-bold text-gray-900 mb-4">
          📋 Batafsil Ro'yxat
        </h3>
        
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b-2 border-gray-200">
                <th className="text-left py-3 px-4 font-semibold text-gray-700">#</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-700">Daraxt Turi</th>
                <th className="text-right py-3 px-4 font-semibold text-gray-700">Soni</th>
                <th className="text-right py-3 px-4 font-semibold text-gray-700">Foiz</th>
              </tr>
            </thead>
            <tbody>
              {stats.species_breakdown.map((item, idx) => (
                <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-3 px-4 text-gray-600">{idx + 1}</td>
                  <td className="py-3 px-4 font-medium text-gray-900">
                    {item.species || 'Noma\'lum'}
                  </td>
                  <td className="py-3 px-4 text-right text-gray-700">
                    {item.count}
                  </td>
                  <td className="py-3 px-4 text-right text-gray-700">
                    {((item.count / stats.total_trees) * 100).toFixed(1)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      
    </div>
  );
}

export default StatsPage;