
# backend/models/feature_extractor.py

import cv2
import numpy as np
from PIL import Image
from typing import Dict, List, Tuple, Optional
import os

# Optional ML imports with fallbacks
try:
    import torch
    import torch.nn as nn
    import torchvision.transforms as transforms
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    from transformers import ViTModel, AutoImageProcessor
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

try:
    from segment_anything import sam_model_registry, SamPredictor
    SAM_AVAILABLE = True
except ImportError:
    SAM_AVAILABLE = False

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False

try:
    import timm
    TIMM_AVAILABLE = True
except ImportError:
    TIMM_AVAILABLE = False

class FeatureExtractor:
    """
    Simple feature extractor that works without heavy ML dependencies
    Uses OpenCV and numpy for basic feature extraction
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize feature extractor
        
        Args:
            model_path: Path to model (optional, not used in simple version)
        """
        self.model_path = model_path
        print("Simple FeatureExtractor initialized (using OpenCV)")
    
    def extract_features(self, image_path: str) -> np.ndarray:
        """
        Extract features from image using improved methods
        
        Args:
            image_path: Path to image
            
        Returns:
            Feature vector (normalized and more discriminative)
        """
        try:
            # Load image
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            # Resize to standard size for consistency
            img = cv2.resize(img, (224, 224))
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Extract multiple feature types
            features = []
            
            # 1. Multi-scale Color Histograms (more bins for better discrimination)
            for channel in range(3):
                hist = cv2.calcHist([img], [channel], None, [64], [0, 256])
                hist = cv2.normalize(hist, hist).flatten()
                features.extend(hist)
            
            # 2. HSV Color Space (illumination invariant)
            hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            for channel in range(3):
                hist = cv2.calcHist([hsv], [channel], None, [32], [0, 256] if channel > 0 else [0, 180])
                hist = cv2.normalize(hist, hist).flatten()
                features.extend(hist)
            
            # 3. Enhanced Texture features
            texture_feats = self._extract_texture_features(gray)
            features.extend(texture_feats)
            
            # 4. Edge features (important for tree structure)
            edges = cv2.Canny(gray, 50, 150)
            edge_hist = cv2.calcHist([edges], [0], None, [32], [0, 256])
            edge_hist = cv2.normalize(edge_hist, edge_hist).flatten()
            features.extend(edge_hist)
            
            # 5. Shape features
            shape_feats = self._extract_shape_features(gray)
            features.extend(shape_feats)
            
            # 6. Spatial Color Distribution (divided into grid)
            grid_features = self._extract_spatial_features(img_rgb)
            features.extend(grid_features)
            
            # 7. Color moments
            for channel in range(3):
                channel_data = img_rgb[:,:,channel].flatten()
                features.extend([
                    np.mean(channel_data),
                    np.std(channel_data),
                    np.cbrt(np.mean((channel_data - np.mean(channel_data))**3)),  # Signed third color moment
                    np.mean((channel_data - np.mean(channel_data))**4)  # Kurtosis
                ])
            
            # Convert to numpy array and normalize
            features = np.array(features, dtype=np.float32)
            if not np.all(np.isfinite(features)):
                raise ValueError("Feature extraction produced non-finite values")
            
            # L2 normalization for better similarity comparison
            norm = np.linalg.norm(features)
            if norm > 0:
                features = features / norm
            
            return features
            
        except Exception as e:
            print(f"Error extracting features: {e}")
            import traceback
            traceback.print_exc()
            raise ValueError("Could not extract valid image features") from e
    
    def _extract_spatial_features(self, img_rgb: np.ndarray) -> List[float]:
        """Extract spatial color distribution features"""
        features = []
        h, w = img_rgb.shape[:2]
        
        # Divide image into 2x2 grid
        grid_h, grid_w = h // 2, w // 2
        
        for i in range(2):
            for j in range(2):
                # Get grid cell
                cell = img_rgb[i*grid_h:(i+1)*grid_h, j*grid_w:(j+1)*grid_w]
                
                # Color statistics for each cell
                for channel in range(3):
                    features.append(np.mean(cell[:,:,channel]))
                    features.append(np.std(cell[:,:,channel]))
        
        return features
    
    def _extract_texture_features(self, gray: np.ndarray) -> List[float]:
        """Extract enhanced texture features"""
        features = []
        
        # Resize for consistent feature size
        gray = cv2.resize(gray, (128, 128))
        
        # 1. Local binary pattern-like features
        kernel = np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]])
        conv = cv2.filter2D(gray.astype(np.float32), -1, kernel)
        features.extend([
            np.mean(conv),
            np.std(conv),
            np.min(conv),
            np.max(conv)
        ])
        
        # 2. Gradient features (multiple scales)
        for ksize in [3, 5]:
            grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=ksize)
            grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=ksize)
            magnitude = np.sqrt(grad_x**2 + grad_y**2)
            features.extend([
                np.mean(magnitude),
                np.std(magnitude),
                np.median(magnitude)
            ])
        
        # 3. Laplacian (edge detection)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        features.extend([
            np.mean(np.abs(laplacian)),
            np.std(laplacian)
        ])
        
        # 4. Entropy (texture complexity)
        hist, _ = np.histogram(gray, bins=256, range=(0, 256), density=True)
        hist = hist[hist > 0]  # Remove zeros
        entropy = -np.sum(hist * np.log2(hist))
        features.append(entropy)
        
        return features
    
    def _extract_shape_features(self, gray: np.ndarray) -> List[float]:
        """Extract enhanced shape features"""
        features = []
        
        # Multiple thresholding methods for robustness
        thresholds = []
        
        # 1. Otsu's thresholding
        _, thresh1 = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        thresholds.append(thresh1)
        
        # 2. Adaptive thresholding
        thresh2 = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        thresholds.append(thresh2)
        
        for thresh in thresholds:
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if len(contours) > 0:
                # Largest contour
                cnt = max(contours, key=cv2.contourArea)
                area = cv2.contourArea(cnt)
                perimeter = cv2.arcLength(cnt, True)
                
                # Bounding box
                x, y, w, h = cv2.boundingRect(cnt)
                aspect_ratio = float(w) / h if h > 0 else 0
                extent = area / (w * h) if w * h > 0 else 0
                
                # Convex hull
                hull = cv2.convexHull(cnt)
                hull_area = cv2.contourArea(hull)
                solidity = area / hull_area if hull_area > 0 else 0
                
                # Compactness
                compactness = 4 * np.pi * area / (perimeter**2) if perimeter > 0 else 0
                
                features.extend([
                    area / 10000,  # Normalize
                    perimeter / 1000,  # Normalize
                    aspect_ratio,
                    extent,
                    solidity,
                    compactness
                ])
            else:
                features.extend([0, 0, 0, 0, 0, 0])
        
        return features


