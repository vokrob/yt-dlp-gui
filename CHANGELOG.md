### 2026.08.01

#### Features

- [ci] yt-dlp-style rolling release workflow
- apply YouTube Dark theme and unify notification/toast colors
- add Back button and remove Home button from download queue
- cache video info and qualities per URL
- [ui] replace UpdateBanner with inline update button and hourly re-check
- auto-update yt-dlp weekly via CI (zero manual intervention)
- cache update check results for 6 hours (avoid API rate limit)
- bundle ffmpeg/deno, add cookies.txt, translate yt-dlp errors
- retry downloads with fallback browsers on cookie failure

#### Bug fixes

- [ci] accept -vv flag in make_changelog
- [ci] use GITHUB_REF for release commit push
- [ci] accept -vv flag in update_changelog
- replace Unicode punctuation with ASCII
- suppress loader error dialogs during binary validation; skip BtbN ffmpeg on Windows older than 2004; unify bootstrap logging to AppData
- validate downloaded binaries (run check) and fall back between ffmpeg sources
- bootstrap yt-dlp/ffmpeg binaries in frozen entry point (root main.py), return True when binaries exist
- version bump writing corrupted version line (-Value prefix bug)
- pyproject version update in release script
- support date-based versions in release script
- harden first-run binary download (timeout, validation, ffmpeg fallback)
- restore original logo
- restore cropped logo without shift
- set window icon reliably via Win32 API
- [update-checker] do not overwrite cache with empty results
- handle Ctrl+V paste on non-QWERTY keyboard layouts
- yaml syntax - flatten python one-liner

#### Refactoring

- remove unused psutil dependency and dead code paths
- remove dead code, legacy components and duplicated helpers
- [download-options] remove redundant format and quality labels
- replace scrollable frame with canvas-based scroll in download queue
- remove duplicate progress hooks, improve progress parsing
- center save path input in download options
- remove redundant yt-dlp CLI flags
- parse yt-dlp progress from stdout instead of stderr
- replace yt-dlp Python package with standalone binary

#### Documentation

- update changelog
- add system requirements and cookie notes to README
- remove obsolete CHANGELOG and CONTRIBUTING
- update screenshots
- try text-bottom alignment for logo
- adjust logo alignment with vertical-align
- shift logo icon down for better visual alignment
- crop transparent padding from logo
- align logo to baseline in README header
- reduce logo size in README header
- vertically align logo with title in README

#### CI changes

- use conventional commit and annotated tag in release script
- build only Windows for now (macOS/linux broken)

#### Chores

- [release] v2026.08.01
- remove duplicate release workflow
- [release] v2026.07.31
- [release] v1
- [release] v1
- [release] v1
- update app icon
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- clean up branding, UI text and debug output
- [release] v1.1.0
- add release script
- add ffmpeg_cache and deno_cache to .gitignore
- update yt-dlp to v2026.7.4

#### Other

- Release 2026.08.01
- 
- :ci skip all
- 
- Release 2026.08.01
- 
- :ci skip all
- 
- v2026.08.05
- v2026.08.04
- v2026.08.03
- v2026.08.02
- v2026.08.01
- Switch to sequential versioning (v1, v2, v3...)
- Remove all Russian text and emojis; full English localization
- Strip extra args to match bare yt-dlp CLI behavior
- Fix 'no cookies' attempt actually passing cookies; add debug command logging
- Fix nightly URL to yt-dlp/yt-dlp-nightly-builds; add stable fallback
- Update yt-dlp to nightly; add player_client fallback chain; user-friendly errors
- Clean up yt-dlp error messages for user display
- Sync yt-dlp update before GUI; add android player_client for YouTube
- Fix console windows spawning and improve error reporting
- - Capture real yt-dlp stderr errors and display to user
- - Load video formats sequentially after video info
- 
- rename release artifact to yt-dlp-gui.exe
- v1.1.0
- v1.1.1
- v1.1.0
- - Add binary_manager.py (downloads yt-dlp/ffmpeg on first run)
- - Add ytdlp_wrapper.py — subprocess wrapper for yt-dlp CLI
- - Add cookie_opts_to_cli() helper in cookie_manager.py
- - Migrate download_manager, format_detector, video_preview to
- subprocess calls
- - Remove ffmpeg/deno bundling from build.py (downloaded at
- runtime)
- - Remove CI auto-update workflow (replaced by in-app update)
- - Add auto-update of yt-dlp.exe on startup
- - Add splash window for first-launch binary download
- - Fix duplicate main() in main.py (second def overrides first)
- - Update .gitignore: ffmpeg_cache/deno_cache -> bin_dev/
- 
- v1.1.0: add self-update mechanism (check GitHub releases, download & restart)
- causing silent failures on authenticated content. Fall back
- through Chrome -> Firefox -> Edge -> no-cookies before giving up.
- 
- Also add noplaylist to all extractions and simplify format
- selectors by removing the unused language=orig fallback.
- 
- Update README with badges and better formatting
- Add YT-DLP GUI application
<details>
<summary>Previous versions</summary>

