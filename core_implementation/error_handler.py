"""
Error Handler for ALOA
Provides generic fallback methods for errors.
"""

class ErrorHandler:
    def handle_error(self, operation: str, error: Exception):
        print(f"Handling error in {operation}: {error}")
        return {"status": "error", "message": str(error)}

error_handler = ErrorHandler()
