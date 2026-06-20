; Inno Setup script for epy_paper
; Version 0.1.0
;
; Build from the project root AFTER running `python build.py`:
;   ISCC.exe installer\windows\epy_paper.iss
;
; Output: installer\dist\epy_paper-setup-0.1.0.exe
;
; Design decisions:
;   - PrivilegesRequired=lowest  -> per-user install; no UAC prompt.
;     This is intentional: the file-association backend (winreg_assoc.py)
;     writes to HKCU, which requires the *installing* user's context.
;     A per-user install keeps the app directory, the registry work, and
;     the user account all consistent.
;   - DefaultDirName={localappdata}\Programs\epy_paper  -> conventional
;     location for user-scoped apps on Windows 10/11.
;   - Windows 10/11 UserChoice limitation:
;     Microsoft signs the UserChoice key with an undocumented HMAC that
;     only Windows itself can produce.  No installer or third-party app
;     can silently set a file-type default since Windows 8.  The
;     --as-default flag writes the *legacy* handler and the Capabilities
;     tree so the app appears in "Settings > Default apps".  The user
;     must open that Settings page and click "Set as default" for the
;     change to take effect in the UserChoice.
;
; Shared runtime option (see installer/SHARED_RUNTIME.md):
;   When epy_reports is already installed and its PySide6/Qt runtime
;   version matches the version bundled here, the installer offers to
;   share one copy of the ~150 MB _internal/ runtime under:
;     {localappdata}\Programs\epy_shared_runtime\<qt-version>\_internal\
;   A directory junction is placed at {app}\_internal pointing there.
;   A reference-count key in HKCU tracks consumers; the shared directory
;   is removed only when the last consumer uninstalls.

#define AppName "epy_paper"
#define AppVersion "0.1.0"
#define AppPublisher "Ing. Angel Navarro-Mora M.Sc."
#define AppURL "https://github.com/estructuraPy/epy_paper"
#define AppId "{{A3C1F8E5-4D72-4B91-8F0E-2A9B7D6C5E18}"
#define AppExeName "epy_paper.exe"
; Paths are relative to the location of this .iss file (installer\windows\).
#define DistDir "..\..\dist\epy_paper"
#define IconFile "..\..\assets_build\epy_paper.ico"
#define OutputDir "..\..\installer\dist"

