[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
AppId={{A1B2C3D4-E5F6-7G8H-9I0J-K1L2M3N4O5P6}}
AppName=Peak Finder Pro
AppVersion=1.0.0
AppPublisher=Dhruv Makwana
AppPublisherURL=https://github.com/Dhruv-mak/peak_find
AppSupportURL=https://github.com/Dhruv-mak/peak_find/issues
AppUpdatesURL=https://github.com/Dhruv-mak/peak_find/releases
DefaultDirName={autopf}\Peak Finder Pro
DefaultGroupName=Peak Finder Pro
AllowNoIcons=yes
LicenseFile=
InfoBeforeFile=
InfoAfterFile=
OutputDir=installer
OutputBaseFilename=PeakFinderPro-Setup
SetupIconFile=icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1

[Files]
Source: "dist\PeakFinderPro\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{group}\Peak Finder Pro"; Filename: "{app}\PeakFinderPro.exe"; IconFilename: "{app}\icon.ico"
Name: "{group}\{cm:UninstallProgram,Peak Finder Pro}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Peak Finder Pro"; Filename: "{app}\PeakFinderPro.exe"; IconFilename: "{app}\icon.ico"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\Peak Finder Pro"; Filename: "{app}\PeakFinderPro.exe"; IconFilename: "{app}\icon.ico"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\PeakFinderPro.exe"; Description: "{cm:LaunchProgram,Peak Finder Pro}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
