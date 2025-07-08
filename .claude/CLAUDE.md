# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要
これはClaude CodeのGitHub連携をテストするためのシンプルなPythonサンプルプロジェクトです。

## 開発環境
- Python 3.12（.python-versionで指定）
- pyproject.tomlで依存関係管理

## よく使うコマンド

### 実行
```bash
python3 main.py
```

### 依存関係のインストール（今後追加された場合）
```bash
pip install -e .
```

## プロジェクト構造
- `main.py`: メインエントリーポイント
- `pyproject.toml`: プロジェクト設定と依存関係定義

## 開発時の注意点
- このプロジェクトはまだ初期段階のため、機能追加時は適切なディレクトリ構造（src/, tests/など）の作成を検討してください
- pyproject.tomlを使った最新のPythonプロジェクト管理方式を維持してください