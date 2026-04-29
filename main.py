import uvicorn

if __name__ == "__main__":
    print("======================================")
    print("  QuDrop FastAPI Server Initializing  ")
    print("======================================")
    print("Starting backend. The frontend should connect to http://127.0.0.1:5001")
    uvicorn.run("server.app:app", host="0.0.0.0", port=5001, reload=True)