[Setup]
AppId={#AppId}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}
DefaultDirName={localappdata}\Programs\{#AppName}
DefaultGroupName={#AppName}
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=commandline
OutputDir={#OutputDir}
OutputBaseFilename=epy_paper-setup-{#AppVersion}
SetupIconFile={#IconFile}
UninstallDisplayIcon={app}\{#AppExeName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
UsePreviousGroup=yes
DisableProgramGroupPage=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "opendefaults"; Description: "Open Windows Default Apps settings after install (to confirm epy_paper as default)"; GroupDescription: "File associations:"; Flags: unchecked

[Files]
; Main executable — always installed to {app}.
Source: "{#DistDir}\{#AppExeName}"; DestDir: "{app}"; Flags: ignoreversion

; PySide6/Qt _internal runtime tree.
; This entry always runs.  When the user opts in to runtime sharing, the
; [Code] section (CurStepChanged/ssPostInstall) will:
;   1. Delete the just-installed {app}\_internal directory.
;   2. Create a directory junction {app}\_internal -> shared location.
Source: "{#DistDir}\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; auto* constants resolve to the per-user folders when PrivilegesRequired=lowest.
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\{#AppExeName}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\{#AppExeName}"; Tasks: desktopicon

[Run]
; Register file associations in HKCU immediately after installation.
Filename: "{app}\{#AppExeName}"; Parameters: "--register --as-default"; \
    Flags: runascurrentuser nowait postinstall skipifsilent; \
    Description: "Register epy_paper for .md / .markdown files"

; Optional: open Windows Default Apps settings.
Filename: "{app}\{#AppExeName}"; Parameters: "--set-default"; \
    Flags: runascurrentuser nowait postinstall skipifsilent unchecked; \
    Description: "Open Windows Default Apps settings (confirm epy_paper as default)"; \
    Tasks: opendefaults

[UninstallRun]
; Remove registry keys when the user uninstalls.
Filename: "{app}\{#AppExeName}"; Parameters: "--unregister"; \
    RunOnceId: "UnregisterFileAssoc"; \
    Flags: runascurrentuser nowait

[Code]
// ---------------------------------------------------------------------------
// Shared PySide6/Qt runtime — wizard page and install/uninstall logic
//
// Approach: option (a) — shared versioned component directory + junction.
//
// Layout when sharing is active:
//   {localappdata}\Programs\epy_shared_runtime\<qt-ver>\_internal\
//   {localappdata}\Programs\epy_paper\_internal  <- JUNCTION -> above
//
// Refcount registry (HKCU\Software\epy_suite\shared_runtime):
//   qt_version  REG_SZ    "6.11.1.0"
//   refcount    REG_DWORD  2
//
// Sibling: epy_reports (must already be installed for sharing to work)
// ---------------------------------------------------------------------------

const
  SHARED_BASE_DIR = '\Programs\epy_shared_runtime';
  REFCOUNT_KEY    = 'Software\epy_suite\shared_runtime';

var
  GShareAvailable : Boolean;
  GQtVersion      : String;
  GSharedDir      : String;
  GUserChoseShare : Boolean;

  SharedRtPage    : TWizardPage;
  ShareCheckbox   : TCheckBox;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function GetQtVersionFromDll(const DllPath: String): String;
var
  VS: String;
begin
  Result := '';
  if FileExists(DllPath) then
    if GetVersionNumbersString(DllPath, VS) then
      Result := VS;
end;

function SharedInternalDir(const QtVer: String): String;
begin
  Result := GetEnv('LOCALAPPDATA') + SHARED_BASE_DIR + '\' + QtVer + '\_internal';
end;

function SharedBaseForVer(const QtVer: String): String;
begin
  Result := GetEnv('LOCALAPPDATA') + SHARED_BASE_DIR + '\' + QtVer;
end;

function SharedRoot: String;
begin
  Result := GetEnv('LOCALAPPDATA') + SHARED_BASE_DIR;
end;

function GetRegRefcount: Cardinal;
var V: Cardinal;
begin
  Result := 0;
  if RegQueryDWordValue(HKEY_CURRENT_USER, REFCOUNT_KEY, 'refcount', V) then
    Result := V;
end;

procedure SetRegRefcount(const Val: Cardinal);
begin
  RegWriteDWordValue(HKEY_CURRENT_USER, REFCOUNT_KEY, 'refcount', Val);
end;

function CopyDirViaRobocopy(const Src, Dst: String): Boolean;
var
  Params     : String;
  ResultCode : Integer;
begin
  Result    := False;
  ForceDirectories(Dst);
  Params := '"' + Src + '" "' + Dst + '" /E /COPY:DAT /R:2 /W:1 /NP /NFL /NDL /NJS /NJH';
  if Exec(ExpandConstant('{sys}\robocopy.exe'), Params, '', SW_HIDE,
          ewWaitUntilTerminated, ResultCode) then
    Result := (ResultCode >= 0) and (ResultCode <= 7);
end;

function CreateJunction(const LinkPath, TargetPath: String): Boolean;
var
  Params     : String;
  ResultCode : Integer;
begin
  Params := '/C mklink /J "' + LinkPath + '" "' + TargetPath + '"';
  Result := Exec(ExpandConstant('{sys}\cmd.exe'), Params, '', SW_HIDE,
                 ewWaitUntilTerminated, ResultCode) and (ResultCode = 0);
end;

function RemoveJunction(const LinkPath: String): Boolean;
var
  Params     : String;
  ResultCode : Integer;
begin
  if not DirExists(LinkPath) then begin Result := True; Exit; end;
  Params := '/C rmdir "' + LinkPath + '"';
  Result := Exec(ExpandConstant('{sys}\cmd.exe'), Params, '', SW_HIDE,
                 ewWaitUntilTerminated, ResultCode) and (ResultCode = 0);
end;

// ---------------------------------------------------------------------------
// Custom wizard page
// ---------------------------------------------------------------------------

procedure CreateSharedRtWizardPage;
var
  DescLabel : TLabel;
  NoteLabel : TLabel;
begin
  SharedRtPage := CreateCustomPage(
    wpSelectTasks,
    'Shared PySide6/Qt Runtime',
    'Reduce disk usage by sharing the runtime between epy_paper and epy_reports.'
  );

  DescLabel := TLabel.Create(SharedRtPage);
  DescLabel.Parent    := SharedRtPage.Surface;
  DescLabel.Left      := 0;
  DescLabel.Top       := 0;
  DescLabel.Width     := SharedRtPage.SurfaceWidth;
  DescLabel.AutoSize  := False;
  DescLabel.WordWrap  := True;
  DescLabel.Height    := 36;

  ShareCheckbox := TCheckBox.Create(SharedRtPage);
  ShareCheckbox.Parent  := SharedRtPage.Surface;
  ShareCheckbox.Left    := 0;
  ShareCheckbox.Top     := 44;
  ShareCheckbox.Width   := SharedRtPage.SurfaceWidth;
  ShareCheckbox.Height  := 20;
  ShareCheckbox.Caption := 'Share the PySide6/Qt runtime with epy_reports  (recommended)';

  NoteLabel := TLabel.Create(SharedRtPage);
  NoteLabel.Parent    := SharedRtPage.Surface;
  NoteLabel.Left      := 16;
  NoteLabel.Top       := 72;
  NoteLabel.Width     := SharedRtPage.SurfaceWidth - 16;
  NoteLabel.AutoSize  := False;
  NoteLabel.WordWrap  := True;
  NoteLabel.Height    := 120;

  if GShareAvailable then begin
    DescLabel.Caption :=
      'epy_reports is installed and uses the same Qt ' + GQtVersion +
      ' runtime as this version of epy_paper.';
    ShareCheckbox.Enabled := True;
    ShareCheckbox.Checked := True;
    NoteLabel.Caption :=
      'Observation: When enabled, a single ~150 MB copy of the PySide6/Qt ' +
      'runtime is installed to:' + #13#10 +
      '  ' + SharedInternalDir(GQtVersion) + #13#10 +
      'Each app''s _internal folder becomes a directory junction pointing there. ' +
      'Uninstalling one app removes its junction but leaves the shared runtime ' +
      'intact for the other app. The shared runtime is deleted automatically ' +
      'only when all apps that opted in have been uninstalled.' + #13#10 +
      'Uncheck to keep a self-contained ~150 MB runtime inside epy_paper only.';
  end else begin
    DescLabel.Caption :=
      'epy_reports is not installed or uses a different Qt version.';
    ShareCheckbox.Enabled := False;
    ShareCheckbox.Checked := False;
    NoteLabel.Caption :=
      'Observation: Runtime sharing is only available when both epy_paper ' +
      'and epy_reports are installed and built against the same PySide6/Qt ' +
      'version. To enable this option:' + #13#10 +
      '  1. Install epy_reports first.' + #13#10 +
      '  2. Re-run this installer — the checkbox will be available.' + #13#10 +
      'epy_paper will install its own self-contained ~150 MB runtime.';
  end;
end;

// ---------------------------------------------------------------------------
// Inno lifecycle hooks
// ---------------------------------------------------------------------------

procedure InitializeWizard;
var
  SiblingDll  : String;
  LocalDll    : String;
  SiblingVer  : String;
  LocalVer    : String;
begin
  GShareAvailable := False;
  GQtVersion      := '';
  GSharedDir      := '';
  GUserChoseShare := False;

  // Path to the sibling app's Qt6Core.dll (already installed).
  SiblingDll := GetEnv('LOCALAPPDATA') +
    '\Programs\epy_reports\_internal\PySide6\Qt6Core.dll';

  LocalDll := GetEnv('LOCALAPPDATA') +
    '\Programs\epy_paper\_internal\PySide6\Qt6Core.dll';

  SiblingVer := GetQtVersionFromDll(SiblingDll);

  if (SiblingVer <> '') then begin
    LocalVer := GetQtVersionFromDll(LocalDll);
    if LocalVer = '' then begin
      GShareAvailable := True;
      GQtVersion      := SiblingVer;
    end else if LocalVer = SiblingVer then begin
      GShareAvailable := True;
      GQtVersion      := SiblingVer;
    end;
  end;

  if GShareAvailable then
    GSharedDir := SharedInternalDir(GQtVersion);

  CreateSharedRtWizardPage;
end;

// ---------------------------------------------------------------------------
// Install-time: post-install step
// ---------------------------------------------------------------------------

procedure CurStepChanged(CurStep: TSetupStep);
var
  AppDir           : String;
  AppInternalDir   : String;
  InstalledSiblingDll : String;
  InstalledLocalDll   : String;
  SiblingVerCheck  : String;
  LocalVerCheck    : String;
  CurrentRefcount  : Cardinal;
  CopyOk           : Boolean;
  JunctionOk       : Boolean;
begin
  if CurStep <> ssPostInstall then Exit;

  GUserChoseShare := GShareAvailable and ShareCheckbox.Checked;

  if not GUserChoseShare then Exit;

  AppDir         := ExpandConstant('{app}');
  AppInternalDir := AppDir + '\_internal';

  InstalledSiblingDll := GetEnv('LOCALAPPDATA') +
    '\Programs\epy_reports\_internal\PySide6\Qt6Core.dll';
  InstalledLocalDll := AppInternalDir + '\PySide6\Qt6Core.dll';

  SiblingVerCheck := GetQtVersionFromDll(InstalledSiblingDll);
  LocalVerCheck   := GetQtVersionFromDll(InstalledLocalDll);

  if (SiblingVerCheck = '') or (LocalVerCheck = '') or
     (SiblingVerCheck <> LocalVerCheck) then begin
    MsgBox(
      'Shared runtime: version mismatch detected at install time.' + #13#10 +
      '  Installed epy_paper Qt: ' + LocalVerCheck + #13#10 +
      '  Installed epy_reports Qt:  ' + SiblingVerCheck + #13#10 +
      'The self-contained runtime in ' + AppInternalDir + ' will be kept.',
      mbInformation, MB_OK);
    Exit;
  end;

  GQtVersion := LocalVerCheck;
  GSharedDir := SharedInternalDir(GQtVersion);

  if not DirExists(GSharedDir) then begin
    CopyOk := CopyDirViaRobocopy(AppInternalDir, GSharedDir);
    if not CopyOk then begin
      MsgBox(
        'Warning: Could not copy the runtime to the shared location:' + #13#10 +
        '  ' + GSharedDir + #13#10 +
        'The self-contained runtime in ' + AppInternalDir + ' will be kept.',
        mbInformation, MB_OK);
      Exit;
    end;
  end;

  if DirExists(AppInternalDir) then
    DelTree(AppInternalDir, True, True, True);

  JunctionOk := CreateJunction(AppInternalDir, GSharedDir);
  if not JunctionOk then begin
    MsgBox(
      'Warning: Could not create the runtime junction at:' + #13#10 +
      '  ' + AppInternalDir + #13#10 +
      'Restoring the self-contained runtime.',
      mbInformation, MB_OK);
    CopyDirViaRobocopy(GSharedDir, AppInternalDir);
    Exit;
  end;

  RegWriteStringValue(HKEY_CURRENT_USER, REFCOUNT_KEY, 'qt_version', GQtVersion);
  CurrentRefcount := GetRegRefcount;
  SetRegRefcount(CurrentRefcount + 1);
end;

// ---------------------------------------------------------------------------
// Uninstall-time logic
// ---------------------------------------------------------------------------

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  AppInternalPath : String;
  StoredQtVer     : String;
  CurrentRefcount : Cardinal;
  SharedDir       : String;
begin
  if CurUninstallStep <> usUninstall then Exit;

  AppInternalPath := ExpandConstant('{app}') + '\_internal';

  if not RegQueryStringValue(HKEY_CURRENT_USER, REFCOUNT_KEY,
                             'qt_version', StoredQtVer) then Exit;

  SharedDir := SharedInternalDir(StoredQtVer);

  if DirExists(AppInternalPath) then
    RemoveJunction(AppInternalPath);

  CurrentRefcount := GetRegRefcount;
  if CurrentRefcount > 1 then begin
    SetRegRefcount(CurrentRefcount - 1);
  end else begin
    if DirExists(SharedDir) then
      DelTree(SharedDir, True, True, True);
    RemoveDir(SharedBaseForVer(StoredQtVer));
    RemoveDir(SharedRoot);
    RegDeleteKeyIncludingSubkeys(HKEY_CURRENT_USER, REFCOUNT_KEY);
    RegDeleteKeyIfEmpty(HKEY_CURRENT_USER, 'Software\epy_suite');
  end;
end;
