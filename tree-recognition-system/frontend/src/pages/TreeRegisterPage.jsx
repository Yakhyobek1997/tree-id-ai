import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Navigation from '../components/Navigation';
import ImageUploader from '../components/ImageUploader';
import { registerTree } from '../services/api';
import '../App.css';

function TreeRegisterPage() {
  const [image, setImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [treeType, setTreeType] = useState('');
  const [locationLat, setLocationLat] = useState('');
  const [locationLng, setLocationLng] = useState('');
  const [locationAddress, setLocationAddress] = useState('');
  const navigate = useNavigate();

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

  const handleRegister = async () => {
    if (!image) {
      alert('Iltimos, rasm tanlang!');
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append('image', image);
      if (treeType) formData.append('tree_type', treeType);
      if (locationLat) formData.append('location_lat', locationLat);
      if (locationLng) formData.append('location_lng', locationLng);
      if (locationAddress) formData.append('location_address', locationAddress);

      const response = await registerTree(formData);
      setResult(response);

      // If tree already exists, show message and redirect
      if (response.status === 'exists') {
        setTimeout(() => {
          navigate(`/tree/${response.tree_id}`);
        }, 3000);
      } else if (response.status === 'registered' || response.success) {
        // Success - redirect to tree detail
        setTimeout(() => {
          navigate(`/tree/${response.tree_id}`);
        }, 2000);
      }
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
          <h1>📝 Yangi Daraxt Qo'shish</h1>
          
          <ImageUploader
            onImageChange={handleImageChange}
            imagePreview={imagePreview}
            disabled={loading}
          />

          <div className="form-group">
            <label>Daraxt Turi (ixtiyoriy)</label>
            <input
              type="text"
              placeholder="Masalan: Qayrag'och, Terak, etc."
              value={treeType}
              onChange={(e) => setTreeType(e.target.value)}
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label>Manzil (ixtiyoriy)</label>
            <input
              type="text"
              placeholder="Manzil"
              value={locationAddress}
              onChange={(e) => setLocationAddress(e.target.value)}
              disabled={loading}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="form-group">
              <label>Kenglik (Latitude)</label>
              <input
                type="number"
                step="any"
                placeholder="41.3111"
                value={locationLat}
                onChange={(e) => setLocationLat(e.target.value)}
                disabled={loading}
              />
            </div>
            <div className="form-group">
              <label>Uzunlik (Longitude)</label>
              <input
                type="number"
                step="any"
                placeholder="69.2797"
                value={locationLng}
                onChange={(e) => setLocationLng(e.target.value)}
                disabled={loading}
              />
            </div>
          </div>

          <div className="button-group">
            <button
              onClick={handleRegister}
              disabled={loading || !image}
              className="btn"
            >
              {loading ? 'Yuklanmoqda...' : '📝 Daraxtni Ro\'yxatga Olish'}
            </button>
          </div>

          {result && (
            <div className={`result ${result.error ? 'error' : result.status === 'exists' ? 'warning' : 'success'}`}>
              <h3>{result.message}</h3>
              {result.tree_id && (
                <p><strong>Daraxt ID:</strong> {result.tree_id}</p>
              )}
              {result.tree_type && (
                <p><strong>Tur:</strong> {result.tree_type}</p>
              )}
              {result.similarity && (
                <p><strong>O'xshashlik:</strong> {(result.similarity * 100).toFixed(1)}%</p>
              )}
              {result.status === 'exists' && (
                <p className="text-sm mt-2">⚠️ Daraxt sahifasiga yo'naltirilmoqda...</p>
              )}
              {(result.status === 'registered' || result.success) && (
                <p className="text-sm mt-2">✅ Daraxt sahifasiga yo'naltirilmoqda...</p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default TreeRegisterPage;
