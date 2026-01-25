# TUI Styles - Modular CSS Organization

This directory contains the CSS styling for the REPL TUI, organized into modular sections for better maintainability.

## File Structure

### `index.tcss` (Master file - USED BY APP)
The main CSS file loaded by `app.py`. Contains all styles organized into four logical sections:

1. **Theme** - Design tokens and color variables
2. **Layout** - Screen structure and container layout rules
3. **Components** - Widget-specific styling
4. **States** - State-based styling (focus, hover, error states)

**Note:** Textual CSS does not support `@import` statements, so all styles are consolidated in this single file with clear section boundaries.

### Individual Section Files (Reference Only)

The following files serve as documentation and reference for each CSS section:

- `theme.tcss` - Theme section reference
- `layout.tcss` - Layout section reference
- `components.tcss` - Components section reference
- `states.tcss` - States section reference

These files are NOT directly imported but contain the same CSS found in their respective sections of `index.tcss`. They exist to:
- Document the modular organization
- Make it easier to locate specific styles
- Support future refactoring if Textual adds import support
- Provide clear separation of concerns

## Usage

The app loads CSS via:
```python
# src/repl_client/tui/app.py
CSS_PATH = "styles/index.tcss"
```

## Modifying Styles

When making CSS changes:

1. **Edit `index.tcss`** - This is the file actually used by the app
2. **Update corresponding section file** - Keep reference files in sync (optional but recommended)
3. **Follow section organization** - Keep styles in their appropriate sections:
   - Theme: Color variables, design tokens
   - Layout: Screen structure, grid/dock/height/width
   - Components: Widget-specific appearance
   - States: Focus, hover, error, etc.

## Benefits of This Organization

- **Easier navigation** - Find styles by category
- **Clearer intent** - Separate layout from appearance from interaction
- **Better maintainability** - Change theme without affecting layout
- **Future-ready** - If Textual adds import support, easy to split
- **Documentation** - Section files serve as living documentation

## Migration Notes

This directory was created in Phase 1 of the TUI refactor (2026-01-24) by splitting the monolithic `repl.tcss` file. The old file has been deprecated but kept for reference until Phase 2 is complete.
