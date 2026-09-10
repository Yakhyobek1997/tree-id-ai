// frontend/src/pages/TreeDetailPage.jsx

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { 
  ArrowLeft, Calendar, MapPin, Tag, Database, AlertCircle
} from 'lucide-react';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000/api';

function TreeDetailPage() {
  const { treeId } = useParams();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [treeData, setTreeData] = useState(null);
  const [error, setError] = useState(null);
  
  useEffect(() => {
    fetchTreeData();
  }, [treeId]);
  
  const fetchTreeData = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_URL}/trees/${treeId}?include_observations=true`);
      setTreeData(response.data);
      setError(null);
    } catch (err) {
      console.error('Error fetching tree data:', err);
      setError(err.response?.data?.message || 'Daraxt ma\'lumotlarini yuklab bo\'lmadi');
    } finally {
      setLoading(false);
    }
  };
  
  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-green-600"></div>
        <p className="ml-4 text-gray-600">Yuklanmoqda...</p>
      </div>
    );
  }
  
  if (error || !treeData) {
    return (
      <div className="max-w-2xl mx-auto text-center">
        <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Xatolik</h2>
        <p className="text-gray-600 mb-4">{error}</p>
        <button
          onClick={() => navigate('/')}
          className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 transition"
        >
          Asosiy sahifaga qaytish
        </button>
      </div>
    );
  }
  
  const observations = treeData.observations || [];
  
  return (
    <div className="max-w-5xl mx-auto">
      
      {/* Header */}
      <div className="mb-8">
        <button
          onClick={() => navigate(-1)}
          className="flex items-center text-gray-600 hover:text-gray-900 mb-4 transition"
        >
          <ArrowLeft className="w-5 h-5 mr-2" />
          Orqaga
        </button>
        
        <div className="bg-white rounded-2xl shadow-lg p-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-6">
            🌳 Daraxt Ma'lumotlari
          </h1>
          
          <div className="grid md:grid-cols-2 gap-6">
            
            {/* Tree ID */}
            <div className="bg-gray-50 rounded-xl p-4">
              <div className="flex items-center mb-2">
                <Database className="w-5 h-5 text-gray-600 mr-2" />
                <span className="text-sm text-gray-600 font-semibold">Daraxt ID</span>
              </div>
              <p className="text-lg font-mono text-gray-900">{treeData.tree_id}</p>
            </div>
            
            {/* Tree Type */}
            <div className="bg-gray-50 rounded-xl p-4">
              <div className="flex items-center mb-2">
                <Tag className="w-5 h-5 text-gray-600 mr-2" />
                <span className="text-sm text-gray-600 font-semibold">Daraxt Turi</span>
              </div>
              <p className="text-lg font-medium text-gray-900">
                {treeData.tree_type || treeData.tree_species || 'Noma\'lum'}
              </p>
            </div>
            
            {/* Registration Date */}
            {treeData.registered_date && (
              <div className="bg-gray-50 rounded-xl p-4">
                <div className="flex items-center mb-2">
                  <Calendar className="w-5 h-5 text-gray-600 mr-2" />
                  <span className="text-sm text-gray-600 font-semibold">Ro'yxatga Olingan</span>
                </div>
                <p className="text-lg text-gray-900">
                  {new Date(treeData.registered_date).toLocaleDateString('uz-UZ', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                  })}
                </p>
              </div>
            )}
            
            {/* Location */}
            {(treeData.location_address || (treeData.location_lat && treeData.location_lng)) && (
              <div className="bg-gray-50 rounded-xl p-4">
                <div className="flex items-center mb-2">
                  <MapPin className="w-5 h-5 text-gray-600 mr-2" />
                  <span className="text-sm text-gray-600 font-semibold">Joylashuv</span>
                </div>
                {treeData.location_address && (
                  <p className="text-lg text-gray-900 mb-1">{treeData.location_address}</p>
                )}
                {treeData.location_lat && treeData.location_lng && (
                  <p className="text-sm text-gray-600 font-mono">
                    {treeData.location_lat.toFixed(6)}, {treeData.location_lng.toFixed(6)}
                  </p>
                )}
              </div>
            )}
            
          </div>
          
          {/* Status */}
          <div className="mt-6 pt-6 border-t border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">Holat</p>
                <div className="flex items-center">
                  <span className={`inline-block w-3 h-3 rounded-full mr-2 ${
                    treeData.status === 'active' ? 'bg-green-500' : 'bg-gray-400'
                  }`}></span>
                  <span className="font-medium text-gray-900 capitalize">
                    {treeData.status === 'active' ? 'Faol' : treeData.status || 'Noma\'lum'}
                  </span>
                </div>
              </div>
              
              {treeData.has_features && (
                <div className="text-right">
                  <p className="text-sm text-gray-600 mb-1">Feature'lar</p>
                  <span className="text-green-600 font-medium">✓ Mavjud</span>
                </div>
              )}
            </div>
          </div>
          
        </div>
      </div>
      
      {/* Observations Section */}
      {observations && observations.length > 0 && (
        <div className="bg-white rounded-2xl shadow-lg p-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">
            📊 Kuzatuvlar Tarixi
          </h2>
          
          <div className="space-y-4">
            {observations.map((obs, index) => (
              <div key={index} className="bg-gray-50 rounded-xl p-4 border-l-4 border-green-500">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <p className="text-sm text-gray-600 mb-2">
                      📅 {new Date(obs.observation_date).toLocaleDateString('uz-UZ', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </p>
                    
                    {obs.health_status && (
                      <p className="text-gray-900 mb-1">
                        <span className="font-semibold">Salomatlik:</span> {obs.health_status}
                      </p>
                    )}
                    
                    {obs.growth_stage && (
                      <p className="text-gray-900 mb-1">
                        <span className="font-semibold">O'sish Bosqichi:</span> {obs.growth_stage}
                      </p>
                    )}
                    
                    {obs.notes && (
                      <p className="text-gray-700 mt-2 italic">"{obs.notes}"</p>
                    )}
                  </div>
                  
                  {obs.image_path && (
                    <span className="ml-4 text-sm text-gray-500">🖼️ Rasm</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* No Observations */}
      {(!observations || observations.length === 0) && (
        <div className="bg-white rounded-2xl shadow-lg p-8 text-center">
          <p className="text-gray-600">📊 Hali kuzatuvlar yo'q</p>
          <p className="text-sm text-gray-500 mt-2">
            Bu daraxt uchun kuzatuvlar qo'shilganda bu yerda ko'rinadi
          </p>
        </div>
      )}
      
      {/* Metadata */}
      {treeData.metadata && Object.keys(treeData.metadata).length > 0 && (
        <div className="bg-white rounded-2xl shadow-lg p-8 mt-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">
            ℹ️ Qo'shimcha Ma'lumotlar
          </h2>
          
          <div className="bg-gray-50 rounded-xl p-4">
            <pre className="text-sm text-gray-700 overflow-auto">
              {JSON.stringify(treeData.metadata, null, 2)}
            </pre>
          </div>
        </div>
      )}
      
    </div>
  );
}

export default TreeDetailPage;
