# Streamlit Community Cloud Deployment Checklist

**Project:** Water-Opt MVP Dashboard
**Target:** Streamlit Community Cloud (Free Tier)
**Last Updated:** 2025-10-15

---

## Prerequisites

- [ ] GitHub account (required for Streamlit Cloud)
- [ ] Git repository pushed to GitHub
- [ ] Working Streamlit app locally tested

---

## Phase 1: Prepare Your Repository

### 1.1 Verify Requirements File
- [ ] Confirm `requirements.txt` exists in project root
- [ ] Verify all dependencies are listed with versions (optional but recommended)
- [ ] Test locally: `pip install -r requirements.txt`

### 1.2 Create Streamlit Configuration Files

- [ ] Create `.streamlit/` directory in project root
- [ ] Add `.streamlit/config.toml` for app configuration
- [ ] Add `.streamlit/secrets.toml.example` as template (DO NOT commit actual secrets)

### 1.3 Prepare Data Files

**Option A: Commit Data Files (Simple)**
- [ ] Run `make etl` to generate all data files
- [ ] Verify data files exist in `data/stage/` and `data/mart/`
- [ ] Update `.gitignore` to ALLOW data files (remove `data/` from gitignore if present)
- [ ] Commit data files to repository

**Option B: Fetch on Startup (Advanced)**
- [ ] Create `startup.sh` script to run ETL on deployment
- [ ] Update `Main.py` to check for data and fetch if missing
- [ ] Add API keys to Streamlit secrets

**Recommendation:** Use Option A for MVP (simpler, faster startup)

### 1.4 Add README for Streamlit Cloud

- [ ] Create or update `README.md` with:
  - Project description
  - Link to live demo (add after deployment)
  - Local setup instructions
  - Data sources attribution

### 1.5 Push to GitHub

- [ ] Commit all changes
- [ ] Push to GitHub: `git push origin main`
- [ ] Verify repository is public (or upgrade Streamlit plan for private repos)

---

## Phase 2: Set Up Streamlit Community Cloud

### 2.1 Create Streamlit Account

