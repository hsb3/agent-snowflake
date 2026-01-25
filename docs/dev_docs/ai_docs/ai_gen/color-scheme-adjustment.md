# Color Scheme Adjustment - Gray-30/Gray-90 Base

## Changes Made

Updated base colors from extreme ends (white/gray-100) to softer middle values (gray-30/gray-90).

---

## New Base Colors

### Dark Mode (Default) - Base: Gray-90

**Before**: gray-100 (`#161616`) - Very dark, almost black
**After**: gray-90 (`#262626`) - Softer dark gray

**Color Hierarchy** (darkest → lightest):
- Sunken: `#161616` (gray-100) - Depressed areas
- **Primary: `#262626` (gray-90)** - Main background ⭐ **BASE**
- Secondary: `#393939` (gray-80) - Panels, sidebar
- Tertiary: `#525252` (gray-70) - Nested content, lighter areas

**Result**: Softer, less harsh dark theme with more visible gray tones

---

### Light Mode - Base: Gray-30

**Before**: white (`#ffffff`) - Pure white, stark
**After**: gray-30 (`#c6c6c6`) - Softer light gray

**Color Hierarchy** (lightest → darkest):
- Tertiary: `#f4f4f4` (gray-10) - Lightest nested
- Secondary: `#e0e0e0` (gray-20) - Lighter panels
- **Primary: `#c6c6c6` (gray-30)** - Main background ⭐ **BASE**
- Sunken: `#f4f4f4` (gray-10) - Depressed areas

**Text Adjusted**:
- Primary: `#000000` (pure black) - Maximum contrast on gray-30
- Secondary: `#161616` (gray-100) - Very dark for muted text
- Tertiary: `#393939` (gray-80) - Dark gray for subtle

**Result**: Softer light theme, less eye strain than pure white

---

## Visual Comparison

### Dark Mode

**Old** (gray-100 base):
```
Main bg: #161616 (very dark, almost black)
Message area: #161616
Welcome box: #393939 (stark contrast against black-ish bg)
```

**New** (gray-90 base):
```
Main bg: #262626 (softer dark gray)
Message area: #262626
Welcome box: #525252 (less stark, more subtle layering)
```

### Light Mode

**Old** (white base):
```
Main bg: #ffffff (pure white, very bright)
Panels: #f4f4f4 (minimal contrast)
```

**New** (gray-30 base):
```
Main bg: #c6c6c6 (soft gray, easier on eyes)
Panels: #e0e0e0 (subtle lighter panels)
Nested: #f4f4f4 (progressive lightening)
```

---

## Textual Conflicts Resolved

### Built-in Variables Overridden

```tcss
/* We explicitly define these to override Textual defaults */
$surface:      $surface-primary;      /* Maps to our gray-90/gray-30 */
$text:         $content-primary;      /* Maps to our gray-10/black */
$text-muted:   $content-secondary;    /* Maps to our gray-30/gray-100 */
$primary:      $interactive;          /* Maps to our blue-60 */
$secondary:    $surface-secondary;    /* Maps to our gray-80/gray-20 */
$accent:       $interactive;          /* Maps to our blue-60 */
```

### Auto-generated Modifiers Overridden

Textual auto-generates these based on base colors:
- `$surface-lighten-1`, `$surface-lighten-2`, `$surface-lighten-3`
- `$surface-darken-1`, `$surface-darken-2`, `$surface-darken-3`
- Same for `$primary`, `$secondary`, etc.

**We now explicitly define them** to use our semantic tokens:
```tcss
$surface-lighten-1: $surface-secondary;   /* gray-80 in dark / gray-20 in light */
$surface-lighten-2: $surface-tertiary;    /* gray-70 in dark / gray-10 in light */
$surface-darken-1:  $surface-sunken;      /* gray-100 in dark / gray-10 in light */

$primary-lighten-1: $interactive-hover;   /* blue-50 in dark / blue-70 in light */
$primary-darken-1:  $interactive-active;  /* blue-40 in dark / blue-80 in light */
```

**Benefit**: Our Carbon colors fully control the palette, Textual doesn't inject its own calculated values

---

## Expected Visual Changes

### You Should See

**Dark Mode** (Ctrl+D if in light):
- Main background: Medium-dark gray (`#262626`), not almost-black
- Welcome message box: Lighter gray (`#525252`), better layering
- More visible gray tones throughout
- Softer, less harsh appearance

**Light Mode** (Ctrl+D to toggle):
- Main background: Light gray (`#c6c6c6`), not pure white
- Text: Pure black (`#000000`), excellent readability
- Progressive lightening in panels
- Easier on eyes than stark white

---

## Color Reference

### Dark Mode (gray-90 base)

| Element | Color | Hex | Carbon Token |
|---------|-------|-----|--------------|
| Main background | Dark gray | `#262626` | gray-90 |
| Sidebar/panels | Lighter gray | `#393939` | gray-80 |
| Nested content | Mid gray | `#525252` | gray-70 |
| Sunken areas | Very dark | `#161616` | gray-100 |
| Primary text | Light gray | `#f4f4f4` | gray-10 |
| Muted text | Mid gray | `#c6c6c6` | gray-30 |

### Light Mode (gray-30 base)

| Element | Color | Hex | Carbon Token |
|---------|-------|-----|--------------|
| Main background | Light gray | `#c6c6c6` | gray-30 |
| Sidebar/panels | Lighter | `#e0e0e0` | gray-20 |
| Nested content | Lightest | `#f4f4f4` | gray-10 |
| Primary text | Black | `#000000` | black |
| Muted text | Very dark | `#161616` | gray-100 |

### Status Colors (Same in Both Modes)

| Purpose | Color | Hex | Carbon Token |
|---------|-------|-----|--------------|
| Success | Green | `#42be65` | green-40 |
| Error | Red | `#da1e28` | red-60 |
| Warning | Yellow | `#f1c21b` | yellow-30 |
| Info | Blue | `#4589ff` | blue-50 |

---

## Benefits

1. **Softer appearance** - Less extreme contrast
2. **Better layering** - More visible depth with gray tones
3. **Reduced eye strain** - Neither pure black nor pure white
4. **Professional** - Matches modern design trends (Discord, VS Code use gray bases)
5. **Carbon-compliant** - Still using Carbon Design System palette
6. **No Textual conflicts** - Our tokens fully override built-in auto-generation

---

## Testing

```bash
make tui-dev
```

1. Check dark mode appearance (default)
2. Press **Ctrl+D** to toggle to light mode
3. Check light mode appearance
4. Press **Ctrl+D** again to toggle back

**Quality checks**:
```bash
make check-repl
```

All tests should still pass (color values don't affect functionality).

---

## What Was Fixed

1. ✅ **Base colors softened** - gray-30/gray-90 instead of white/gray-100
2. ✅ **Text contrast adjusted** - Pure black on gray-30 in light mode
3. ✅ **Textual overrides added** - Prevent auto-generated color modifiers
4. ✅ **Semantic tokens preserved** - Still using Carbon Design System
5. ✅ **Layer hierarchy clear** - Sunken → Primary → Secondary → Tertiary

The TUI should now have a softer, more polished appearance with better visual hierarchy!
