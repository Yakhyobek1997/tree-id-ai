import React from 'react';

function ImageUploader({ onImageChange, imagePreview, disabled }) {
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      onImageChange(file);
    }
  };

  return (
    <div>
      <div className="file-input-wrapper">
        <input
          type="file"
          accept="image/*"
          capture="environment"
          onChange={handleFileChange}
          disabled={disabled}
        />
      </div>
      
      {imagePreview && (
        <div className="image-preview">
          <img src={imagePreview} alt="Preview" />
        </div>
      )}
    </div>
  );
}

export default ImageUploader;