### 2026.08.01

#### Features

- [ci] yt-dlp-style rolling release workflow
- apply YouTube Dark theme and unify notification/toast colors
- add Back button and remove Home button from download queue
- cache video info and qualities per URL
- [ui] replace UpdateBanner with inline update button and hourly re-check
- auto-update yt-dlp weekly via CI (zero manual intervention)
- cache update check results for 6 hours (avoid API rate limit)
- bundle ffmpeg/deno, add cookies.txt, translate yt-dlp errors
- retry downloads with fallback browsers on cookie failure

#### Bug fixes

- [ci] use GITHUB_REF for release commit push
- [ci] accept -vv flag in update_changelog
- replace Unicode punctuation with ASCII
- suppress loader error dialogs during binary validation; skip BtbN ffmpeg on Windows older than 2004; unify bootstrap logging to AppData
- validate downloaded binaries (run check) and fall back between ffmpeg sources
- bootstrap yt-dlp/ffmpeg binaries in frozen entry point (root main.py), return True when binaries exist
- version bump writing corrupted version line (-Value prefix bug)
- pyproject version update in release script
- support date-based versions in release script
- harden first-run binary download (timeout, validation, ffmpeg fallback)
- restore original logo
- restore cropped logo without shift
- set window icon reliably via Win32 API
- [update-checker] do not overwrite cache with empty results
- handle Ctrl+V paste on non-QWERTY keyboard layouts
- yaml syntax - flatten python one-liner

#### Refactoring

- remove unused psutil dependency and dead code paths
- remove dead code, legacy components and duplicated helpers
- [download-options] remove redundant format and quality labels
- replace scrollable frame with canvas-based scroll in download queue
- remove duplicate progress hooks, improve progress parsing
- center save path input in download options
- remove redundant yt-dlp CLI flags
- parse yt-dlp progress from stdout instead of stderr
- replace yt-dlp Python package with standalone binary

#### Documentation

- update changelog
- add system requirements and cookie notes to README
- remove obsolete CHANGELOG and CONTRIBUTING
- update screenshots
- try text-bottom alignment for logo
- adjust logo alignment with vertical-align
- shift logo icon down for better visual alignment
- crop transparent padding from logo
- align logo to baseline in README header
- reduce logo size in README header
- vertically align logo with title in README

#### CI changes

- use conventional commit and annotated tag in release script
- build only Windows for now (macOS/linux broken)

#### Chores

- [release] v2026.08.01
- remove duplicate release workflow
- [release] v2026.07.31
- [release] v1
- [release] v1
- [release] v1
- update app icon
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- clean up branding, UI text and debug output
- [release] v1.1.0
- add release script
- add ffmpeg_cache and deno_cache to .gitignore
- update yt-dlp to v2026.7.4

#### Other

