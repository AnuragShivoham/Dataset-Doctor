# Requirements Document

## Introduction

This feature transforms the existing bare Monaco Editor instance (`monaco.html`) into a fully functional, browser-based IDE interface. The IDE provides a real-world IDE experience with a file explorer, multi-tab editor, toolbar/menu bar, status bar, and an integrated terminal panel — all self-contained in a single HTML/CSS/JS application that loads Monaco Editor from the locally installed `node_modules/monaco-editor` package.

## Glossary

- **IDE**: The Monaco IDE UI — the complete browser-based IDE application described in this document.
- **Editor**: The Monaco Editor instance that renders and edits file content.
- **File_Explorer**: The left-side panel that displays the virtual file tree and allows file/folder navigation.
- **Tab_Bar**: The horizontal row of open-file tabs above the Editor.
- **Tab**: A single clickable element in the Tab_Bar representing an open file.
- **Toolbar**: The top-most bar containing application-level menus and action buttons.
- **Status_Bar**: The bottom bar displaying contextual information about the current editor state.
- **Terminal_Panel**: The resizable panel at the bottom of the IDE that provides a simulated terminal output area.
- **Active_File**: The file whose content is currently displayed and editable in the Editor.
- **Virtual_File_System**: An in-memory representation of files and folders managed by the IDE.
- **Theme**: The visual color scheme applied to the IDE (dark or light).
- **Language_Mode**: The Monaco Editor language used for syntax highlighting and IntelliSense, derived from the file extension.

---

## Requirements

### Requirement 1: Overall IDE Layout

**User Story:** As a developer, I want a standard IDE-style layout in the browser, so that I can work in a familiar environment without leaving the browser.

#### Acceptance Criteria

1. THE IDE SHALL render a full-viewport layout composed of a Toolbar at the top, a File_Explorer on the left, a Tab_Bar and Editor in the center, a Terminal_Panel at the bottom, and a Status_Bar at the very bottom.
2. THE IDE SHALL fill 100% of the browser viewport width and height with no scroll bars on the outer page.
3. WHEN the browser window is resized, THE IDE SHALL reflow all panels to maintain their proportional layout within the new viewport dimensions.
4. THE IDE SHALL load Monaco Editor from the local `node_modules/monaco-editor/min/vs` path rather than from a CDN.

---

### Requirement 2: File Explorer Panel

**User Story:** As a developer, I want a file explorer on the left side, so that I can navigate and open files in my project.

#### Acceptance Criteria

1. THE File_Explorer SHALL display a tree of files and folders from the Virtual_File_System.
2. THE Virtual_File_System SHALL be pre-populated with at least three example files of different types (e.g., `.js`, `.html`, `.css`) on initial load.
3. WHEN a user clicks a file in the File_Explorer, THE IDE SHALL open that file in the Editor and make it the Active_File.
4. WHEN a user clicks a folder in the File_Explorer, THE File_Explorer SHALL toggle the expanded or collapsed state of that folder.
5. THE File_Explorer SHALL display file-type icons or visual indicators that distinguish files from folders.
6. WHEN a file is the Active_File, THE File_Explorer SHALL highlight that file's entry to indicate it is selected.
7. THE File_Explorer SHALL support a "New File" action that prompts the user for a file name and adds the new file to the Virtual_File_System.
8. THE File_Explorer SHALL support a "New Folder" action that prompts the user for a folder name and adds the new folder to the Virtual_File_System.

---

### Requirement 3: Multi-Tab Editor

**User Story:** As a developer, I want to open multiple files in tabs, so that I can switch between files quickly without losing my place.

#### Acceptance Criteria

1. THE Tab_Bar SHALL display one Tab for each file that has been opened during the session.
2. WHEN a user clicks a Tab, THE Editor SHALL display the content of the file associated with that Tab and make it the Active_File.
3. THE Tab_Bar SHALL visually distinguish the Active_File's Tab from all other Tabs.
4. WHEN a user closes a Tab by clicking its close button, THE IDE SHALL remove that Tab from the Tab_Bar.
5. WHEN the last Tab is closed, THE Editor SHALL display an empty welcome state with instructional text.
6. WHEN a file's content has been modified but not saved, THE Tab_Bar SHALL display a visual indicator (e.g., a dot) on that file's Tab.
7. WHEN the same file is opened more than once from the File_Explorer, THE IDE SHALL activate the existing Tab for that file rather than opening a duplicate Tab.

---

### Requirement 4: Monaco Editor Integration

**User Story:** As a developer, I want the editor area to use Monaco Editor with full syntax highlighting and editing capabilities, so that I have a professional code editing experience.

#### Acceptance Criteria

1. THE Editor SHALL render using the Monaco Editor library loaded from `node_modules`.
2. WHEN a file is opened, THE Editor SHALL set the Language_Mode based on the file's extension (e.g., `.js` → JavaScript, `.html` → HTML, `.css` → CSS, `.ts` → TypeScript, `.json` → JSON, `.md` → Markdown).
3. THE Editor SHALL occupy all available space in the center content area after accounting for the Tab_Bar height.
4. WHEN the IDE Theme changes, THE Editor SHALL apply the corresponding Monaco Editor theme (`vs-dark` for dark mode, `vs` for light mode).
5. THE Editor SHALL preserve the scroll position and cursor position of each open file when the user switches between Tabs.
6. WHEN the user edits file content in the Editor, THE IDE SHALL mark that file as modified in the Virtual_File_System.

