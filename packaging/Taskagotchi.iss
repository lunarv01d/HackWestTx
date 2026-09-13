#define MyAppName "Taskagotchi"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Taskagotchi"
#define MyAppExeName "Taskagotchi.exe"

[Setup]
AppId={{7997A8D7-483E-4C45-A57D-9F462FD11E5D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\Taskagotchi
DefaultGroupName=Taskagotchi
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=..\dist\installer
OutputBaseFilename=Taskagotchi-Setup-Windows-x64
SetupIconFile=Taskagotchi.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Files]
Source: "..\dist\Taskagotchi\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\Taskagotchi"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\Taskagotchi"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch Taskagotchi"; Flags: nowait postinstall skipifsilent