- Release 2026.08.01
- 
- :ci skip all
- 
- v2026.08.05
- v2026.08.04
- v2026.08.03
- v2026.08.02
- v2026.08.01
- Switch to sequential versioning (v1, v2, v3...)
- Remove all Russian text and emojis; full English localization
- Strip extra args to match bare yt-dlp CLI behavior
- Fix 'no cookies' attempt actually passing cookies; add debug command logging
- Fix nightly URL to yt-dlp/yt-dlp-nightly-builds; add stable fallback
- Update yt-dlp to nightly; add player_client fallback chain; user-friendly errors
- Clean up yt-dlp error messages for user display
- Sync yt-dlp update before GUI; add android player_client for YouTube
- Fix console windows spawning and improve error reporting
- - Capture real yt-dlp stderr errors and display to user
- - Load video formats sequentially after video info
- 
- rename release artifact to yt-dlp-gui.exe
- v1.1.0
- v1.1.1
- v1.1.0
- - Add binary_manager.py (downloads yt-dlp/ffmpeg on first run)
- - Add ytdlp_wrapper.py — subprocess wrapper for yt-dlp CLI
- - Add cookie_opts_to_cli() helper in cookie_manager.py
- - Migrate download_manager, format_detector, video_preview to
- subprocess calls
- - Remove ffmpeg/deno bundling from build.py (downloaded at
- runtime)
- - Remove CI auto-update workflow (replaced by in-app update)
- - Add auto-update of yt-dlp.exe on startup
- - Add splash window for first-launch binary download
- - Fix duplicate main() in main.py (second def overrides first)
- - Update .gitignore: ffmpeg_cache/deno_cache -> bin_dev/
- 
- v1.1.0: add self-update mechanism (check GitHub releases, download & restart)
- causing silent failures on authenticated content. Fall back
- through Chrome -> Firefox -> Edge -> no-cookies before giving up.
- 
- Also add noplaylist to all extractions and simplify format
- selectors by removing the unused language=orig fallback.
- 
- Update README with badges and better formatting
- Add YT-DLP GUI application
<details>
<summary>Previous versions</summary>

### 2026.08.01

#### Features

- [ci] yt-dlp-style rolling release workflow
- apply YouTube Dark theme and unify notification/toast colors
- add Back button and remove Home button from download queue
- cache video info and qualities per URL
- [ui] replace UpdateBanner with inline update button and hourly re-check
- auto-update yt-dlp weekly via CI (zero manual intervention)
- cache update check results for 6 hours (avoid API rate limit)
- bundle ffmpeg/deno, add cookies.txt, translate yt-dlp errors
- retry downloads with fallback browsers on cookie failure

#### Bug fixes

- [ci] use GITHUB_REF for release commit push
- [ci] accept -vv flag in update_changelog
- replace Unicode punctuation with ASCII
- suppress loader error dialogs during binary validation; skip BtbN ffmpeg on Windows older than 2004; unify bootstrap logging to AppData
- validate downloaded binaries (run check) and fall back between ffmpeg sources
- bootstrap yt-dlp/ffmpeg binaries in frozen entry point (root main.py), return True when binaries exist
- version bump writing corrupted version line (-Value prefix bug)
- pyproject version update in release script
- support date-based versions in release script
- harden first-run binary download (timeout, validation, ffmpeg fallback)
- restore original logo
- restore cropped logo without shift
- set window icon reliably via Win32 API
- [update-checker] do not overwrite cache with empty results
- handle Ctrl+V paste on non-QWERTY keyboard layouts
- yaml syntax - flatten python one-liner

#### Refactoring

- remove unused psutil dependency and dead code paths
- remove dead code, legacy components and duplicated helpers
- [download-options] remove redundant format and quality labels
- replace scrollable frame with canvas-based scroll in download queue
- remove duplicate progress hooks, improve progress parsing
- center save path input in download options
- remove redundant yt-dlp CLI flags
- parse yt-dlp progress from stdout instead of stderr
- replace yt-dlp Python package with standalone binary

#### Documentation

- update changelog
- add system requirements and cookie notes to README
- remove obsolete CHANGELOG and CONTRIBUTING
- update screenshots
- try text-bottom alignment for logo
- adjust logo alignment with vertical-align
- shift logo icon down for better visual alignment
- crop transparent padding from logo
- align logo to baseline in README header
- reduce logo size in README header
- vertically align logo with title in README

#### CI changes

- use conventional commit and annotated tag in release script
- build only Windows for now (macOS/linux broken)

#### Chores

