#define MyAppName "Orbix"
#define MyAppVersion "1.5.0"
#define MyAppPublisher "Orbix Vision"
#define MyAppURL "https://github.com/ADI-2707/Orbix"
#define MyAppExeName "Orbix.exe"

[Setup]
AppId={{9A2F4B38-6D71-4A59-86BC-52C8A8F2913A}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=..\dist
OutputBaseFilename=Orbix-Setup-v{#MyAppVersion}
SetupIconFile=..\packaging\icons\orbix.ico
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}
PrivilegesRequiredOverridesAllowed=commandline dialog

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\dist\Orbix\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\packaging\icons\orbix.ico"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{unins000}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\packaging\icons\orbix.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
