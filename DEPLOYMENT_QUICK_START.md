# Quick Start: Deploy to Streamlit Cloud

**Goal:** Get your Water-Opt dashboard live in under 30 minutes!

---

## What You Need

1. GitHub account (free)
2. This repository pushed to GitHub
3. 30 minutes of your time

---

## Step-by-Step Instructions

### Step 1: Prepare Your Repository (5 minutes)

Your repository is already configured! These files are ready:
- `.streamlit/config.toml` - App configuration
- `.streamlit/secrets.toml.example` - Template for API keys
- Data files in `data/stage/` and `data/mart/`
- Updated `.gitignore` to include data files

**Action Required:**

```bash
# Add and commit the new files
git add .streamlit/ CHECKLIST_STREAMLIT.md DEPLOYMENT_QUICK_START.md
git add data/stage/ data/mart/
git add .gitignore docs/README.md

# Commit
git commit -m "Add Streamlit deployment configuration and data files"

# Push to GitHub
git push origin main
```

---

### Step 2: Create Streamlit Account (2 minutes)

1. Go to **[share.streamlit.io](https://share.streamlit.io)**
2. Click **"Continue with GitHub"**
3. Authorize Streamlit to access your GitHub account
4. Verify your email if prompted

---

### Step 3: Deploy Your App (3 minutes)

1. Click **"New app"** button (top right)
2. Fill in the deployment form:
   - **Repository:** Select your `WaterProj` repository
   - **Branch:** `main`
   - **Main file path:** `app/Main.py`
   - **App URL:** Choose a name like `water-opt-dashboard`
3. Click **"Deploy!"**

The app will now build (3-5 minutes). You'll see:
- Installing dependencies
- Starting app
- App is live!

---

### Step 4: Test Your App (5 minutes)

Your app will be live at: `https://[your-chosen-name].streamlit.app`

Test all tabs:
- [ ] Setup: Adjust sliders and inputs
- [ ] Hydrology: View SWE data and scenarios
- [ ] Markets: View price trends
- [ ] Decision: See profit comparison and recommendation
- [ ] Map: View rice field locations
- [ ] Compliance: Read regulatory information

---

### Step 5: Embed in Your Website (10 minutes)

#### Option A: Direct Link

Add to your website's navigation or portfolio section:

```html
<a href="https://your-app-name.streamlit.app"
   target="_blank"
   rel="noopener noreferrer">
  View Water-Opt Dashboard
</a>
```

#### Option B: Iframe Embed (Recommended)

Embed the full dashboard:

```html
<div style="max-width: 1200px; margin: 0 auto;">
  <h2>Water-Opt: Rice Growing Decision Tool</h2>
  <p>
    Interactive dashboard for California rice growers to compare
    profitability of growing rice vs. fallowing and selling water rights.
  </p>

  <iframe
    src="https://your-app-name.streamlit.app?embed=true"
    width="100%"
    height="800px"
    frameborder="0"
    style="border: none; border-radius: 8px;
           box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
  </iframe>

  <p style="margin-top: 1rem; font-size: 0.9rem; color: #666;">
    <a href="https://github.com/yourusername/WaterProj" target="_blank">
      View Source Code
    </a> |
    Built with Streamlit
  </p>
</div>
```

#### Tips for Embedding:
- Use `?embed=true` for cleaner appearance (hides Streamlit header)
- Adjust `height` to fit your layout (800-1000px recommended)
- Add responsive CSS for mobile devices
- Test on different browsers

---

## Troubleshooting

### Build Fails

**Problem:** "ModuleNotFoundError" or import errors

**Solution:**
1. Check `requirements.txt` has all dependencies
2. Verify Python version compatibility (3.10+)
3. Check logs in Streamlit dashboard

### Data Not Loading

**Problem:** "Data not available" warnings

**Solution:**
1. Verify data files are committed: `git ls-files data/`
2. Check `.gitignore` allows `data/stage/` and `data/mart/`
3. Push data files: `git push origin main`

### App is Slow

**Problem:** App takes long to load or respond

**Solution:**
- Data files are cached after first load
- Large GeoJSON file (~13MB) may take time initially
- Consider optimizing data files if needed

### Iframe Not Displaying

**Problem:** Blank iframe or "Connection refused"

**Solution:**
- Check if website blocks iframes (Content Security Policy)
- Verify app URL is correct
- Try adding `?embed=true` parameter
- Test in different browsers

---

## Next Steps

### Update Your App

Any time you push to GitHub, Streamlit auto-deploys:

```bash
# Make changes locally
git add .
git commit -m "Update dashboard"
git push origin main

# App redeploys automatically in 2-3 minutes
```

### Monitor Your App

- View logs in Streamlit dashboard
- Check analytics in Settings
- Set up email notifications for errors

### Optional Enhancements

- Add Google Analytics to track usage
- Create custom domain (requires paid plan)
- Share on social media / portfolio
- Submit to Streamlit Gallery

---

## Support

- **Detailed Guide:** See [CHECKLIST_STREAMLIT.md](CHECKLIST_STREAMLIT.md)
- **Streamlit Docs:** [docs.streamlit.io](https://docs.streamlit.io)
- **Community Forum:** [discuss.streamlit.io](https://discuss.streamlit.io)

---

## Summary Checklist

Before deploying:
- [ ] Git repository pushed to GitHub
- [ ] Data files committed (`data/stage/`, `data/mart/`)
- [ ] Streamlit config files added (`.streamlit/`)

To deploy:
- [ ] Create Streamlit account
- [ ] Deploy app (main file: `app/Main.py`)
- [ ] Test all tabs work
- [ ] Get your app URL

To embed:
- [ ] Add link or iframe to your website
- [ ] Test embedding works
- [ ] Add attribution/description

---

**Estimated Total Time:** 25-30 minutes

**Cost:** $0 (Free on Streamlit Community Cloud)

**You're ready to deploy! Good luck!**