- [release] v2026.08.01
- remove duplicate release workflow
- [release] v2026.07.31
- [release] v1
- [release] v1
- [release] v1
- update app icon
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- clean up branding, UI text and debug output
- [release] v1.1.0
- add release script
- add ffmpeg_cache and deno_cache to .gitignore
- update yt-dlp to v2026.7.4

#### Other

- v2026.08.05
- v2026.08.04
- v2026.08.03
- v2026.08.02
- v2026.08.01
- Switch to sequential versioning (v1, v2, v3...)
- Remove all Russian text and emojis; full English localization
- Strip extra args to match bare yt-dlp CLI behavior
- Fix 'no cookies' attempt actually passing cookies; add debug command logging
- Fix nightly URL to yt-dlp/yt-dlp-nightly-builds; add stable fallback
- Update yt-dlp to nightly; add player_client fallback chain; user-friendly errors
- Clean up yt-dlp error messages for user display
- Sync yt-dlp update before GUI; add android player_client for YouTube
- Fix console windows spawning and improve error reporting
- - Capture real yt-dlp stderr errors and display to user
- - Load video formats sequentially after video info
- 
- rename release artifact to yt-dlp-gui.exe
- v1.1.0
- v1.1.1
- v1.1.0
- - Add binary_manager.py (downloads yt-dlp/ffmpeg on first run)
- - Add ytdlp_wrapper.py — subprocess wrapper for yt-dlp CLI
- - Add cookie_opts_to_cli() helper in cookie_manager.py
- - Migrate download_manager, format_detector, video_preview to
- subprocess calls
- - Remove ffmpeg/deno bundling from build.py (downloaded at
- runtime)
- - Remove CI auto-update workflow (replaced by in-app update)
- - Add auto-update of yt-dlp.exe on startup
- - Add splash window for first-launch binary download
- - Fix duplicate main() in main.py (second def overrides first)
- - Update .gitignore: ffmpeg_cache/deno_cache -> bin_dev/
- 
- v1.1.0: add self-update mechanism (check GitHub releases, download & restart)
- causing silent failures on authenticated content. Fall back
- through Chrome -> Firefox -> Edge -> no-cookies before giving up.
- 
- Also add noplaylist to all extractions and simplify format
- selectors by removing the unused language=orig fallback.
- 
- Update README with badges and better formatting
- Add YT-DLP GUI application
<details>
<summary>Previous versions</summary>

### 2026.08.01

#### Features

- [ci] yt-dlp-style rolling release workflow
- apply YouTube Dark theme and unify notification/toast colors
- add Back button and remove Home button from download queue
- cache video info and qualities per URL
- [ui] replace UpdateBanner with inline update button and hourly re-check
- auto-update yt-dlp weekly via CI (zero manual intervention)
- cache update check results for 6 hours (avoid API rate limit)
- bundle ffmpeg/deno, add cookies.txt, translate yt-dlp errors
- retry downloads with fallback browsers on cookie failure

#### Bug fixes

- replace Unicode punctuation with ASCII
- suppress loader error dialogs during binary validation; skip BtbN ffmpeg on Windows older than 2004; unify bootstrap logging to AppData
- validate downloaded binaries (run check) and fall back between ffmpeg sources
- bootstrap yt-dlp/ffmpeg binaries in frozen entry point (root main.py), return True when binaries exist
- version bump writing corrupted version line (-Value prefix bug)
- pyproject version update in release script
- support date-based versions in release script
- harden first-run binary download (timeout, validation, ffmpeg fallback)
- restore original logo
- restore cropped logo without shift
- set window icon reliably via Win32 API
- [update-checker] do not overwrite cache with empty results
- handle Ctrl+V paste on non-QWERTY keyboard layouts
- yaml syntax - flatten python one-liner

#### Refactoring

- remove unused psutil dependency and dead code paths
- remove dead code, legacy components and duplicated helpers
- [download-options] remove redundant format and quality labels
- replace scrollable frame with canvas-based scroll in download queue
- remove duplicate progress hooks, improve progress parsing
- center save path input in download options
- remove redundant yt-dlp CLI flags
- parse yt-dlp progress from stdout instead of stderr
- replace yt-dlp Python package with standalone binary

