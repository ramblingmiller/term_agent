import os
import sys
import uvicorn

from api.api_server import app

def main():
    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        print("Usage: python term_api.py")
        sys.exit(0)
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    uvicorn.run(app, host=host, port=port, log_level="info")

if __name__ == "__main__":
    main()
