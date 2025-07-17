import os

class Settings:
    PROCESSOR_DEFAULT_URL: str = os.getenv("PROCESSOR_DEFAULT_URL", "http://payment-processor-default:8080")
    PROCESSOR_FALLBACK_URL: str = os.getenv("PROCESSOR_FALLBACK_URL", "http://payment-processor-fallback:8080")

settings = Settings()