#### Documentation

- add system requirements and cookie notes to README
- remove obsolete CHANGELOG and CONTRIBUTING
- update screenshots
- try text-bottom alignment for logo
- adjust logo alignment with vertical-align
- shift logo icon down for better visual alignment
- crop transparent padding from logo
- align logo to baseline in README header
- reduce logo size in README header
- vertically align logo with title in README

#### CI changes

- use conventional commit and annotated tag in release script
- build only Windows for now (macOS/linux broken)

#### Chores

- [release] v2026.08.01
- remove duplicate release workflow
- [release] v2026.07.31
- [release] v1
- [release] v1
- [release] v1
- update app icon
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- clean up branding, UI text and debug output
- [release] v1.1.0
- add release script
- add ffmpeg_cache and deno_cache to .gitignore
- update yt-dlp to v2026.7.4

#### Other

- v2026.08.05
- v2026.08.04
- v2026.08.03
- v2026.08.02
- v2026.08.01
- Switch to sequential versioning (v1, v2, v3...)
- Remove all Russian text and emojis; full English localization
- Strip extra args to match bare yt-dlp CLI behavior
- Fix 'no cookies' attempt actually passing cookies; add debug command logging
- Fix nightly URL to yt-dlp/yt-dlp-nightly-builds; add stable fallback
- Update yt-dlp to nightly; add player_client fallback chain; user-friendly errors
- Clean up yt-dlp error messages for user display
- Sync yt-dlp update before GUI; add android player_client for YouTube
- Fix console windows spawning and improve error reporting
- - Capture real yt-dlp stderr errors and display to user
- - Load video formats sequentially after video info
- 
- rename release artifact to yt-dlp-gui.exe
- v1.1.0
- v1.1.1
- v1.1.0
- - Add binary_manager.py (downloads yt-dlp/ffmpeg on first run)
- - Add ytdlp_wrapper.py вЂ” subprocess wrapper for yt-dlp CLI
- - Add cookie_opts_to_cli() helper in cookie_manager.py
- - Migrate download_manager, format_detector, video_preview to
- subprocess calls
- - Remove ffmpeg/deno bundling from build.py (downloaded at
- runtime)
- - Remove CI auto-update workflow (replaced by in-app update)
- - Add auto-update of yt-dlp.exe on startup
- - Add splash window for first-launch binary download
- - Fix duplicate main() in main.py (second def overrides first)
- - Update .gitignore: ffmpeg_cache/deno_cache -> bin_dev/
- 
- v1.1.0: add self-update mechanism (check GitHub releases, download & restart)
- causing silent failures on authenticated content. Fall back
- through Chrome -> Firefox -> Edge -> no-cookies before giving up.
- 
- Also add noplaylist to all extractions and simplify format
- selectors by removing the unused language=orig fallback.
- 
- Update README with badges and better formatting
- Add YT-DLP GUI application
<details>
<summary>Previous versions</summary>

### 2026.08.01

#### Features

- apply YouTube Dark theme and unify notification/toast colors
- add Back button and remove Home button from download queue
- cache video info and qualities per URL
- [ui] replace UpdateBanner with inline update button and hourly re-check
- auto-update yt-dlp weekly via CI (zero manual intervention)
- cache update check results for 6 hours (avoid API rate limit)
- bundle ffmpeg/deno, add cookies.txt, translate yt-dlp errors
- retry downloads with fallback browsers on cookie failure

#### Bug fixes

- replace Unicode punctuation with ASCII
- suppress loader error dialogs during binary validation; skip BtbN ffmpeg on Windows older than 2004; unify bootstrap logging to AppData
- validate downloaded binaries (run check) and fall back between ffmpeg sources
- bootstrap yt-dlp/ffmpeg binaries in frozen entry point (root main.py), return True when binaries exist
- version bump writing corrupted version line (-Value prefix bug)
- pyproject version update in release script
- support date-based versions in release script
- harden first-run binary download (timeout, validation, ffmpeg fallback)
- restore original logo
- restore cropped logo without shift
- set window icon reliably via Win32 API
- [update-checker] do not overwrite cache with empty results
- handle Ctrl+V paste on non-QWERTY keyboard layouts
- yaml syntax - flatten python one-liner

