# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['tournament_cli/cli.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'typer',
        'rich',
        'markdown',
        'weasyprint',
        'tournament_cli',
        'tournament_cli.models',
        'tournament_cli.storage',
        'tournament_cli.matchmaking',
        'tournament_cli.display',
        'tournament_cli.export',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='tournament-cli',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
