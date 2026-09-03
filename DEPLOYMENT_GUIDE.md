# NIRIKSHAN — Production Deployment Guide
**Problem Statement Reference**: SIH26034  
**Target Architecture**: Next.js 14 Frontend on **Vercel** + FastAPI Backend on **Dedicated Container / PaaS** (Render / Railway / Fly.io / Docker VPS)

---

## 1. Architecture Overview

```
 [ Officers / Public Verify ]
              |
              v (HTTPS)
   +-----------------------+
   |   Vercel Edge CDN     |  ---> Next.js 14 Frontend (App Router, Tailwind CSS)
   | nirikshan.vercel.app  |
   +-----------+-----------+
               |
               | (REST API over HTTPS)
               v
   +-----------------------+
   |   PaaS / Docker VPS   |  ---> FastAPI (Python 3.11, RapidOCR, OpenCV, ReportLab)
   | nirikshan-api.example |
   +-----------+-----------+
               |
               v (Persistent Volume Mount)
   +-----------------------+
   |   Persistent Disk     |  ---> SQLite WAL DB, Evidence Images, Signed PDF Reports
   +-----------------------+
```

---

## 2. Step 1: Deploying the FastAPI Backend

The backend requires a persistent environment with Python 3.11 and system dependencies for OpenCV/ONNX.

### Option A: Deploying on Render (Recommended Managed PaaS)

