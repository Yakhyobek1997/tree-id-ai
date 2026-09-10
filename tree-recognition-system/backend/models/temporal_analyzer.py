# backend/models/temporal_analyzer.py

import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List
from scipy.stats import linregress

class TemporalAnalyzer:
    """
    Daraxtning vaqt o'tishi bilan o'zgarishini kuzatish.
    - O'sish
    - Rang o'zgarishi (fasllar)
    - Shoxlar kesilishi
    - Kasallik rivojlanishi
    """
    
    def __init__(self):
        self.season_colors = {
            'bahor': {'h_range': (35, 85), 'dominance': 0.3},    # Yashil
            'yoz': {'h_range': (35, 85), 'dominance': 0.5},      # Ko'k yashil
            'kuz': {'h_range': (10, 35), 'dominance': 0.4},      # Sariq/qizil
            'qish': {'h_range': (0, 180), 'dominance': 0.1}      # Kam rang
        }
    
    def analyze_temporal_changes(
        self,
        scans: List[Dict],
        time_window: str = 'all'
    ) -> Dict:
        """
        Bir nechta scan'larni tahlil qilib o'zgarishlarni aniqlash.
        
        Args:
            scans: Vaqt bo'yicha tartiblangan scan'lar
            time_window: 'all', 'year', 'month', 'week'
        
        Returns:
            {
                'growth_rate': 0.05,  # 5% per month
                'seasonal_pattern': {...},
                'pruning_events': [...],
                'health_trend': 'improving',
                'predictions': {...}
            }
        """
        
        if len(scans) < 2:
            return {
                'error': 'Kamida 2 ta scan kerak',
                'available_scans': len(scans)
            }
        
        # Sort by time
        scans = sorted(scans, key=lambda x: x['timestamp'])
        
        analysis = {
            'total_scans': len(scans),
            'time_span': self._calculate_time_span(scans),
            'growth_analysis': self._analyze_growth(scans),
            'color_analysis': self._analyze_color_changes(scans),
            'structural_analysis': self._analyze_structural_changes(scans),
            'health_analysis': self._analyze_health_trends(scans),
            'seasonal_pattern': self._detect_seasonal_pattern(scans),
            'predictions': self._make_predictions(scans)
        }
        
        return analysis
    
    def _calculate_time_span(self, scans: List[Dict]) -> Dict:
        """Vaqt oralig'ini hisoblash"""
        first = datetime.fromisoformat(scans[0]['timestamp'])
        last = datetime.fromisoformat(scans[-1]['timestamp'])
        
        delta = last - first
        
        return {
            'first_scan': scans[0]['timestamp'],
            'last_scan': scans[-1]['timestamp'],
            'days': delta.days,
            'months': delta.days / 30.44,
            'years': delta.days / 365.25
        }
    
    def _analyze_growth(self, scans: List[Dict]) -> Dict:
        """O'sishni tahlil qilish"""
        areas = []
        timestamps = []
        
        for scan in scans:
            areas.append(scan['features']['segmentation']['area'])
            timestamps.append(datetime.fromisoformat(scan['timestamp']).timestamp())
        
        # Linear regression
        if len(areas) > 1:
            slope, intercept, r_value, p_value, std_err = linregress(timestamps, areas)
            
            # Growth rate (per day)
            growth_rate_daily = slope / np.mean(areas) if np.mean(areas) > 0 else 0
            growth_rate_monthly = growth_rate_daily * 30.44
            growth_rate_yearly = growth_rate_daily * 365.25
        else:
            slope, r_value, growth_rate_daily = 0, 0, 0
            growth_rate_monthly, growth_rate_yearly = 0, 0
        
        # Absolute growth
        absolute_growth = areas[-1] - areas[0]
        relative_growth = absolute_growth / areas[0] if areas[0] > 0 else 0
        
        return {
            'initial_area': float(areas[0]),
            'current_area': float(areas[-1]),
            'absolute_growth': float(absolute_growth),
            'relative_growth_percent': float(relative_growth * 100),
            'growth_rate_daily': float(growth_rate_daily * 100),
            'growth_rate_monthly': float(growth_rate_monthly * 100),
            'growth_rate_yearly': float(growth_rate_yearly * 100),
            'trend_strength': float(r_value ** 2),  # R²
            'is_growing': slope > 0,
            'growth_consistency': 'high' if r_value**2 > 0.7 else 'low'
        }
    
    def _analyze_color_changes(self, scans: List[Dict]) -> Dict:
        """Rang o'zgarishini tahlil (fasllar)"""
        color_timeline = []
        
        for scan in scans:
            timestamp = scan['timestamp']
            colors = scan['features']['color']['dominant_colors']
            
            # Green percentage
            green_pct = sum(
                c['percentage'] for c in colors
                if 40 < self._bgr_to_hue(c['bgr']) < 85
            )
            
            # Yellow/Red percentage
            yellowred_pct = sum(
                c['percentage'] for c in colors
                if 0 <= self._bgr_to_hue(c['bgr']) < 35
            )
            
            color_timeline.append({
                'timestamp': timestamp,
                'green_percentage': green_pct,
                'yellowred_percentage': yellowred_pct,
                'detected_season': self._detect_season_from_colors(colors)
            })
        
        # Detect significant color changes
        color_changes = []
        for i in range(1, len(color_timeline)):
            prev = color_timeline[i-1]
            curr = color_timeline[i]
            
            green_diff = abs(curr['green_percentage'] - prev['green_percentage'])
            
            if green_diff > 0.2:  # 20% o'zgarish
                color_changes.append({
                    'from': prev['timestamp'],
                    'to': curr['timestamp'],
                    'type': 'seasonal_change',
                    'from_season': prev['detected_season'],
                    'to_season': curr['detected_season'],
                    'magnitude': float(green_diff)
                })
        
        return {
            'timeline': color_timeline,
            'significant_changes': color_changes,
            'current_season': color_timeline[-1]['detected_season'] if color_timeline else None
        }
    
    def _bgr_to_hue(self, bgr: List[int]) -> float:
        """BGR to Hue conversion"""
        b, g, r = bgr
        b, g, r = b/255.0, g/255.0, r/255.0
        
        max_val = max(r, g, b)
        min_val = min(r, g, b)
        diff = max_val - min_val
        
        if diff == 0:
            return 0
        
        if max_val == r:
            h = 60 * (((g - b) / diff) % 6)
        elif max_val == g:
            h = 60 * (((b - r) / diff) + 2)
        else:
            h = 60 * (((r - g) / diff) + 4)
        
        return h if h >= 0 else h + 360
    
    def _detect_season_from_colors(self, colors: List[Dict]) -> str:
        """Ranglardan faslni aniqlash"""
        green_amount = sum(
            c['percentage'] for c in colors
            if 40 < self._bgr_to_hue(c['bgr']) < 85
        )
        
        yellowred_amount = sum(
            c['percentage'] for c in colors
            if 0 <= self._bgr_to_hue(c['bgr']) < 35
        )
        
        if green_amount > 0.5:
            return 'yoz'
        elif yellowred_amount > 0.3:
            return 'kuz'
        elif green_amount > 0.3:
            return 'bahor'
        else:
            return 'qish'
    
    def _analyze_structural_changes(self, scans: List[Dict]) -> Dict:
        """Strukturaviy o'zgarishlar (shoxlar kesilishi)"""
        branch_counts = []
        timestamps = []
        
        for scan in scans:
            branch_counts.append(scan['features']['objects']['total_count'])
            timestamps.append(scan['timestamp'])
        
        # Detect pruning events (kesish voqealari)
        pruning_events = []
        for i in range(1, len(branch_counts)):
            prev_count = branch_counts[i-1]
            curr_count = branch_counts[i]
            
            # Agar 20% dan ko'p kamaysa
            if curr_count < prev_count * 0.8:
                pruning_events.append({
                    'date': timestamps[i],
                    'branches_before': prev_count,
                    'branches_after': curr_count,
                    'branches_removed': prev_count - curr_count,
                    'reduction_percent': float((prev_count - curr_count) / prev_count * 100)
                })
        
        return {
            'branch_count_timeline': [
                {'timestamp': t, 'count': c}
                for t, c in zip(timestamps, branch_counts)
            ],
            'pruning_events': pruning_events,
            'total_pruning_events': len(pruning_events),
            'current_branch_count': branch_counts[-1]
        }
    
    def _analyze_health_trends(self, scans: List[Dict]) -> Dict:
        """Salomatlik tendensiyasini tahlil"""
        health_scores = []
        timestamps = []
        
        for scan in scans:
            # Health score calculation
            features = scan['features']
            
            # Green color amount
            colors = features['color']['dominant_colors']
            green_pct = sum(
                c['percentage'] for c in colors
                if 40 < self._bgr_to_hue(c['bgr']) < 85
            )
            
            # Leaf/branch density
            area = features['segmentation']['area']
            branch_count = features['objects']['total_count']
            density = branch_count / area if area > 0 else 0
            
            # Texture uniformity (smooth bark = healthy)
            texture_uniformity = 1 - features['texture']['glcm_contrast'] / 100
            
            # Combined health score
            health = (
                green_pct * 40 +
                min(density * 10000, 30) +
                texture_uniformity * 30
            )
            
            health_scores.append(health)
            timestamps.append(scan['timestamp'])
        
        # Trend analysis
        if len(health_scores) > 1:
            slope, _, r_value, _, _ = linregress(
                range(len(health_scores)),
                health_scores
            )
            
            if slope > 0.5:
                trend = 'yaxshilanmoqda'
            elif slope < -0.5:
                trend = 'yomonlashmoqda'
            else:
                trend = 'barqaror'
        else:
            slope, r_value, trend = 0, 0, 'noma\'lum'
        
        return {
            'timeline': [
                {'timestamp': t, 'health_score': float(h)}
                for t, h in zip(timestamps, health_scores)
            ],
            'initial_health': float(health_scores[0]),
            'current_health': float(health_scores[-1]),
            'trend': trend,
            'trend_strength': float(r_value ** 2),
            'average_health': float(np.mean(health_scores)),
            'health_status': self._get_health_status(health_scores[-1])
        }
    
    def _get_health_status(self, score: float) -> str:
        """Health score'dan holat aniqlash"""
        if score >= 80:
            return 'a\'lo'
        elif score >= 60:
            return 'yaxshi'
        elif score >= 40:
            return 'o\'rtacha'
        else:
            return 'yomon'
    
    def _detect_seasonal_pattern(self, scans: List[Dict]) -> Dict:
        """Fasl naqshini aniqlash"""
        if len(scans) < 4:
            return {'error': 'Fasl naqshini aniqlash uchun 4+ scan kerak'}
        
        seasonal_data = {}
        
        for scan in scans:
            timestamp = datetime.fromisoformat(scan['timestamp'])
            month = timestamp.month
            
            # Season detection
            if month in [3, 4, 5]:
                season = 'bahor'
            elif month in [6, 7, 8]:
                season = 'yoz'
            elif month in [9, 10, 11]:
                season = 'kuz'
            else:
                season = 'qish'
            
            if season not in seasonal_data:
                seasonal_data[season] = []
            
            # Get green percentage
            colors = scan['features']['color']['dominant_colors']
            green_pct = sum(
                c['percentage'] for c in colors
                if 40 < self._bgr_to_hue(c['bgr']) < 85
            )
            
            seasonal_data[season].append({
                'green_percentage': green_pct,
                'area': scan['features']['segmentation']['area'],
                'branch_count': scan['features']['objects']['total_count']
            })
        
        # Average by season
        seasonal_averages = {}
        for season, data_list in seasonal_data.items():
            seasonal_averages[season] = {
                'avg_green': float(np.mean([d['green_percentage'] for d in data_list])),
                'avg_area': float(np.mean([d['area'] for d in data_list])),
                'avg_branches': float(np.mean([d['branch_count'] for d in data_list])),
                'sample_count': len(data_list)
            }
        
        return {
            'seasonal_averages': seasonal_averages,
            'has_clear_pattern': len(seasonal_data) >= 3
        }
    
    def _make_predictions(self, scans: List[Dict]) -> Dict:
        """Kelajakni bashorat qilish"""
        if len(scans) < 3:
            return {'error': 'Bashorat uchun 3+ scan kerak'}
        
        # Growth prediction
        areas = [s['features']['segmentation']['area'] for s in scans]
        timestamps = [datetime.fromisoformat(s['timestamp']).timestamp() for s in scans]
        
        slope, intercept, r_value, _, _ = linregress(timestamps, areas)
        
        # Predict 30, 90, 365 days
        last_timestamp = timestamps[-1]
        predictions = {}
        
        for days in [30, 90, 365]:
            future_timestamp = last_timestamp + (days * 24 * 60 * 60)
            predicted_area = slope * future_timestamp + intercept
            
            predictions[f'{days}_days'] = {
                'predicted_area': float(predicted_area),
                'growth_from_current': float(predicted_area - areas[-1]),
                'confidence': float(r_value ** 2)
            }
        
        return predictions
    
    def compare_two_scans(self, scan1: Dict, scan2: Dict) -> Dict:
        """Ikki scan'ni solishtirish"""
        time1 = datetime.fromisoformat(scan1['timestamp'])
        time2 = datetime.fromisoformat(scan2['timestamp'])
        time_diff = abs((time2 - time1).days)
        
        f1 = scan1['features']
        f2 = scan2['features']
        
        # Area change
        area_change = f2['segmentation']['area'] - f1['segmentation']['area']
        area_change_pct = (area_change / f1['segmentation']['area'] * 100) if f1['segmentation']['area'] > 0 else 0
        
        # Branch change
        branch_change = f2['objects']['total_count'] - f1['objects']['total_count']
        
        # Color change
        color1 = f1['color']['histogram']
        color2 = f2['color']['histogram']
        color_difference = np.sqrt(np.sum((color1 - color2) ** 2))
        
        return {
            'time_difference_days': time_diff,
            'area_change': {
                'absolute': float(area_change),
                'percentage': float(area_change_pct),
                'per_day': float(area_change / time_diff) if time_diff > 0 else 0
            },
            'branch_change': {
                'absolute': branch_change,
                'pruned': branch_change < -2
            },
            'color_change': {
                'magnitude': float(color_difference),
                'season_change': self._detect_season_from_colors(f1['color']['dominant_colors']) != 
                                self._detect_season_from_colors(f2['color']['dominant_colors'])
            }
        }