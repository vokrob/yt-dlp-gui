# Changelog

## v1.1.1 - 29.07.2026

### Fixed
- Добавлен фоновый вызов update_ytdlp() при запуске — yt-dlp теперь автообновляется автоматически

## v1.1.0 - 29.07.2026

### Added
- Выбор пути сохранения аудио/видео через интерфейс (Browse...)
- Поле "Save to:" показывает текущую папку, можно изменить в один клик

### Changed
- Размер установщика уменьшен с 110 MB до ~18 MB (бинарники скачиваются при первом запуске)
- yt-dlp теперь запускается как subprocess, а не импортируется как Python-пакет

### Removed
- Удалён bundling ffmpeg/deno из PyInstaller сборки
- Очищена git история от 300+ MB бинарных объектов

## v1.0.0 - 18.07.2025

Initial release.

### Features
- Video downloads from YouTube and other sites
- Quality selection (144p-4K)
- Audio extraction to MP3
- Download progress tracking
- Cross-platform support

### Technical
- Python 3.9+
- CustomTkinter interface
- Executable builds
