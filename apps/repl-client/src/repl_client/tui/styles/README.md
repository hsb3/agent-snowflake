# TUI Styles - Modular CSS Organization

Textual CSS files for the REPL TUI, organized into semantic modules.

## File Structure

```
styles/
├── theme.tcss       # Design tokens (colors, semantic variables) - FIRST
├── layout.tcss      # Screen structure, containers, layout rules
├── components.tcss  # Widget styling (messages, inputs, status)
├── sidebar.tcss     # Sidebar widget styles
├── modals.tcss      # Modal screens (command palette, selection)
├── states.tcss      # Focus, hover, status states
├── light-mode.tcss  # Light theme overrides - LAST
├── index.tcss       # BUILD OUTPUT (concatenated, loaded by app)
└── README.md        # This file
```

## Build Process

Textual CSS doesn't support `@import`, so modular files are **concatenated** into `index.tcss`:

```bash
make build-css  # Concatenates: theme → layout → components → sidebar → modals → states → light-mode
```

The order matters - theme.tcss must be first to define variables before use.

**After editing any `.tcss` file, run `make build-css` to rebuild `index.tcss`.**

## Design System

Based on [Carbon Design System](https://carbondesignsystem.com/guidelines/color/usage/) (IBM).

### Semantic Variables (theme.tcss)

**Surfaces:**
- `$surface-primary` - Main background (gray-90 dark, gray-30 light)
- `$surface-secondary` - Panels, cards (gray-80 dark)
- `$surface-tertiary` - Nested content (gray-70 dark)

**Text:**
- `$text-primary` - Main text (gray-10 dark)
- `$text-secondary` - Secondary text (gray-30 dark)
- `$text-tertiary` - Subtle text (gray-40 dark)

**Interactive:**
- `$interactive` - Primary interactive color (blue-60)
- `$interactive-hover` - Hover state (blue-50 dark)

**Status:**
- `$status-success` - Success (green-40)
- `$status-error` - Error (red-60)
- `$status-warning` - Warning (yellow-30)
- `$status-info` - Info (blue-50)

**Borders:**
- `$border-subtle` - Subtle borders (gray-80 dark)
- `$border-default` - Default borders (gray-70 dark)

### Light Mode

Light mode variables are defined with `-light` suffix and used in `light-mode.tcss` with `:light` pseudo-class:

```css
/* In theme.tcss */
$surface-primary-light: $gray-30;

/* In light-mode.tcss */
Screen:light #message-area {
    background: $surface-primary-light;
}
```

## Modifying Styles

1. **Variables** - Edit `theme.tcss` for colors, design tokens
2. **Layout** - Edit `layout.tcss` for screen structure
3. **Components** - Edit `components.tcss` for widget appearance
4. **Modals** - Edit `modals.tcss` for modal screens
5. **States** - Edit `states.tcss` for focus/hover/status
6. **Light mode** - Edit `light-mode.tcss` for light theme

## Textual CSS Reference

- [Design System](https://textual.textualize.io/guide/design/)
- [CSS Reference](https://textual.textualize.io/guide/CSS/)
- [Styles Reference](https://textual.textualize.io/styles/)
