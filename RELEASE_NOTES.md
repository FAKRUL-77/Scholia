# Scholia 1.0.0

**Release date:** 2026-11-21
**Type:** First stable release
**Platform:** macOS (built with PyInstaller). Source runs wherever PySide6 runs.

Scholia is a desktop app for reading lecture PDFs and writing your own notes for every page, side by side. This first release covers the full study workflow: build a library of PDFs, read them with a linked note page per slide, and let everything save itself.

---

## Highlights

- **One note page per PDF page.** Change the PDF page and the matching notes appear instantly.
- **Library for all your lectures.** Add as many PDFs as you need and switch between them in one click. The list persists between launches.
- **Rich, fast note editor.** Titles, headings, bold, highlight, bullet and numbered lists, screenshots from the clipboard, and Markdown-style typing shortcuts.
- **Automatic saving.** No Save button, and nothing leaves your computer.
- **Modern interface.** Vector icons, light and dark themes, and a resizable split view.

## What's included

### Library
- Add one or many PDFs (`Cmd+O`, the **Add PDF** button, or drag and drop onto the window)
- Each entry shows your last page and how many pages have notes
- Right-click for **Show in Finder** or **Remove from list**; `Delete` removes the selected entry
- Removing a PDF from the list never deletes the PDF file or its notes
- Files that were moved or deleted are clearly marked, with guidance on how to recover
- The last opened PDF reopens on the page you left

### Reader
- Continuous PDF view with zoom in, zoom out, and fit-to-width
- Jump to a page by typing its number, or use the arrow buttons, `Cmd+[` / `Cmd+]`, or the arrow keys when the PDF has focus
- Draggable divider between the PDF and the notes; window size and panel layout are remembered
- Collapsible PDF list (`Cmd+\`)

### Highlighting
- Select PDF text by dragging, or double-click a word
- A floating bar offers four highlight colors, **Copy**, and **Add to notes** (inserts the text as a quote)
- Click an existing highlight to recolor, copy, or remove it
- Highlights are saved per PDF and restored on the next launch
- `Cmd+C` copies the selection, `Esc` clears it

### Notes editor
- Title, heading, normal text, bold, and highlight (the highlight is readable in both themes)
- Bullet and numbered lists with nesting (`Tab` / `Shift+Tab`)
- Typing shortcuts: `- ` bullet list, `1. ` numbered list, `# ` title, `## ` heading
- Paste screenshots with `Cmd+V`, or insert an image from a file
- Undo and redo
- Toolbar buttons show the formatting at the cursor (bold, highlight, list type)
- Save status in the notes header (*Editing…* / *Saved ✓*)

### Appearance
- Light and dark themes; the first launch follows your system setting
- Consistent vector icons that adapt to the active theme
- New app icon for the Dock, Launchpad and Finder
- Helpful empty state when no PDF is loaded

## Installation

**macOS app**
1. Download `Scholia-1.0.0-macos.zip` from the assets below and unzip it.
2. Drag **Scholia.app** into **Applications**.
3. On first launch, right-click the app and choose **Open**, or allow it in **System Settings → Privacy & Security → Open Anyway**.

**From source** (Python 3.10+)
```bash
git clone https://github.com/<your-username>/Scholia.git
cd Scholia
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 Scholia.py
```

## Where your data is stored

Notes and highlights are stored next to each PDF in a folder named `<pdf name>_notes`, containing `notes.json` and an `images/` folder. Copy that folder to back up or move your notes. The PDF list and window layout are stored in the standard macOS preferences for the app. Scholia makes no network connections.

## Requirements

| | |
|---|---|
| Operating system | macOS (developed and tested on macOS) |
| Python (source only) | 3.10 or newer |
| Dependencies (source only) | PySide6 6.5 or newer |

## Known issues and limitations

- **Unsigned build.** The app is not signed or notarized, so macOS asks for confirmation on first launch.
- **Notes are linked by file name.** If you rename a PDF, rename its `*_notes` folder to match. Notes are not lost; they are just not found under the new name.
- **PDF pages stay white in dark theme.** Only the interface is themed.
- **Highlights are not written into the PDF.** They live in Scholia's own files, so other PDF apps will not show them.
- **Scanned PDFs cannot be selected.** Text selection needs a PDF with real text.
- **No search or export yet.**
- **Windows and Linux are untested.** PySide6 is cross-platform, but shortcuts follow macOS conventions.
- **Build architecture.** The release app runs on the type of Mac it was built on (Apple Silicon or Intel).

## Upgrading

This is the first stable release. If you used an earlier development build (working name *FReader*), your notes are read as they are, and your PDF list, theme and window layout are carried over automatically on first launch.

## Verifying your download

Compare the checksum of the downloaded file with the one published on the release page:

```bash
shasum -a 256 Scholia-1.0.0-macos.zip
```

## Feedback

Please report bugs and ideas on the [issue tracker](../../issues). Include your macOS version, the steps to reproduce, and (if the app fails to start) the output of:

```bash
"/Applications/Scholia.app/Contents/MacOS/Scholia"
```

---

**Full changelog:** initial release