1. **Sign up / Log in to Render**: [https://render.com](https://render.com).
2. **Create New Web Service**:
   - Select **Build and deploy from a Git repository**.
   - Connect your GitHub repository: `https://github.com/rajputjay00/SIH26034.git`.
3. **Configure Service Settings**:
   - **Name**: `nirikshan-backend-api`
   - **Region**: Singapore / India (or nearest to users)
   - **Environment**: `Docker` (Render will automatically detect the root `Dockerfile`)
   - **Instance Type**: Starter (or higher)
4. **Configure Environment Variables**:
   In the **Environment** tab, set:
   ```env
   ENVIRONMENT=production
   DEBUG=False
   SECRET_KEY=generate-a-strong-64-character-random-hex-string
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=1440
   DATABASE_URL=sqlite:///./legalmetrix.db
   ALLOWED_ORIGINS=https://your-frontend-domain.vercel.app,http://localhost:3000
   FRONTEND_URL=https://your-frontend-domain.vercel.app
   REPORT_VERIFICATION_BASE_URL=https://your-frontend-domain.vercel.app/verify
   STORAGE_EVIDENCE_PATH=storage/evidence
   STORAGE_DERIVED_PATH=storage/derived
   STORAGE_REPORTS_PATH=storage/reports
   ```
5. **Attach Persistent Disk (Critical for Storage & SQLite)**:
   - Navigate to **Disks** $\rightarrow$ **Add Disk**.
   - **Mount Path**: `/app/storage`
   - **Size**: `5 GB` (or as required)
6. **Deploy**:
   - Click **Create Web Service**.
   - Render will build the container and provide your live HTTPS Backend URL:
     $$\text{Example: } \texttt{https://nirikshan-backend-api.onrender.com}$$

---

### Option B: Deploying via Docker on any Linux VPS / AWS EC2

1. **SSH into your server** and install Docker & Docker Compose:
   ```bash
   sudo apt-get update && sudo apt-get install -y docker.io docker-compose
   ```
2. **Clone the repository**:
   ```bash
   git clone https://github.com/rajputjay00/SIH26034.git
   cd SIH26034
   ```
3. **Create production `.env`**:
   ```bash
   cp backend/.env.example .env
   nano .env
   # Set ENVIRONMENT=production, DEBUG=False, SECRET_KEY, and ALLOWED_ORIGINS
   ```
4. **Build and start the container**:
   ```bash
   docker build -t nirikshan-backend:latest .
   docker run -d \
     --name nirikshan-backend \
     --restart always \
     -p 8000:8000 \
     -v $(pwd)/storage:/app/storage \
     -v $(pwd)/legalmetrix.db:/app/legalmetrix.db \
     --env-file .env \
     nirikshan-backend:latest
   ```
5. **Setup Nginx Reverse Proxy with SSL (Certbot / Let's Encrypt)** for HTTPS.

---

## 3. Step 2: Deploying the Next.js Frontend to Vercel

1. **Log in to Vercel**: [https://vercel.com](https://vercel.com).
2. **Add New Project**:
   - Click **Add New...** $\rightarrow$ **Project**.
   - Import your GitHub repository: `rajputjay00/SIH26034`.
3. **Configure Project Settings**:
   - **Framework Preset**: `Next.js`
   - **Root Directory**: Select `frontend` (Click **Edit** and choose `frontend`).
4. **Configure Environment Variables**:
   Under **Environment Variables**, add:
   ```env
   NEXT_PUBLIC_APP_NAME="NIRIKSHAN — Legal Metrology Compliance & Inspection System"
   NEXT_PUBLIC_API_URL="https://nirikshan-backend-api.onrender.com"
   ```
   *(Replace with your actual deployed backend HTTPS URL from Step 1).*
5. **Deploy**:
   - Click **Deploy**.
   - Vercel will run `npm run build` and output your live production URL:
     $$\text{Example: } \texttt{https://sih26034.vercel.app}$$

---

## 4. Step 3: Synchronize Production CORS Configuration

Now that you have your live Vercel URL (e.g. `https://sih26034.vercel.app`):
1. Go back to your backend host (e.g. Render Dashboard $\rightarrow$ Environment Variables).
2. Update `ALLOWED_ORIGINS`:
   ```env
   ALLOWED_ORIGINS="https://sih26034.vercel.app,http://localhost:3000"
   FRONTEND_URL="https://sih26034.vercel.app"
   REPORT_VERIFICATION_BASE_URL="https://sih26034.vercel.app/verify"
   ```
3. Save changes. The backend will restart and accept cross-origin requests from your Vercel deployment.

---

## 5. Step 4: End-to-End Production Verification

Run through this post-deployment verification checklist:

1. **Backend Health Check**:
   - Open `https://your-backend-api.example/api/v1/health` in browser.
   - Verify JSON response: `{"status": "HEALTHY", "subsystems": {"rule_engine": "READY", "ocr_engine": "READY", "audit_chain": "ONLINE"}}`.
2. **Frontend Loading**:
   - Navigate to `https://your-frontend.vercel.app`.
   - Verify the top utility bar displays the green **"Online"** system status badge.
3. **Create Inspection**:
   - Click **+ Start Inspection**.
   - Enter commodity notes and click **Initialize & Capture Photo**.
4. **Evidence Ingestion & Perception**:
   - Upload or photograph packaging panels.
   - Click **Run OCR & Extract Declarations**.
   - Confirm RapidOCR parses commodity name, net quantity, MRP, and manufacturer address.
5. **Deterministic Rule Evaluation**:
   - Click **Evaluate Statutory Rules**.
   - Review pass/fail determinations and arithmetic breakdowns.
6. **Finalize & PDF Verification**:
   - Submit authoritative final determination.
   - Click **Download PDF Report**. Verify header, SHA-256 digest, and QR code.
   - Scan QR code or open `/verify/<report_id>` to confirm cryptographic authenticity.

---

## 6. Common Deployment Errors & Troubleshooting

| Issue / Error | Root Cause | Solution |
| :--- | :--- | :--- |
| **CORS Error in Browser Console** (`Blocked by CORS policy`) | Frontend origin is missing from backend `ALLOWED_ORIGINS`. | Add exact frontend URL (including `https://`, no trailing slash) to `ALLOWED_ORIGINS` in backend environment settings. |
| **Mixed Content Warning / Failed Fetch** | Frontend is HTTPS, but `NEXT_PUBLIC_API_URL` is set to `http://`. | Ensure backend is served over SSL (`https://`). |
| **Missing `libGL.so.1` in Docker Logs** | OpenCV requires Linux system graphics libraries. | Use the provided production `Dockerfile` which installs `libgl1`, `libglib2.0-0`, and `libgomp1`. |
| **Data / Cases Lost on Backend Restart** | Backend deployed on ephemeral storage without persistent disk mount. | Attach a persistent disk volume to `/app/storage` (Render / Docker volume). |
| **401 Unauthorized Loop** | JWT secret key mismatch or expired token. | Ensure `SECRET_KEY` is consistent across restarts; frontend automatically refreshes expired sessions. |

---

## 7. Rollback & Maintenance Procedure

### Frontend Rollback (Vercel):
1. In the Vercel Dashboard, go to **Deployments**.
2. Select the previous stable deployment.
3. Click the **...** menu $\rightarrow$ **Instant Rollback**.

### Backend Rollback:
1. Re-deploy the previous commit hash in your Git repository or revert the container tag:
   ```bash
   git revert HEAD
   git push origin main
   ```
2. Database backups can be restored from the daily SQLite WAL snapshot in `storage/backups/`.
