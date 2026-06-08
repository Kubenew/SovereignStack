# Building SovereignStack for Windows

## Prerequisites

| Tool | Required | Install |
|------|----------|---------|
| **Rust** | Yes | `winget install Rustlang.Rustup` or [rustup.rs](https://rustup.rs) |
| **Python 3.10+** | For Python services | `winget install Python.Python.3.12` |
| **PyInstaller** | For bundling .py → .exe | `pip install pyinstaller` |
| **WiX Toolset v4** | For MSI installer | `winget install WiXToolset.WiX` or [wixtoolset.org](https://wixtoolset.org) |

## Quick Build (binaries only)

```powershell
# Build both binaries (x86_64-pc-windows-msvc is default on Windows)
cargo build --release --bin ss-node
cargo build --release --bin ss-cli

# Find them in:
.\target\release\ss-node.exe
.\target\release\ss-cli.exe
```

## Full Release Build (including Python services + MSI)

```powershell
.\scripts\build-release.ps1 -Version "0.3.0"
```

This produces:

```
dist\SovereignStack-v0.3.0\
├── bin\
│   ├── ss-node.exe      (reference node HTTP server)
│   └── ss-cli.exe       (CLI client)
├── services\
│   ├── gateway-service.exe
│   ├── federation-service.exe
│   ├── merkle-audit.exe
│   └── memory-service.exe
├── config\
│   └── env.example
├── docs\
│   ├── README.md
│   ├── CERTIFICATION.md
│   ├── CONFORMANCE.md
│   └── SECURITY.md
└── data\                 (runtime data — created on first run)
```

And optionally `dist\SovereignStack-v0.3.0.msi` (Windows Installer package).

## Running

### As a command-line tool

```powershell
ss-cli.exe --help
ss-cli.exe node status
```

### As a server

```powershell
ss-node.exe --port 8546
```

### As a Windows Service (if installed via MSI)

```powershell
Start-Service SsNode
Get-Service SsNode
Stop-Service SsNode
```

### From source (without building)

```powershell
cargo run --bin ss-node -- --port 8546
```

## MSI Installer Details

The WiX installer (`installer\sovereignstack.wxs`) creates:

- **Install path**: `%ProgramFiles%\SovereignStack\`
- **Windows Service**: `SsNode` (auto-start, runs as NetworkService)
- **Start Menu**: Shortcut to `ss-cli.exe`
- **Data directory**: `%ProgramFiles%\SovereignStack\data\` (configurable via `--data`)

To build the MSI manually:

```powershell
candle.exe -arch x64 -dVersion=0.3.0 -dSourceDir=dist\SovereignStack-v0.3.0 -out dist\sovereignstack.wixobj installer\sovereignstack.wxs
light.exe -out dist\SovereignStack-v0.3.0.msi dist\sovereignstack.wixobj
```

## Cross-compilation from Linux/macOS

```bash
# Install the Windows target
rustup target add x86_64-pc-windows-msvc

# Build (requires MinGW-w64 or LLVM tools on Linux)
cargo build --release --target x86_64-pc-windows-msvc --bin ss-node --bin ss-cli

# The .exe files will be at:
# target/x86_64-pc-windows-msvc/release/ss-node.exe
# target/x86_64-pc-windows-msvc/release/ss-cli.exe
```

## Troubleshooting

| Error | Fix |
|-------|-----|
| `link.exe` not found | Install [Visual Studio Build Tools](https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022) with "C++ tools" workload |
| `candle.exe` not found | Install WiX Toolset v4: `winget install WiXToolset.WiX` |
| Python services not bundled | Run with `-SkipPyInstaller` flag to build binaries only |
| Port 8546 in use | Use `--port 8547` to change the listening port |
