import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Navigation from '../components/Navigation';
import { getTrees } from '../services/api';
import '../App.css';

function TreeListPage() {
  const [trees, setTrees] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadTrees();
  }, []);

  const loadTrees = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getTrees();
      setTrees(response.trees || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleDateString('uz-UZ');
    } catch {
      return dateString;
    }
  };

  return (
    <div>
      <Navigation />
      <div className="container">
        <div className="card">
          <h1>📋 Daraxtlar Ro'yxati</h1>
          
          <div className="button-group">
            <Link to="/register" className="btn">
              + Yangi Daraxt Qo'shish
            </Link>
            <button onClick={loadTrees} className="btn btn-secondary" disabled={loading}>
              {loading ? 'Yuklanmoqda...' : '🔄 Yangilash'}
            </button>
          </div>

          {loading && <div className="loading">Yuklanmoqda...</div>}
          
          {error && (
            <div className="result error">
              <h3>Xatolik</h3>
              <p>{error}</p>
            </div>
          )}

          {!loading && !error && trees.length === 0 && (
            <div className="result">
              <h3>Hozircha daraxtlar yo'q</h3>
              <p>Birinchi daraxtni qo'shing!</p>
              <Link to="/register" className="btn" style={{ marginTop: '1rem' }}>
                Daraxt Qo'shish
              </Link>
            </div>
          )}

          {!loading && trees.length > 0 && (
            <div className="grid">
              {trees.map((tree) => (
                <Link
                  key={tree.tree_id}
                  to={`/tree/${tree.tree_id}`}
                  className="tree-card"
                >
                  <h3>🌳 {tree.tree_type || tree.tree_species || 'Noma\'lum'}</h3>
                  <p><strong>ID:</strong> {tree.tree_id?.substring(0, 8)}...</p>
                  <p><strong>Ro'yxatga olingan:</strong> {formatDate(tree.registered_date)}</p>
                  {tree.location_address && (
                    <p><strong>📍 Manzil:</strong> {tree.location_address}</p>
                  )}
                  <div style={{ marginTop: '0.5rem', fontSize: '0.875rem' }}>
                    {tree.has_features && <span style={{ color: '#10b981' }}>✅ Feature'lar bor</span>}
                    {tree.status && <span style={{ marginLeft: '0.5rem', color: tree.status === 'active' ? '#10b981' : '#6b7280' }}>
                      {tree.status === 'active' ? '● Faol' : '○ ' + tree.status}
                    </span>}
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default TreeListPage;
