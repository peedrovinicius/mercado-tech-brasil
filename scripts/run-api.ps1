$ErrorActionPreference = "Stop"
uvicorn src.api.main:app --reload
