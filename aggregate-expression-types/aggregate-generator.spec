# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['aggregate_expression_types/main.py'],
    pathex=['/home/codedmart/.cache/pypoetry/virtualenvs/aggregate-expression-types-e5EsB3gb-py3.12/lib/python3.12/site-packages'],
    binaries=[],
    datas=[('aggregate_expression_types', 'aggregate_expression_types')],
    hiddenimports=['ruamel.yaml', 'ruamel.yaml.constructor', 'ruamel.yaml.representer', 'ruamel.yaml.resolver'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='aggregate-generator',
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
