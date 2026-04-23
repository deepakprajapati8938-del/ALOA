"""
Error Detector for ALOA
Monitors system anomalies.
"""

class ErrorDetector:
    def check_for_errors(self, operation: str, result: any) -> bool:
        if isinstance(result, Exception):
            print(f"Error detected in {operation}: {result}")
            return True
        return False

error_detector = ErrorDetector()
