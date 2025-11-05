# ⚡ Quick Test Guide - DataFlow AI Redesign

## 🚀 **START COMMANDS**

### **1. Start Backend (Terminal 1):**
```bash
cd /workspace
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### **2. Start Frontend (Terminal 2):**
```bash
cd /workspace
npm run dev
```

### **3. Open Browser:**
```
http://localhost:5173
```

---

## ✅ **QUICK VERIFICATION CHECKLIST**

### **Dashboard (Home) - 30 seconds**
- [ ] See 4 metric cards with real numbers (no "Cost Savings")
- [ ] Activity feed shows real timestamps
- [ ] Platform insights section visible
- [ ] All neon effects visible (glowing borders)

### **Navigation Sidebar - 10 seconds**
- [ ] Only 4 tabs visible: Dashboard, Clean Data, Convert SQL, Smart Analytics
- [ ] NO "Activity" or "Settings" tabs
- [ ] Smart Analytics has sparkles ✨ icon

### **Smart Analytics Tab ⭐ - 60 seconds**
- [ ] Click "Smart Analytics" in sidebar
- [ ] See 4 main sections:
  1. Query Optimizer (top left) - heatmap visible
  2. Anomaly Detector (top right) - purple card
  3. Activity Intelligence (middle) - lime green card
  4. Performance Insights (bottom) - cyan card
- [ ] All cards have neon glow effects
- [ ] Hover over cards to see glow increase

### **Clean Data Tab - 20 seconds**
- [ ] Upload a CSV file
- [ ] Check dashboard activity feed for new upload entry
- [ ] Unchanged from before (as required)

### **Convert SQL Tab - 20 seconds**
- [ ] Paste a SQL query
- [ ] Convert to different dialect
- [ ] Unchanged from before (as required)

---

## 🎨 **VISUAL CHECKS**

### **Neon Effects Present:**
- [ ] Gradient text on page titles
- [ ] Glowing card borders (cyan, purple, lime)
- [ ] Pulsing animations on alerts
- [ ] Neon badges with colored borders
- [ ] Icon glow effects
- [ ] Hover effects work smoothly

### **No Mock Data:**
- [ ] Dashboard shows real quality score
- [ ] No "Cost Savings" metric anywhere
- [ ] Activity feed has real timestamps
- [ ] File counts are accurate

---

## 🐛 **TROUBLESHOOTING**

### **Backend Not Starting:**
```bash
# Check if port 8000 is in use
lsof -i :8000

# Install dependencies if needed
pip install -r requirements.txt
```

### **Frontend Not Starting:**
```bash
# Reinstall dependencies
rm -rf node_modules
npm install
npm run dev
```

### **Neon Effects Not Showing:**
- [ ] Check browser console for errors
- [ ] Verify `/src/styles/neon.css` exists
- [ ] Check `/src/main.tsx` imports neon.css

### **API Errors:**
- [ ] Verify backend is running on http://localhost:8000
- [ ] Check `/docs` endpoint: http://localhost:8000/docs
- [ ] Look for Smart Analytics endpoints in docs

---

## ✨ **SUCCESS INDICATORS**

### **You Know It's Working When:**
1. ✅ Navigation shows exactly 4 tabs (no Monitoring/Settings)
2. ✅ Smart Analytics page loads with glowing purple/cyan/lime cards
3. ✅ Dashboard activity feed shows real data entries
4. ✅ Hovering over cards makes them glow brighter
5. ✅ No "Cost Savings" or mock data anywhere

---

## 📱 **MOBILE TEST (Optional)**

1. Resize browser window to mobile size
2. Check navigation menu (hamburger icon)
3. Verify neon effects still visible
4. Cards should stack vertically

---

## 🎯 **DEMO PREPARATION**

### **Before Demonstrating:**
1. Upload 2-3 files to Clean Data tab
2. Convert 1-2 SQL queries
3. Refresh dashboard to see activities
4. Navigate to Smart Analytics
5. Show neon hover effects

### **Demo Script (2 minutes):**
1. "Dashboard shows real metrics - no mock data"
2. "Activity feed tracks all platform actions"
3. "Smart Analytics provides AI insights" (show each section)
4. "Neon aesthetic makes it visually distinctive" (hover demo)
5. "All three features integrated seamlessly"

---

## 🔗 **USEFUL URLS**

- Frontend: http://localhost:5173
- Backend API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

---

## ✅ **FINAL CHECK**

Run this command in browser console to verify no errors:
```javascript
console.log("Check for red errors above - should be none!");
```

---

**Total Test Time: ~3 minutes**  
**Status: Ready to impress! 🚀**
