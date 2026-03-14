# ForensiClear

Restore clarity. Preserve integrity.

ForensiClear is a production-style MVP for lawful forensic-style image restoration. It preserves the original upload, runs a classical computer-vision enhancement pipeline, generates a structured audit log, and lets reviewers compare the original against the enhanced result before exporting files.

## What the app does

- Uploads JPG, JPEG, PNG, and WEBP images
- Preserves the original source file untouched
- Applies denoising, conservative deblurring, optional edge sharpening, gentle contrast enhancement, and optional 2x upscale
- Supports an evidence-safe mode that limits aggressive processing
- Creates immutable processing runs so one job can be processed multiple times without overwriting prior outputs
- Uses signed preview and download URLs instead of public static artifact exposure
- Queues processing through a bounded worker pool and reports live run phases to the frontend
- Stores job and run metadata in SQLite for ownership-aware history and persistence across restarts
- Protects upload and processing endpoints with bearer API-key authentication
- Exposes authenticated queue metrics for worker/throughput visibility
- Displays before/after comparison with split-view and side-by-side modes
- Exports the restored image and its audit log JSON

## Tech stack

### Frontend

- React with Vite
- Tailwind CSS
- Axios
- React Dropzone
- Framer Motion

### Backend

- FastAPI
- Uvicorn
- OpenCV
- NumPy
- Pillow
- scikit-image
- SQLite

## Project structure

```text
deblurring/
  backend/
  frontend/
  README.md
```

## Run the backend

1. Create and activate a Python virtual environment.
2. Install dependencies:

```bash
cd backend
pip install -r requirements.txt
```

3. Copy `backend/.env.example` into your shell environment or set the variables manually. At minimum configure:

```bash
set FORENSICLEAR_API_KEYS=analyst-dev:change-me-dev-key
set FORENSICLEAR_SIGNING_SECRET=replace-this-with-a-long-random-secret
set FORENSICLEAR_WORKER_COUNT=2
set FORENSICLEAR_QUEUE_MAX_SIZE=12
```

4. Start the FastAPI server:

```bash
uvicorn app.main:app --reload
```

5. Open the API at `http://localhost:8000` or the docs at `http://localhost:8000/docs`.

## Run the frontend

1. Install dependencies:

```bash
cd frontend
npm install
```

2. Optionally copy `frontend/.env.example` to `.env` and adjust the backend URL if needed.
3. Start the Vite dev server:

```bash
npm run dev
```

4. Open the app at `http://localhost:5173`.

## Example workflow

1. Start the backend and frontend locally.
2. Enter the configured bearer API key in the Access Control panel.
3. Drag in a supported image and confirm the source is preserved.
4. Choose denoise, deblur, sharpen, upscale, and evidence-safe settings.
5. Start a processing run. The UI will queue the run and poll status until it completes or fails.
6. Review the preserved original and the completed enhanced output in the comparison panel.
7. Inspect the structured audit log for that specific run and review the Recent Jobs history panel.
8. Download the restored image and the log JSON for that run.

## API endpoints

- `GET /health`
- `GET /auth/me`
- `GET /auth/jobs`
- `GET /ops/metrics`
- `POST /upload`
- `POST /process/{job_id}`
- `GET /process/{job_id}/{run_id}`
- `GET /preview/original/{job_id}`
- `GET /preview/restored/{job_id}/{run_id}`
- `GET /download/image/{job_id}/{run_id}`
- `GET /download/log/{job_id}/{run_id}`

## Tests

Install the backend dev dependencies and run:

```bash
cd backend
pip install -r requirements-dev.txt
pytest
```

## Forensic integrity disclaimer

ForensiClear is designed for lawful enhancement and visibility improvement. Enhanced outputs may improve readability or inspection quality, but they do not represent guaranteed recovery of exact lost detail. Always retain the original upload, disclose enhancement steps, and avoid treating reconstructed visibility as certainty.
