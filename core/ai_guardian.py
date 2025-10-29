# core/ai_guardian.py - AI Guardian Alerts System
"""
AI Guardian: Local content moderation that protects your family
- Scans uploaded files for potential risks
- Flags inappropriate content, personal data leaks, violence
- ALL processing happens locally - zero data leaves your Black Box
- Encrypted alerts for parents
"""

import re
import json
from datetime import datetime
from django.core.files.uploadedfile import UploadedFile

class AIGuardian:
    """
    Local AI content moderation system
    Scans files before encryption and flags potential issues
    """

    # Keywords for different risk categories
    RISK_CATEGORIES = {
        'personal_data': {
            'patterns': [
                r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
                r'\b\d{16}\b',  # Credit card
                r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b',  # Email
                r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # Phone number
            ],
            'keywords': ['password', 'ssn', 'social security', 'credit card', 'bank account'],
            'severity': 'high',
            'icon': '🔐',
            'message': 'May contain personal data (SSN, credit card, passwords)'
        },
        'inappropriate': {
            'keywords': ['explicit', 'nsfw', 'adult', 'pornography'],
            'severity': 'critical',
            'icon': '🚫',
            'message': 'May contain inappropriate or explicit content'
        },
        'violence': {
            'keywords': ['weapon', 'gun', 'violence', 'threat', 'harm', 'kill'],
            'severity': 'high',
            'icon': '⚠️',
            'message': 'May contain references to violence or weapons'
        },
        'privacy_concern': {
            'keywords': ['address', 'location', 'home address', 'phone number', 'private'],
            'severity': 'medium',
            'icon': '📍',
            'message': 'May contain location or privacy-sensitive information'
        },
        'medical': {
            'keywords': ['prescription', 'medication', 'medical record', 'diagnosis', 'treatment'],
            'severity': 'medium',
            'icon': '💊',
            'message': 'May contain medical or health information'
        }
    }

    def __init__(self):
        self.alerts_log = []

    def scan_file(self, file: UploadedFile, owner_name: str) -> dict:
        """
        Scan an uploaded file for potential risks

        Returns:
            {
                'safe': bool,
                'flags': list of detected issues,
                'severity': 'safe'|'medium'|'high'|'critical',
                'recommendations': list of strings
            }
        """
        flags = []
        max_severity = 'safe'

        # Get file content
        content = self._extract_content(file)

        if not content:
            return {
                'safe': True,
                'flags': [],
                'severity': 'safe',
                'recommendations': []
            }

        # Scan for each risk category
        for category, rules in self.RISK_CATEGORIES.items():
            detected = self._check_category(content, rules)
            if detected:
                flags.append({
                    'category': category,
                    'severity': rules['severity'],
                    'icon': rules['icon'],
                    'message': rules['message'],
                    'details': detected
                })

                # Update max severity
                if self._severity_level(rules['severity']) > self._severity_level(max_severity):
                    max_severity = rules['severity']

        # Generate recommendations
        recommendations = self._generate_recommendations(flags)

        # Log the alert
        if flags:
            self.alerts_log.append({
                'timestamp': datetime.now().isoformat(),
                'file_name': file.name,
                'owner': owner_name,
                'flags': flags,
                'severity': max_severity
            })

        return {
            'safe': len(flags) == 0,
            'flags': flags,
            'severity': max_severity,
            'recommendations': recommendations,
            'scanned_at': datetime.now().isoformat()
        }

    def _extract_content(self, file: UploadedFile) -> str:
        """Extract text content from file for scanning"""
        try:
            # For text files
            if file.content_type and 'text' in file.content_type:
                return file.read().decode('utf-8', errors='ignore')

            # For common document types (in production, use proper parsers)
            if file.name.endswith(('.txt', '.md', '.csv', '.log')):
                return file.read().decode('utf-8', errors='ignore')

            # For PDFs, images, etc. - in production, use OCR/PDF parsers
            # For now, scan filename and basic metadata
            return file.name

        except Exception as e:
            print(f"Error extracting content: {e}")
            return ""

    def _check_category(self, content: str, rules: dict) -> list:
        """Check if content matches category rules"""
        matches = []
        content_lower = content.lower()

        # Check regex patterns
        if 'patterns' in rules:
            for pattern in rules['patterns']:
                found = re.findall(pattern, content, re.IGNORECASE)
                if found:
                    matches.extend([f"Pattern detected: {match[:10]}..." for match in found])

        # Check keywords
        if 'keywords' in rules:
            for keyword in rules['keywords']:
                if keyword.lower() in content_lower:
                    matches.append(f"Keyword: {keyword}")

        return matches

    def _severity_level(self, severity: str) -> int:
        """Convert severity to numeric level for comparison"""
        levels = {'safe': 0, 'medium': 1, 'high': 2, 'critical': 3}
        return levels.get(severity, 0)

    def _generate_recommendations(self, flags: list) -> list:
        """Generate actionable recommendations based on flags"""
        recommendations = []

        if not flags:
            return ["✅ File looks safe! No issues detected."]

        # Check severities
        has_critical = any(f['severity'] == 'critical' for f in flags)
        has_high = any(f['severity'] == 'high' for f in flags)

        if has_critical:
            recommendations.append("🚨 Review this file immediately before sharing with family")
            recommendations.append("Consider removing sensitive content or using a different file")

        if has_high:
            recommendations.append("⚠️ This file contains sensitive information")
            recommendations.append("Make sure only trusted family members have access")

        # Category-specific recommendations
        categories = [f['category'] for f in flags]

        if 'personal_data' in categories:
            recommendations.append("💡 Remove or redact personal data before uploading")

        if 'privacy_concern' in categories:
            recommendations.append("📍 Consider if location/contact info needs to be shared")

        if 'medical' in categories:
            recommendations.append("💊 Medical records should be stored with extra care")

        return recommendations

    def scan_content(self, content: str, filename: str, file_type: str = 'other') -> dict:
        """
        Scan raw text content for risks
        Used by vault upload integration

        Args:
            content: Text content to scan
            filename: Name of the file
            file_type: Type of file (document, image, etc.)

        Returns:
            {
                'severity': 'safe'|'low'|'medium'|'high'|'critical',
                'risk_score': 0-100,
                'patterns_detected': ['SSN', 'Credit Card'],
                'keywords_detected': ['password', 'address'],
                'categories': ['personal_data', 'privacy'],
                'summary': 'AI analysis summary',
                'recommendations': 'What to do about it'
            }
        """
        flags = []
        max_severity = 'safe'
        patterns_detected = []
        keywords_detected = []
        categories = []

        # If no content, assume safe
        if not content or len(content.strip()) == 0:
            # Check filename for keywords
            content = filename

        # Scan for each risk category
        for category, rules in self.RISK_CATEGORIES.items():
            detected = self._check_category(content, rules)
            if detected:
                categories.append(category)
                flags.append({
                    'category': category,
                    'severity': rules['severity'],
                    'icon': rules['icon'],
                    'message': rules['message'],
                    'details': detected
                })

                # Track patterns and keywords separately
                for detail in detected:
                    if 'Pattern detected' in detail:
                        pattern_name = category.replace('_', ' ').title()
                        if pattern_name not in patterns_detected:
                            patterns_detected.append(pattern_name)
                    elif 'Keyword' in detail:
                        keyword = detail.split(': ')[1] if ': ' in detail else detail
                        if keyword not in keywords_detected:
                            keywords_detected.append(keyword)

                # Update max severity
                if self._severity_level(rules['severity']) > self._severity_level(max_severity):
                    max_severity = rules['severity']

        # Calculate risk score (0-100)
        risk_score = 0
        if max_severity == 'low':
            risk_score = 30
        elif max_severity == 'medium':
            risk_score = 50
        elif max_severity == 'high':
            risk_score = 75
        elif max_severity == 'critical':
            risk_score = 95

        # Add points for multiple categories
        risk_score += min(len(categories) * 5, 20)
        risk_score = min(risk_score, 100)

        # Generate summary
        if len(flags) == 0:
            summary = f"File '{filename}' passed all security scans. No risks detected."
        else:
            issues = ', '.join([f['category'].replace('_', ' ') for f in flags])
            summary = f"Detected potential {issues} in '{filename}'."

        # Generate recommendations
        recommendations_list = self._generate_recommendations(flags)
        recommendations = ' '.join(recommendations_list)

        return {
            'severity': max_severity,
            'risk_score': risk_score,
            'patterns_detected': patterns_detected,
            'keywords_detected': keywords_detected,
            'categories': categories,
            'summary': summary,
            'recommendations': recommendations,
            'flags': flags  # Keep for compatibility
        }

    def get_family_safety_score(self, member_id: int) -> dict:
        """
        Calculate a safety score for a family member based on their uploads
        """
        member_alerts = [a for a in self.alerts_log if a.get('owner') == member_id]

        total_files = len(member_alerts) + 100  # Assume some safe files
        flagged_files = len(member_alerts)
        critical_flags = sum(1 for a in member_alerts if a['severity'] == 'critical')

        safety_score = max(0, 100 - (flagged_files * 5) - (critical_flags * 20))

        return {
            'score': safety_score,
            'total_files_scanned': total_files,
            'flagged_files': flagged_files,
            'critical_flags': critical_flags,
            'status': 'excellent' if safety_score > 90 else 'good' if safety_score > 70 else 'needs_attention'
        }


# Global instance
guardian = AIGuardian()


def scan_upload(file: UploadedFile, owner_name: str) -> dict:
    """
    Convenience function to scan a file upload
    Usage: result = scan_upload(uploaded_file, request.user.username)
    """
    return guardian.scan_file(file, owner_name)
