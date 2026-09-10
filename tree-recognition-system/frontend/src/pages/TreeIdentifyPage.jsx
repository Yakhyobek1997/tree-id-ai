import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Navigation from '../components/Navigation';
import ImageUploader from '../components/ImageUploader';
import { identifyTree } from '../services/api';
import '../App.css';

function TreeIdentifyPage() {
  const navigate = useNavigate();
  const [image, setImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleImageChange = (file) => {
    setImage(file);
    setResult(null);
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleIdentify = async () => {
    if (!image) {
      alert('Iltimos, rasm tanlang!');
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append('image', image);

      const response = await identifyTree(formData);
      setResult(response);
    } catch (error) {
      setResult({
        error: true,
        message: error.response?.data?.message || error.message || 'Xatolik yuz berdi'
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <Navigation />
      <div className="container">
        <div className="card">
          <h1>🔍 Daraxtni Tanish</h1>
          
          <ImageUploader
            onImageChange={handleImageChange}
            imagePreview={imagePreview}
            disabled={loading}
          />

          <div className="button-group">
            <button
              onClick={handleIdentify}
              disabled={loading || !image}
              className="btn btn-success"
            >
              {loading ? 'Tekshirilmoqda...' : '🔍 Daraxtni Tanish'}
            </button>
          </div>

          {loading && <div className="loading">Rasm tahlil qilinmoqda...</div>}

          {result && (
            <div className={`result ${result.error ? 'error' : result.found ? 'success' : 'warning'}`}>
              
              {/* Found - Daraxt bazada bor */}
              {result.found && result.success && (
                <>
                  <h3>✅ {result.message || 'Daraxt topildi!'}</h3>
                  <div style={{
                    background: 'linear-gradient(135deg, #f0fff4 0%, #d1fae5 100%)',
                    borderLeft: '4px solid #10b981',
                    padding: '1rem',
                    marginTop: '1rem',
                    borderRadius: '8px'
                  }}>
                    <p style={{ color: '#065f46', fontWeight: '600', marginBottom: '0.5rem' }}>
                      🎉 Bu daraxt allaqachon ro'yxatga olingan!
                    </p>
                    <p><strong>Daraxt ID:</strong> {result.tree_id}</p>
                    {result.tree_type && <p><strong>Tur:</strong> {result.tree_type}</p>}
                    {result.similarity && (
                      <p><strong>O'xshashlik:</strong> {(result.similarity * 100).toFixed(1)}%</p>
                    )}
                    {result.confidence && (
                      <p><strong>Ishonch:</strong> {
                        result.confidence === 'high' ? 'Yuqori' : 
                        result.confidence === 'medium' ? 'O\'rtacha' : 
                        result.confidence === 'low' ? 'Past' : result.confidence
                      }</p>
                    )}
                  </div>
                  
                  <div className="button-group" style={{ marginTop: '1rem' }}>
                    <button
                      onClick={() => navigate(`/tree/${result.tree_id}`)}
                      className="btn"
                    >
                      📋 Batafsil Ma'lumot
                    </button>
                  </div>
                </>
              )}
              
              {/* Not Found - Daraxt bazada yo'q */}
              {!result.found && result.success && (
                <>
                  <h3>❌ {result.message || 'Daraxt topilmadi'}</h3>
                  <div style={{
                    background: 'linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%)',
                    borderLeft: '4px solid #f59e0b',
                    padding: '1rem',
                    marginTop: '1rem',
                    borderRadius: '8px'
                  }}>
                    <p style={{ color: '#92400e', fontWeight: '600', marginBottom: '0.5rem' }}>
                      🌱 Bu daraxt bazada yo'q
                    </p>
                    <p style={{ color: '#b45309', marginBottom: '0.75rem' }}>
                      Bu yangi daraxt bo'lishi mumkin. Agar siz bu daraxtni ro'yxatga olmoqchi bo'lsangiz, 
                      quyidagi tugmani bosing.
                    </p>
                    {result.similarity && (
                      <p style={{ fontSize: '0.875rem', color: '#d97706' }}>
                        Eng yaqin o'xshashlik: {(result.similarity * 100).toFixed(1)}% 
                        (Threshold: 75%)
                      </p>
                    )}
                  </div>
                  
                  <div className="button-group" style={{ marginTop: '1rem' }}>
                    <button
                      onClick={() => navigate('/register')}
                      className="btn"
                    >
                      ➕ Daraxtni Ro'yxatga Olish
                    </button>
                  </div>
                </>
              )}
              
              {/* Error */}
              {result.error && (
                <>
                  <h3>❌ Xatolik</h3>
                  <p>{result.message}</p>
                </>
              )}
              
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default TreeIdentifyPage;