#### Refactoring

- remove unused psutil dependency and dead code paths
- remove dead code, legacy components and duplicated helpers
- [download-options] remove redundant format and quality labels
- replace scrollable frame with canvas-based scroll in download queue
- remove duplicate progress hooks, improve progress parsing
- center save path input in download options
- remove redundant yt-dlp CLI flags
- parse yt-dlp progress from stdout instead of stderr
- replace yt-dlp Python package with standalone binary

#### Documentation

- add system requirements and cookie notes to README
- remove obsolete CHANGELOG and CONTRIBUTING
- update screenshots
- try text-bottom alignment for logo
- adjust logo alignment with vertical-align
- shift logo icon down for better visual alignment
- crop transparent padding from logo
- align logo to baseline in README header
- reduce logo size in README header
- vertically align logo with title in README

#### CI changes

- use conventional commit and annotated tag in release script
- build only Windows for now (macOS/linux broken)

#### Chores

- [release] v2026.08.01
- remove duplicate release workflow
- [release] v2026.07.31
- [release] v1
- [release] v1
- [release] v1
- update app icon
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- clean up branding, UI text and debug output
- [release] v1.1.0
- add release script
- add ffmpeg_cache and deno_cache to .gitignore
- update yt-dlp to v2026.7.4

#### Other

- v2026.08.05
- v2026.08.04
- v2026.08.03
- v2026.08.02
- v2026.08.01
- Switch to sequential versioning (v1, v2, v3...)
- Remove all Russian text and emojis; full English localization
- Strip extra args to match bare yt-dlp CLI behavior
- Fix 'no cookies' attempt actually passing cookies; add debug command logging
- Fix nightly URL to yt-dlp/yt-dlp-nightly-builds; add stable fallback
- Update yt-dlp to nightly; add player_client fallback chain; user-friendly errors
- Clean up yt-dlp error messages for user display
- Sync yt-dlp update before GUI; add android player_client for YouTube
- Fix console windows spawning and improve error reporting
- - Capture real yt-dlp stderr errors and display to user
- - Load video formats sequentially after video info
- 
- rename release artifact to yt-dlp-gui.exe
- v1.1.0
- v1.1.1
- v1.1.0
- - Add binary_manager.py (downloads yt-dlp/ffmpeg on first run)
- - Add ytdlp_wrapper.py вЂ” subprocess wrapper for yt-dlp CLI
- - Add cookie_opts_to_cli() helper in cookie_manager.py
- - Migrate download_manager, format_detector, video_preview to
- subprocess calls
- - Remove ffmpeg/deno bundling from build.py (downloaded at
- runtime)
- - Remove CI auto-update workflow (replaced by in-app update)
- - Add auto-update of yt-dlp.exe on startup
- - Add splash window for first-launch binary download
- - Fix duplicate main() in main.py (second def overrides first)
- - Update .gitignore: ffmpeg_cache/deno_cache -> bin_dev/
- 
- v1.1.0: add self-update mechanism (check GitHub releases, download & restart)
- causing silent failures on authenticated content. Fall back
- through Chrome -> Firefox -> Edge -> no-cookies before giving up.
- 
- Also add noplaylist to all extractions and simplify format
- selectors by removing the unused language=orig fallback.
- 
- Update README with badges and better formatting
- Add YT-DLP GUI application
<details>
<summary>Previous versions</summary>

### 2026.08.01

#### Features

- apply YouTube Dark theme and unify notification/toast colors
- add Back button and remove Home button from download queue
- cache video info and qualities per URL
- [ui] replace UpdateBanner with inline update button and hourly re-check
- auto-update yt-dlp weekly via CI (zero manual intervention)
- cache update check results for 6 hours (avoid API rate limit)
- bundle ffmpeg/deno, add cookies.txt, translate yt-dlp errors
- retry downloads with fallback browsers on cookie failure

#### Bug fixes