class MultiViewFeatureExtractor:
    """
    Daraxtni HAR TOMONDAN taniy oladigan feature extractor.
    Rotation, scale, illumination invariant.
    """
    
    def __init__(self, device=None):
        if device is None:
            self.device = 'cuda' if TORCH_AVAILABLE and torch.cuda.is_available() else 'cpu'
        else:
            self.device = device
        print(f"Device: {self.device}")
        
        # Initialize models with fallbacks
        self.vit_processor = None
        self.vit_model = None
        self.yolo = None
        self.sam = None
        self.sam_predictor = None
        self.superpoint = None
        self.efficient_net = None
        self.transform = None
        
        # 1. GLOBAL FEATURES - Vision Transformer (rotation invariant)
        if TRANSFORMERS_AVAILABLE and TORCH_AVAILABLE:
            try:
                print("Loading Vision Transformer...")
                self.vit_processor = AutoImageProcessor.from_pretrained(
                    'google/vit-large-patch16-224-in21k'
                )
                self.vit_model = ViTModel.from_pretrained(
                    'google/vit-large-patch16-224-in21k'
                ).to(self.device)
                self.vit_model.eval()
            except Exception as e:
                print(f"Warning: Vision Transformer not loaded: {e}")
        else:
            print("Warning: Vision Transformer not available (transformers/torch not installed)")
        
        # 2. OBJECT DETECTION - YOLO v8
        if YOLO_AVAILABLE:
            try:
                print("Loading YOLO v8...")
                self.yolo = YOLO('yolov8x.pt')
            except Exception as e:
                print(f"Warning: YOLO not loaded: {e}")
        else:
            print("Warning: YOLO not available (ultralytics not installed)")
        
        # 3. SEGMENTATION - SAM
        if SAM_AVAILABLE and TORCH_AVAILABLE:
            try:
                print("Loading Segment Anything Model...")
                sam_checkpoint = "sam_vit_h_4b8939.pth"
                if os.path.exists(sam_checkpoint):
                    self.sam = sam_model_registry["vit_h"](checkpoint=sam_checkpoint)
                    self.sam.to(self.device)
                    self.sam_predictor = SamPredictor(self.sam)
                else:
                    print(f"Warning: SAM checkpoint not found: {sam_checkpoint}")
            except Exception as e:
                print(f"Warning: SAM not loaded: {e}")
        else:
            print("Warning: SAM not available")
        
        # 4. LOCAL FEATURES - SuperPoint
        print("Loading SuperPoint...")
        self.superpoint = self._load_superpoint()
        
        # 5. MULTI-SCALE CNN - EfficientNet
        if TIMM_AVAILABLE and TORCH_AVAILABLE:
            try:
                print("Loading EfficientNet...")
                self.efficient_net = timm.create_model(
                    'tf_efficientnet_b7_ns',
                    pretrained=True,
                    num_classes=0
                ).to(self.device)
                self.efficient_net.eval()
            except Exception as e:
                print(f"Warning: EfficientNet not loaded: {e}")
        else:
            print("Warning: EfficientNet not available (timm not installed)")
        
        # Image preprocessing
        if TORCH_AVAILABLE:
            self.transform = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225]
                )
            ])
        
        print("Models loaded (some in fallback mode)\n")
    
    def _load_superpoint(self):
        """SuperPoint model yukla"""
        try:
            from models.superpoint import SuperPoint
            config = {
                'nms_dist': 4,
                'conf_thresh': 0.015,
                'nn_thresh': 0.7,
                'cuda': self.device == 'cuda'
            }
            return SuperPoint(config)
        except:
            print("Warning: SuperPoint not loaded, using SIFT")
            return cv2.SIFT_create(nfeatures=2000)
    
    def extract_all_features(self, image_path: str) -> Dict:
        """
        BARCHA feature'larni chiqarish.
        Bu funksiya daraxtni HAR TOMONDAN taniy oladi!
        """
        print(f"Analyzing: {image_path}")
        
        # Rasmni yuklash
        img_cv = cv2.imread(image_path)
        img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
        img_pil = Image.open(image_path).convert('RGB')
        
        features = {
            'image_path': image_path,
            'image_shape': img_cv.shape
        }
        
        # ====== 1. GLOBAL FEATURES (butun daraxt) ======
        print("  📊 Global features...")
        features['global'] = self._extract_global_features(img_pil)
        
        # ====== 2. MULTI-SCALE FEATURES ======
        print("  🔎 Multi-scale features...")
        features['multiscale'] = self._extract_multiscale_features(img_pil)
        
        # ====== 3. ROTATION-INVARIANT LOCAL FEATURES ======
        print("  🌀 Local features (rotation invariant)...")
        features['local'] = self._extract_local_features(img_cv)
        
        # ====== 4. OBJECT DETECTION (shoxlar, barglar) ======
        print("  🌿 Object detection...")
        features['objects'] = self._detect_tree_parts(img_rgb)
        
        # ====== 5. SEGMENTATION (daraxt maskasi) ======
        print("  ✂️ Segmentation...")
        features['segmentation'] = self._segment_tree(img_rgb)
        
        # ====== 6. COLOR FEATURES (har xil yorug'likda) ======
        print("  🎨 Color features...")
        features['color'] = self._extract_color_features(img_cv)
        
        # ====== 7. TEXTURE FEATURES (po'stloq) ======
        print("  🌳 Texture features...")
        features['texture'] = self._extract_texture_features(img_cv)
        
        # ====== 8. GEOMETRIC FEATURES (shakl) ======
        print("  📐 Geometric features...")
        features['geometry'] = self._extract_geometric_features(
            features['segmentation']['mask']
        )
        
        print("Analysis complete!\n")
        return features
    
    def _extract_global_features(self, img_pil: Image) -> Dict:
        """Vision Transformer bilan global features"""
        inputs = self.vit_processor(images=img_pil, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.vit_model(**inputs)
            # [CLS] token = global representation
            global_vec = outputs.last_hidden_state[:, 0].cpu().numpy()
            # Boshqa tokenlar = spatial features
            spatial_vecs = outputs.last_hidden_state[:, 1:].mean(dim=1).cpu().numpy()
        
        return {
            'vector': global_vec.flatten(),
            'spatial_vector': spatial_vecs.flatten(),
            'dimension': global_vec.shape[-1]
        }
    
    def _extract_multiscale_features(self, img_pil: Image) -> Dict:
        """EfficientNet bilan har xil scale'da features"""
        img_tensor = self.transform(img_pil).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            features = self.efficient_net(img_tensor)
            features_np = features.cpu().numpy().flatten()
        
        return {
            'vector': features_np,
            'dimension': len(features_np)
        }
    
    def _extract_local_features(self, img_cv: np.ndarray) -> Dict:
        """Rotation va scale invariant local features"""
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        
        # SIFT (eng ishonchli)
        sift = cv2.SIFT_create(nfeatures=2000)
        keypoints_sift, descriptors_sift = sift.detectAndCompute(gray, None)
        
        # ORB (tez)
        orb = cv2.ORB_create(nfeatures=2000)
        keypoints_orb, descriptors_orb = orb.detectAndCompute(gray, None)
        
        # AKAZE (rotation invariant)
        akaze = cv2.AKAZE_create()
        keypoints_akaze, descriptors_akaze = akaze.detectAndCompute(gray, None)
        
        return {
            'sift': {
                'keypoints': keypoints_sift,
                'descriptors': descriptors_sift,
                'count': len(keypoints_sift)
            },
            'orb': {
                'keypoints': keypoints_orb,
                'descriptors': descriptors_orb,
                'count': len(keypoints_orb)
            },
            'akaze': {
                'keypoints': keypoints_akaze,
                'descriptors': descriptors_akaze,
                'count': len(keypoints_akaze)
            }
        }
    
    def _detect_tree_parts(self, img_rgb: np.ndarray) -> Dict:
        """YOLO bilan daraxt qismlarini aniqlash"""
        results = self.yolo(img_rgb, verbose=False)
        
        detections = {
            'branches': [],
            'leaves': [],
            'trunk': None,
            'total_count': 0
        }
        
        if len(results) > 0 and results[0].boxes is not None:
            for box in results[0].boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                conf = float(box.conf[0])
                cls = int(box.cls[0])
                
                detection = {
                    'bbox': [float(x1), float(y1), float(x2), float(y2)],
                    'confidence': conf,
                    'class': cls,
                    'area': float((x2-x1) * (y2-y1)),
                    'aspect_ratio': float((x2-x1) / (y2-y1) if y2-y1 > 0 else 0)
                }
                
                detections['branches'].append(detection)
                detections['total_count'] += 1
        
        return detections
    
    def _segment_tree(self, img_rgb: np.ndarray) -> Dict:
        """SAM bilan daraxtni segmentatsiya qilish"""
        self.sam_predictor.set_image(img_rgb)
        
        h, w = img_rgb.shape[:2]
        
        # Bir nechta nuqtalardan segment qilish
        points = np.array([
            [w//2, h//2],      # Markaz
            [w//3, h//3],      # Chap yuqori
            [2*w//3, h//3],    # O'ng yuqori
            [w//3, 2*h//3],    # Chap pastki
            [2*w//3, 2*h//3]   # O'ng pastki
        ])
        labels = np.ones(len(points))
        
        masks, scores, logits = self.sam_predictor.predict(
            point_coords=points,
            point_labels=labels,
            multimask_output=True
        )
        
        # Eng yaxshi maskani tanlash
        best_idx = np.argmax(scores)
        best_mask = masks[best_idx]
        
        # Mask'dan kontur chiqarish
        contours, _ = cv2.findContours(
            best_mask.astype(np.uint8),
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        if len(contours) > 0:
            main_contour = max(contours, key=cv2.contourArea)
            contour_area = cv2.contourArea(main_contour)
            perimeter = cv2.arcLength(main_contour, True)
        else:
            contour_area = 0
            perimeter = 0
        
        return {
            'mask': best_mask,
            'score': float(scores[best_idx]),
            'area': float(np.sum(best_mask)),
            'contour_area': float(contour_area),
            'perimeter': float(perimeter),
            'compactness': float(4 * np.pi * contour_area / (perimeter**2) if perimeter > 0 else 0)
        }
    
    def _extract_color_features(self, img_cv: np.ndarray) -> Dict:
        """Har xil color space'larda features"""
        # HSV
        hsv = cv2.cvtColor(img_cv, cv2.COLOR_BGR2HSV)
        hist_h = cv2.calcHist([hsv], [0], None, [32], [0, 180])
        hist_s = cv2.calcHist([hsv], [1], None, [32], [0, 256])
        hist_v = cv2.calcHist([hsv], [2], None, [32], [0, 256])
        
        # LAB
        lab = cv2.cvtColor(img_cv, cv2.COLOR_BGR2LAB)
        hist_l = cv2.calcHist([lab], [0], None, [32], [0, 256])
        hist_a = cv2.calcHist([lab], [1], None, [32], [0, 256])
        hist_b = cv2.calcHist([lab], [2], None, [32], [0, 256])
        
        # RGB
        hist_r = cv2.calcHist([img_cv], [0], None, [32], [0, 256])
        hist_g = cv2.calcHist([img_cv], [1], None, [32], [0, 256])
        hist_b_chan = cv2.calcHist([img_cv], [2], None, [32], [0, 256])
        
        # Normalize
        histograms = {
            'hsv_h': cv2.normalize(hist_h, hist_h).flatten(),
            'hsv_s': cv2.normalize(hist_s, hist_s).flatten(),
            'hsv_v': cv2.normalize(hist_v, hist_v).flatten(),
            'lab_l': cv2.normalize(hist_l, hist_l).flatten(),
            'lab_a': cv2.normalize(hist_a, hist_a).flatten(),
            'lab_b': cv2.normalize(hist_b, hist_b).flatten(),
            'rgb_r': cv2.normalize(hist_r, hist_r).flatten(),
            'rgb_g': cv2.normalize(hist_g, hist_g).flatten(),
            'rgb_b': cv2.normalize(hist_b_chan, hist_b_chan).flatten()
        }
        
        # Concatenate all
        combined = np.concatenate([v for v in histograms.values()])
        
        return {
            'histogram': combined,
            'dimension': len(combined),
            'dominant_colors': self._extract_dominant_colors(img_cv)
        }
    
    def _extract_dominant_colors(self, img_cv: np.ndarray, k=5) -> List:
        """K-means bilan dominant ranglarni topish"""
        from sklearn.cluster import KMeans
        
        pixels = img_cv.reshape(-1, 3).astype(np.float32)
        
        # Random sample (tezlik uchun)
        if len(pixels) > 10000:
            indices = np.random.choice(len(pixels), 10000, replace=False)
            pixels = pixels[indices]
        
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans.fit(pixels)
        
        colors = kmeans.cluster_centers_.astype(int)
        labels = kmeans.labels_
        
        # Har bir rangning foizi
        percentages = np.bincount(labels) / len(labels)
        
        dominant_colors = []
        for color, percentage in zip(colors, percentages):
            dominant_colors.append({
                'bgr': color.tolist(),
                'percentage': float(percentage)
            })
        
        return sorted(dominant_colors, key=lambda x: x['percentage'], reverse=True)
    
    def _extract_texture_features(self, img_cv: np.ndarray) -> Dict:
        """Po'stloq teksturasini tahlil qilish"""
        from skimage.feature import local_binary_pattern, graycomatrix, graycoprops
        
        gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        
        # Local Binary Pattern
        lbp = local_binary_pattern(gray, P=8, R=1, method='uniform')
        hist_lbp, _ = np.histogram(lbp.ravel(), bins=59, range=(0, 59), density=True)
        
        # Gray Level Co-occurrence Matrix (GLCM)
        # Resize uchun (tezlik)
        gray_small = cv2.resize(gray, (256, 256))
        glcm = graycomatrix(
            gray_small,
            distances=[1, 2, 3],
            angles=[0, np.pi/4, np.pi/2, 3*np.pi/4],
            levels=256,
            symmetric=True,
            normed=True
        )
        
        # GLCM properties
        contrast = graycoprops(glcm, 'contrast').flatten()
        dissimilarity = graycoprops(glcm, 'dissimilarity').flatten()
        homogeneity = graycoprops(glcm, 'homogeneity').flatten()
        energy = graycoprops(glcm, 'energy').flatten()
        correlation = graycoprops(glcm, 'correlation').flatten()
        
        # Gabor filters (bark texture)
        gabor_features = self._apply_gabor_filters(gray)
        
        return {
            'lbp': hist_lbp,
            'glcm_contrast': contrast.mean(),
            'glcm_dissimilarity': dissimilarity.mean(),
            'glcm_homogeneity': homogeneity.mean(),
            'glcm_energy': energy.mean(),
            'glcm_correlation': correlation.mean(),
            'gabor': gabor_features
        }
    
    def _apply_gabor_filters(self, gray: np.ndarray) -> np.ndarray:
        """Gabor filters (bark texture uchun)"""
        filters = []
        ksize = 31
        
        for theta in np.arange(0, np.pi, np.pi / 4):
            for sigma in [3, 5]:
                for lambd in [5, 10]:
                    kernel = cv2.getGaborKernel(
                        (ksize, ksize),
                        sigma,
                        theta,
                        lambd,
                        0.5,
                        0
                    )
                    filtered = cv2.filter2D(gray, cv2.CV_8UC3, kernel)
                    filters.append(filtered.mean())
        
        return np.array(filters)
    
    def _extract_geometric_features(self, mask: np.ndarray) -> Dict:
        """Geometrik features (shakl)"""
        contours, _ = cv2.findContours(
            mask.astype(np.uint8),
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        if len(contours) == 0:
            return {
                'area': 0,
                'perimeter': 0,
                'aspect_ratio': 0,
                'extent': 0,
                'solidity': 0,
                'hu_moments': np.zeros(7)
            }
        
        cnt = max(contours, key=cv2.contourArea)
        
        area = cv2.contourArea(cnt)
        perimeter = cv2.arcLength(cnt, True)
        
        # Bounding rectangle
        x, y, w, h = cv2.boundingRect(cnt)
        aspect_ratio = float(w) / h if h > 0 else 0
        extent = area / (w * h) if w * h > 0 else 0
        
        # Convex hull
        hull = cv2.convexHull(cnt)
        hull_area = cv2.contourArea(hull)
        solidity = area / hull_area if hull_area > 0 else 0
        
        # Hu moments (rotation invariant!)
        moments = cv2.moments(cnt)
        hu_moments = cv2.HuMoments(moments).flatten()
        
        return {
            'area': float(area),
            'perimeter': float(perimeter),
            'aspect_ratio': aspect_ratio,
            'extent': extent,
            'solidity': solidity,
            'hu_moments': hu_moments,
            'centroid': [
                float(moments['m10'] / moments['m00']) if moments['m00'] > 0 else 0,
                float(moments['m01'] / moments['m00']) if moments['m00'] > 0 else 0
            ]
        }
