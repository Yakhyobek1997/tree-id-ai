import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Camera, Upload, Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';
import { identifyTree } from '../services/api';
import ImageUploader from '../components/ImageUploader';

function ScanPage() {
  const [image, setImage] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const navigate = useNavigate();

  const handleImageSelect = (file) => {
    if (file) {
      setImage(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreview(reader.result);
      };
      reader.readAsDataURL(file);
      setResult(null);
    }
  };

  const handleScan = async () => {
    if (!image) {
      toast.error('Iltimos, rasm tanlang');
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append('image', image);

      const response = await identifyTree(formData);
      
      if (response.success) {
        setResult(response);
        
        if (response.tree_id) {
          toast.success(`Daraxt topildi! ID: ${response.tree_id}`);
          // Navigate to tree detail page after a short delay
          setTimeout(() => {
            navigate(`/tree/${response.tree_id}`);
          }, 2000);
        } else if (response.similar_trees && response.similar_trees.length > 0) {
          toast.success(`${response.similar_trees.length} ta o'xshash daraxt topildi`);
        } else {
          toast.success('Yangi daraxt topildi!');
        }
      } else {
        toast.error(response.message || 'Tanishishda xatolik yuz berdi');
      }
    } catch (error) {
      console.error('Scan error:', error);
      const errorMsg = error.response?.data?.message || error.message || 'Server bilan bog\'lanishda xatolik';
      toast.error(errorMsg);
      console.error('Full error:', error.response?.data || error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-2xl shadow-xl p-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center gap-2">
          <Camera className="w-8 h-8 text-green-600" />
          Daraxtni Scan Qilish
        </h1>
        <p className="text-gray-600 mb-6">
          Rasm yuklang va AI daraxtni taniydi
        </p>

        {/* Image Upload */}
        <div className="mb-6">
          <ImageUploader
            onImageChange={handleImageSelect}
            imagePreview={preview}
            disabled={loading}
          />
        </div>

        {/* Scan Button */}
        <button
          onClick={handleScan}
          disabled={!image || loading}
          className="w-full bg-green-600 text-white py-4 rounded-xl text-lg font-semibold hover:bg-green-700 transition shadow-lg hover:shadow-xl disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Tahlil qilinmoqda...
            </>
          ) : (
            <>
              <Camera className="w-5 h-5" />
              Scan Qilish
            </>
          )}
        </button>

        {/* Results */}
        {result && (
          <div className={`mt-6 p-6 rounded-xl border ${
            result.found 
              ? 'bg-green-50 border-green-200' 
              : 'bg-yellow-50 border-yellow-200'
          }`}>
            <h3 className="text-xl font-semibold text-gray-900 mb-4">
              Natijalar
            </h3>
            
            {result.found && result.tree_id ? (
              <>
                <div className="mb-4">
                  <p className="text-sm text-gray-600">Daraxt ID:</p>
                  <p className="text-lg font-mono text-green-600">{result.tree_id}</p>
                </div>

                {result.tree_type && (
                  <div className="mb-4">
                    <p className="text-sm text-gray-600">Daraxt turi:</p>
                    <p className="text-lg font-semibold text-gray-900">{result.tree_type}</p>
                  </div>
                )}

                {(result.confidence !== undefined || result.similarity !== undefined) && (
                  <div className="mb-4">
                    <p className="text-sm text-gray-600">Ishonchlilik:</p>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-green-600 h-2 rounded-full"
                          style={{ width: `${(result.confidence || result.similarity || 0) * 100}%` }}
                        />
                      </div>
                      <span className="text-sm font-semibold">
                        {((result.confidence || result.similarity || 0) * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                )}

                {result.message && (
                  <p className="text-green-700 font-medium mt-4">{result.message}</p>
                )}
              </>
            ) : (
              <div className="text-center py-4">
                <div className="mb-4">
                  <p className="text-lg font-semibold text-yellow-800 mb-2">
                    {result.message || 'Bu daraxt bazada yo\'q'}
                  </p>
                  <p className="text-sm text-gray-600 mb-4">
                    Bu daraxt hali bazaga qo'shilmagan. Agar bu yangi daraxt bo'lsa, uni ro'yxatga olishingiz mumkin.
                  </p>
                </div>
                <button
                  onClick={() => navigate('/register')}
                  className="bg-green-600 text-white px-6 py-2 rounded-lg font-semibold hover:bg-green-700 transition"
                >
                  Daraxtni Ro'yxatga Olish
                </button>
              </div>
            )}

            {result.similar_trees && result.similar_trees.length > 0 && (
              <div className="mt-4">
                <p className="text-sm text-gray-600 mb-2">
                  O'xshash daraxtlar ({result.similar_trees.length}):
                </p>
                <div className="space-y-2">
                  {result.similar_trees.map((tree, idx) => (
                    <div
                      key={idx}
                      className="p-3 bg-white rounded-lg border border-green-200 hover:border-green-400 transition cursor-pointer"
                      onClick={() => navigate(`/tree/${tree.tree_id}`)}
                    >
                      <p className="font-medium text-gray-900">
                        {tree.tree_species || tree.tree_type || 'Noma\'lum tur'}
                      </p>
                      <p className="text-sm text-gray-600">
                        O'xshashlik: {(tree.similarity * 100).toFixed(1)}%
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default ScanPage;