---

### Requirement 5: Toolbar and Menu Bar

**User Story:** As a developer, I want a toolbar with menus and common action buttons, so that I can quickly access IDE functions without memorizing keyboard shortcuts.

#### Acceptance Criteria

1. THE Toolbar SHALL display the IDE application name or logo on the left side.
2. THE Toolbar SHALL contain a "File" menu with at minimum the actions: New File, Save, and Save All.
3. THE Toolbar SHALL contain a "View" menu with at minimum the actions: Toggle File Explorer, Toggle Terminal Panel, and Toggle Theme.
4. WHEN the user selects "Save" from the File menu, THE IDE SHALL persist the Active_File's current Editor content to the Virtual_File_System and remove the modified indicator from its Tab.
5. WHEN the user selects "Save All" from the File menu, THE IDE SHALL persist all modified files' Editor content to the Virtual_File_System and remove all modified indicators from the Tab_Bar.
6. WHEN the user selects "Toggle File Explorer" from the View menu, THE File_Explorer SHALL toggle between visible and hidden states.
7. WHEN the user selects "Toggle Terminal Panel" from the View menu, THE Terminal_Panel SHALL toggle between visible and hidden states.
8. WHEN the user selects "Toggle Theme" from the View menu, THE IDE SHALL switch between the dark Theme and the light Theme.
9. WHEN a menu is open and the user clicks outside the menu, THE Toolbar SHALL close the open menu.

---

### Requirement 6: Status Bar

**User Story:** As a developer, I want a status bar at the bottom of the IDE, so that I can see contextual information about the current file and editor state at a glance.

#### Acceptance Criteria

1. THE Status_Bar SHALL display the Language_Mode of the Active_File.
2. THE Status_Bar SHALL display the current cursor line number and column number in the format `Ln {line}, Col {column}`.
3. WHEN the cursor position changes in the Editor, THE Status_Bar SHALL update the line and column display within 100ms.
4. THE Status_Bar SHALL display the current Theme name (e.g., "Dark" or "Light").
5. WHEN no file is open, THE Status_Bar SHALL display placeholder text instead of file-specific information.

---

### Requirement 7: Terminal Panel

**User Story:** As a developer, I want an integrated terminal panel at the bottom of the IDE, so that I can see simulated command output within the IDE context.

#### Acceptance Criteria

1. THE Terminal_Panel SHALL display a read-only output area styled to resemble a terminal (monospace font, dark background).
2. THE Terminal_Panel SHALL display a text input field that accepts user-typed commands.
3. WHEN the user submits a command by pressing Enter in the input field, THE Terminal_Panel SHALL echo the command to the output area prefixed with a prompt symbol (e.g., `$ `).
4. WHEN the user submits the command `clear`, THE Terminal_Panel SHALL clear all content from the output area.
5. WHEN the user submits any command other than `clear`, THE Terminal_Panel SHALL append a simulated response line to the output area (e.g., `Command '{command}' executed.`).
6. THE Terminal_Panel SHALL be vertically resizable by dragging a handle on its top edge.
7. WHEN new output is added to the Terminal_Panel, THE Terminal_Panel SHALL automatically scroll to the bottom of the output area.

---

### Requirement 8: Keyboard Shortcuts

**User Story:** As a developer, I want keyboard shortcuts for common actions, so that I can work efficiently without reaching for the mouse.

#### Acceptance Criteria

1. WHEN the user presses `Ctrl+S` (or `Cmd+S` on macOS), THE IDE SHALL save the Active_File as defined in Requirement 5, Criterion 4.
2. WHEN the user presses `Ctrl+Shift+S` (or `Cmd+Shift+S` on macOS), THE IDE SHALL save all modified files as defined in Requirement 5, Criterion 5.
3. WHEN the user presses `Ctrl+\`` (or `Cmd+\`` on macOS), THE IDE SHALL toggle the Terminal_Panel visibility as defined in Requirement 5, Criterion 7.
4. WHEN the user presses `Ctrl+W` (or `Cmd+W` on macOS) while the Editor is focused, THE IDE SHALL close the Active_File's Tab.

---

### Requirement 9: Theme Support

**User Story:** As a developer, I want to switch between dark and light themes, so that I can work comfortably in different lighting conditions.

#### Acceptance Criteria

1. THE IDE SHALL default to the dark Theme on initial load.
2. WHEN the dark Theme is active, THE IDE SHALL apply a dark color palette to all UI panels (Toolbar, File_Explorer, Tab_Bar, Status_Bar, and Terminal_Panel).
3. WHEN the light Theme is active, THE IDE SHALL apply a light color palette to all UI panels.
4. THE IDE SHALL persist the selected Theme to `localStorage` so that it is restored on the next page load.
5. WHEN the Theme is toggled, THE Editor SHALL switch between `vs-dark` and `vs` Monaco themes simultaneously with the UI Theme change.