- [ ] Go to [share.streamlit.io](https://share.streamlit.io)
- [ ] Click **"Sign up"** or **"Continue with GitHub"**
- [ ] Authorize Streamlit to access your GitHub account
- [ ] Complete email verification if prompted

### 2.2 Connect GitHub Repository

- [ ] Click **"New app"** button (top right)
- [ ] Select your GitHub repository: `WaterProj` (or your repo name)
- [ ] Configure deployment settings:
  - **Branch:** `main` (or your default branch)
  - **Main file path:** `app/Main.py`
  - **App URL:** Choose subdomain (e.g., `water-opt-dashboard`)

### 2.3 Configure Environment (if needed)

- [ ] Click **"Advanced settings"** (optional)
- [ ] Add environment variables/secrets if using API keys:
  - `NASS_API_KEY` (if fetching NASS data)
  - `CIMIS_APP_KEY` (if fetching CIMIS data)
- [ ] Set Python version (default 3.10 should work)

### 2.4 Deploy

- [ ] Click **"Deploy!"** button
- [ ] Wait for build process (3-5 minutes first time)
- [ ] Monitor logs for any errors

---

## Phase 3: Verify Deployment

### 3.1 Test the Live App

- [ ] Open your app URL: `https://[your-subdomain].streamlit.app`
- [ ] Navigate through all tabs:
  - [ ] Setup tab loads and sliders work
  - [ ] Hydrology tab displays data (or shows warning)
  - [ ] Markets tab displays data (or shows warning)
  - [ ] Decision tab calculates correctly
  - [ ] Map tab displays rice polygons (or shows warning)
  - [ ] Compliance tab loads correctly
- [ ] Test calculations with different parameter values
- [ ] Verify charts render properly
- [ ] Test export functionality

### 3.2 Check Data Status

- [ ] In sidebar, expand "Data Status"
- [ ] Verify which data sources are available:
  - [ ] AWDB SWE
  - [ ] Bulletin 120
  - [ ] ERS Prices
  - [ ] DWR Crop Map
  - [ ] CIMIS ETo (optional)

### 3.3 Test Mobile Responsiveness (Optional)

- [ ] Open app on mobile device or use browser dev tools
- [ ] Verify layout is usable on smaller screens

---

## Phase 4: Integrate with Your Website

### 4.1 Get Your App URL

- [ ] Copy your live app URL from Streamlit dashboard
- [ ] Example: `https://water-opt-dashboard.streamlit.app`

### 4.2 Embed in Your Website

**Option A: Direct Link**
- [ ] Add link to your website navigation
- [ ] Example HTML:
  ```html
  <a href="https://water-opt-dashboard.streamlit.app" target="_blank">
    Water-Opt Dashboard
  </a>
  ```

**Option B: Iframe Embed** (Recommended)
- [ ] Add iframe to your website:
  ```html
  <iframe
    src="https://water-opt-dashboard.streamlit.app"
    width="100%"
    height="800px"
    frameborder="0"
    style="border: none; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
  </iframe>
  ```
- [ ] Test iframe on your website
- [ ] Adjust height as needed for your layout

**Option C: Embedded Component with Expand Button**
- [ ] Add "?embed=true" to URL for cleaner embed
- [ ] Example:
  ```html
  <iframe
    src="https://water-opt-dashboard.streamlit.app?embed=true"
    width="100%"
    height="800px"
    frameborder="0">
  </iframe>
  ```

### 4.3 Add Attribution

- [ ] Add description on your website:
  - Project name
  - Brief description of what it does
  - Link to GitHub repository
  - Data sources acknowledgment

---

## Phase 5: Maintenance & Updates

### 5.1 Set Up Automatic Updates

- [ ] Streamlit Cloud auto-deploys on every push to `main` branch
- [ ] Verify auto-deploy is enabled in Streamlit settings
- [ ] Test by making a small change and pushing

### 5.2 Monitor App Health

- [ ] Check Streamlit Cloud dashboard regularly
- [ ] Monitor app logs for errors
- [ ] Set up email notifications (in Streamlit settings)

### 5.3 Update Data Periodically

**If data files are committed:**
- [ ] Schedule regular ETL runs: `make etl`
- [ ] Commit updated data files
- [ ] Push to GitHub (triggers auto-redeploy)

**If data is fetched on startup:**
- [ ] Verify API keys are still valid
- [ ] Check data source URLs haven't changed

### 5.4 Handle Breaking Changes

- [ ] Subscribe to Streamlit changelog
- [ ] Test locally before pushing major changes
- [ ] Keep dependencies up to date: `pip list --outdated`

---

## Phase 6: Optional Enhancements

### 6.1 Custom Domain (Optional)

- [ ] Upgrade to Streamlit paid plan (~$250/month for custom domains)
- [ ] Configure DNS settings
- [ ] Add CNAME record pointing to Streamlit

### 6.2 Analytics (Optional)

- [ ] Add Google Analytics to your website (will track iframe views)
- [ ] Use Streamlit's built-in analytics dashboard
- [ ] Track user engagement and popular features

### 6.3 Share & Promote

- [ ] Share app URL on LinkedIn/Twitter
- [ ] Add to portfolio/resume
- [ ] Submit to Streamlit Gallery (community showcase)

---

## Troubleshooting Common Issues

### App Won't Deploy

**Problem:** Build fails during deployment

**Solutions:**
- [ ] Check logs in Streamlit Cloud dashboard
- [ ] Verify `requirements.txt` has correct package names
- [ ] Ensure `Main.py` path is correct: `app/Main.py`
- [ ] Check Python version compatibility

### Missing Data

**Problem:** Data files not found, warnings shown

**Solutions:**
- [ ] Verify data files are committed and pushed to GitHub
- [ ] Check `.gitignore` isn't excluding data directories
- [ ] Run `git status` to see if files are tracked
- [ ] If using Option B, verify ETL runs successfully on startup

### Slow Performance

**Problem:** App is slow or unresponsive

**Solutions:**
- [ ] Optimize data loading (use `@st.cache_data` decorator)
- [ ] Reduce data file sizes (filter unnecessary rows/columns)
- [ ] Consider upgrading Streamlit plan for more resources
- [ ] Optimize chart rendering (reduce data points)

### Embedding Issues

**Problem:** Iframe doesn't display correctly

**Solutions:**
- [ ] Check if your website blocks iframes (CSP headers)
- [ ] Try adding `?embed=true` to URL
- [ ] Adjust iframe height to fit content
- [ ] Test in different browsers

### API Key Issues

**Problem:** External data sources fail to fetch

**Solutions:**
- [ ] Add API keys to Streamlit secrets (Settings > Secrets)
- [ ] Use format: `KEY_NAME = "value"` (TOML format)
- [ ] Restart app after adding secrets
- [ ] Verify keys are valid and not expired

---

## Success Criteria

- [x] App deploys successfully on Streamlit Cloud
- [x] All tabs load without critical errors
- [x] Data visualizations display correctly
- [x] Calculations produce reasonable results
- [x] App is accessible via public URL
- [x] Embedded successfully on your website
- [x] No console errors or warnings

---

## Resources

- **Streamlit Cloud Docs:** https://docs.streamlit.io/streamlit-community-cloud
- **Deployment Guide:** https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app
- **Secrets Management:** https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app/secrets-management
- **App Settings:** https://docs.streamlit.io/streamlit-community-cloud/manage-your-app
- **Community Forum:** https://discuss.streamlit.io/

---

## Notes

- **Cost:** Streamlit Community Cloud is **FREE** for public repositories
- **Limits:** 1GB RAM, 1 CPU core, community support only
- **Uptime:** Community tier has no SLA (may sleep after inactivity)
- **Private Repos:** Requires paid plan (~$20/month per user)

---

**Estimated Time:** 30-60 minutes for first deployment

**Status:** Ready to deploy once checklist is complete