- replace Unicode punctuation with ASCII
- suppress loader error dialogs during binary validation; skip BtbN ffmpeg on Windows older than 2004; unify bootstrap logging to AppData
- validate downloaded binaries (run check) and fall back between ffmpeg sources
- bootstrap yt-dlp/ffmpeg binaries in frozen entry point (root main.py), return True when binaries exist
- version bump writing corrupted version line (-Value prefix bug)
- pyproject version update in release script
- support date-based versions in release script
- harden first-run binary download (timeout, validation, ffmpeg fallback)
- restore original logo
- restore cropped logo without shift
- set window icon reliably via Win32 API
- [update-checker] do not overwrite cache with empty results
- handle Ctrl+V paste on non-QWERTY keyboard layouts
- yaml syntax - flatten python one-liner

#### Refactoring

- remove unused psutil dependency and dead code paths
- remove dead code, legacy components and duplicated helpers
- [download-options] remove redundant format and quality labels
- replace scrollable frame with canvas-based scroll in download queue
- remove duplicate progress hooks, improve progress parsing
- center save path input in download options
- remove redundant yt-dlp CLI flags
- parse yt-dlp progress from stdout instead of stderr
- replace yt-dlp Python package with standalone binary

#### Documentation

- add system requirements and cookie notes to README
- remove obsolete CHANGELOG and CONTRIBUTING
- update screenshots
- try text-bottom alignment for logo
- adjust logo alignment with vertical-align
- shift logo icon down for better visual alignment
- crop transparent padding from logo
- align logo to baseline in README header
- reduce logo size in README header
- vertically align logo with title in README

#### CI changes

- use conventional commit and annotated tag in release script
- build only Windows for now (macOS/linux broken)

#### Chores

- [release] v2026.08.01
- remove duplicate release workflow
- [release] v2026.07.31
- [release] v1
- [release] v1
- [release] v1
- update app icon
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- [release] v1.1.1
- clean up branding, UI text and debug output
- [release] v1.1.0
- add release script
- add ffmpeg_cache and deno_cache to .gitignore
- update yt-dlp to v2026.7.4

#### Other

- v2026.08.05
- v2026.08.04
- v2026.08.03
- v2026.08.02
- v2026.08.01
- Switch to sequential versioning (v1, v2, v3...)
- Remove all Russian text and emojis; full English localization
- Strip extra args to match bare yt-dlp CLI behavior
- Fix 'no cookies' attempt actually passing cookies; add debug command logging
- Fix nightly URL to yt-dlp/yt-dlp-nightly-builds; add stable fallback
- Update yt-dlp to nightly; add player_client fallback chain; user-friendly errors
- Clean up yt-dlp error messages for user display
- Sync yt-dlp update before GUI; add android player_client for YouTube
- Fix console windows spawning and improve error reporting
- - Capture real yt-dlp stderr errors and display to user
- - Load video formats sequentially after video info
- 
- rename release artifact to yt-dlp-gui.exe
- v1.1.0
- v1.1.1
- v1.1.0
- - Add binary_manager.py (downloads yt-dlp/ffmpeg on first run)
- - Add ytdlp_wrapper.py вЂ” subprocess wrapper for yt-dlp CLI
- - Add cookie_opts_to_cli() helper in cookie_manager.py
- - Migrate download_manager, format_detector, video_preview to
- subprocess calls
- - Remove ffmpeg/deno bundling from build.py (downloaded at
- runtime)
- - Remove CI auto-update workflow (replaced by in-app update)
- - Add auto-update of yt-dlp.exe on startup
- - Add splash window for first-launch binary download
- - Fix duplicate main() in main.py (second def overrides first)
- - Update .gitignore: ffmpeg_cache/deno_cache -> bin_dev/
- 
- v1.1.0: add self-update mechanism (check GitHub releases, download & restart)
- causing silent failures on authenticated content. Fall back
- through Chrome -> Firefox -> Edge -> no-cookies before giving up.
- 
- Also add noplaylist to all extractions and simplify format
- selectors by removing the unused language=orig fallback.
- 
- Update README with badges and better formatting
- Add YT-DLP GUI application
</details>
</details>
</details>
</details>
</details>
