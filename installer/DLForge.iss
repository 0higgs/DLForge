#define MyAppName "DLForge"
#define MyAppVersion "0.5.0"
#define MyAppPublisher "0higgs"
#define MyAppURL "https://github.com/0higgs/DLForge"

[Setup]
AppId={{8B6EF724-91A0-4EB7-9F91-56495DE138AB}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0.17763
WizardStyle=modern
WizardSmallImageFile=..\assets\dlforge-icon.png
Compression=lzma2/max
SolidCompression=yes
OutputDir=..\tmp\installer-output
OutputBaseFilename=DLForge-0.5.0-Setup-offline
LicenseFile=..\LICENSE
InfoBeforeFile=INSTALL_NOTICE_zh-CN.txt
#ifndef UseDefaultSetupIcon
SetupIconFile=..\assets\dlforge.ico
#endif
UninstallDisplayIcon={app}\DLForge.ico
CloseApplications=yes
RestartApplications=no
SetupMutex=DLForgeSetupMutex
AppMutex=DLForgeAppMutex

[Languages]
Name: "chinesesimplified"; MessagesFile: "ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加任务："; Flags: unchecked

[Files]
Source: "..\dist\DLForge\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\assets\dlforge.ico"; DestDir: "{app}"; DestName: "DLForge.ico"; Flags: ignoreversion
Source: "ChineseSimplified.LICENSE"; DestDir: "{app}\licenses"; DestName: "Inno-Setup-Chinese-Translation-MIT.txt"; Flags: ignoreversion

[Icons]
Name: "{group}\DLForge"; Filename: "{app}\DLForge.exe"; WorkingDir: "{app}"; IconFilename: "{app}\DLForge.ico"
Name: "{autodesktop}\DLForge"; Filename: "{app}\DLForge.exe"; WorkingDir: "{app}"; IconFilename: "{app}\DLForge.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\DLForge.exe"; Description: "启动 DLForge"; Flags: nowait postinstall skipifsilent
