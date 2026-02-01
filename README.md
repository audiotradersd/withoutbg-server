# withoutbg Background Removal Server

A REST API server for free, unlimited background removal using the open-source [withoutbg](https://github.com/withoutbg/withoutbg) library.

## Deployment Options

### Option 1: Railway.app (Recommended - Free Tier)

1. Push this folder to GitHub
2. Go to [railway.app](https://railway.app) and create new project
3. Select "Deploy from GitHub repo"
4. Pick this folder, Railway auto-detects Python
5. Copy the deployment URL (e.g., `https://withoutbg-server-xxxx.up.railway.app`)
6. Configure Prism: `wrangler secret put WITHOUTBG_SERVER_URL`

### Option 2: Render.com (Free Tier)

1. Push this folder to GitHub
2. Go to [render.com](https://render.com) and create new Web Service
3. Connect your repo, select this folder
4. It uses `render.yaml` for config
5. Copy the URL and configure Prism

### Option 3: Local + Cloudflare Tunnel

```bash
# Terminal 1: Run server
cd tools/withoutbg-server
pip install -r requirements.txt
python server.py

# Terminal 2: Expose via tunnel
cloudflared tunnel --url http://localhost:5000
# Copy URL: https://xxx-xxx.trycloudflare.com
```

### Option 4: Docker

```bash
docker build -t withoutbg-server .
docker run -p 5000:5000 withoutbg-server
```

## Configure Prism

After deployment, set the server URL:
```bash
cd /home/simondownes/Prism
wrangler secret put WITHOUTBG_SERVER_URL
# Enter your server URL (e.g., https://withoutbg-xxxx.up.railway.app)
```

## API Endpoints

### POST /remove-background

Remove background from an image.

**Request:**
```json
{
  "image_url": "https://example.com/photo.jpg"
}
```
or
```json
{
  "image_data": "base64-encoded-image-data"
}
```

**Response:**
```json
{
  "success": true,
  "image_data": "base64-encoded-png",
  "content_type": "image/png"
}
```

### GET /health

Health check endpoint.

## Performance

- First image: ~5-10 seconds (model loading)
- Subsequent images: ~2-5 seconds
- Memory usage: ~2GB RAM recommended
- Model size: ~320MB disk space

## Docker Alternative

Run with Docker instead of Python directly:

```bash
docker build -t withoutbg-server .
docker run -p 5000:5000 withoutbg-server
```

## Troubleshooting

**Model download fails**: Check internet connection, the model downloads from HuggingFace.

**Out of memory**: The model needs ~2GB RAM. Close other applications or use a machine with more memory.

**Slow processing**: GPU acceleration not currently supported in the open-source version. Processing is CPU-bound.
