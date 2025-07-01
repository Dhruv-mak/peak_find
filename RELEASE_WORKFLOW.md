# Release Workflow Summary

## ✅ **Updated Workflow Features**

### **1. Trigger Changes**
- **Primary**: Only runs when you create a GitHub release
- **Secondary**: Manual trigger available for testing (debug mode off by default)
- **Removed**: No longer runs on push/PR (only on releases)

### **2. Automatic Versioning**
- **Release builds**: Uses the release tag as version (e.g., `v1.2.3` becomes `1.2.3`)
- **Manual builds**: Uses timestamp format (`dev-20250701-1430`)
- **Auto-updates**: 
  - `AppVersion=1.2.3` in setup.iss
  - `OutputBaseFilename=PeakFinderPro-Setup-v1.2.3`
  - ZIP filename: `PeakFinderPro-Portable-v1.2.3.zip`

### **3. Release Integration**
- **Artifacts**: Include version in names for easy identification
- **Release assets**: Automatically attached to GitHub releases
- **File naming**: Consistent versioning across all outputs

## 🚀 **How to Use**

### **Creating a Release Build**
1. **Create a new release** in GitHub:
   - Go to "Releases" → "Create a new release"
   - Create a tag (e.g., `v1.0.0`, `v2.1.3`)
   - Add release notes
   - Click "Publish release"

2. **Workflow automatically runs** and creates:
   - `PeakFinderPro-Portable-v1.0.0.zip`
   - `PeakFinderPro-Setup-v1.0.0.exe`

3. **Files are attached** to your release automatically

### **Testing (Manual Trigger)**
- Go to Actions → "Build Executable and Installer on Release"
- Click "Run workflow"
- Choose debug mode if needed
- Creates timestamped development builds

## 📦 **Output Files**

### **For Release v1.2.3:**
- **Portable**: `PeakFinderPro-Portable-v1.2.3.zip`
- **Installer**: `PeakFinderPro-Setup-v1.2.3.exe`
- **Location**: Attached to GitHub release + available as artifacts

### **For Manual Builds:**
- **Portable**: `PeakFinderPro-Portable-vdev-20250701-1430.zip`
- **Installer**: `PeakFinderPro-Setup-vdev-20250701-1430.exe`
- **Location**: Available as artifacts only

## 🎯 **Benefits**

1. **Zero manual version management** - GitHub release tag controls everything
2. **Professional naming** - Version numbers in all files
3. **Clean release process** - Only runs when needed
4. **Automatic attachment** - Files appear in releases instantly
5. **Version tracking** - Easy to identify which version is which

## 🔧 **Configuration**

The workflow automatically:
- Extracts version from release tag (removes 'v' prefix)
- Updates `setup.iss` with correct version and filename
- Names all output files consistently
- Uploads to both artifacts and release assets

No manual editing of setup.iss needed for releases!
