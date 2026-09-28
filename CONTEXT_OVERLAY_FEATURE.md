# Context Overlay Feature

## Overview
Added a full-screen overlay for editing meeting context, providing more space for longer context descriptions while keeping the main UI compact.

## Feature Description

The Context text area in the main UI now has an **"⛶ Expand"** button that opens a full-screen overlay window for comfortable editing of longer context text.

## UI Components

### Main UI
- **Small text area** (80px height) - Compact, fits perfectly in the UI
- **"⛶ Expand" button** - Opens the full-screen overlay

### Overlay Window
- **Size**: 900x700 pixels, centered on screen
- **Modal**: Blocks interaction with main window until closed
- **Header**: Title + info text + close button (✕)
- **Large text area**: Full-height editor with word wrap
- **Footer**: Character count + action buttons

## Buttons

| Button | Function | Shortcut |
|--------|----------|----------|
| **✕** (top-right) | Close without saving | ESC, Cmd/Ctrl+W |
| **Clear** | Clear all text | - |
| **Cancel** | Close without saving | ESC |
| **Save & Close** | Save changes and close | Cmd/Ctrl+S |

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Escape` | Close overlay (no save) |
| `Cmd+W` / `Ctrl+W` | Close overlay (no save) |
| `Cmd+S` / `Ctrl+S` | Save and close |

## Features

1. **Character Counter** - Shows real-time character count in footer
2. **Auto-focus** - Text area is automatically focused when opened
3. **Content Sync** - Current context is loaded into overlay
4. **Modal Dialog** - Prevents interaction with main window
5. **Centered Window** - Always appears in center of screen
6. **Word Wrap** - Text wraps for comfortable reading
7. **Larger Font** - 14pt font for better readability

## User Workflow

1. User types a short context in the main UI text area
2. If they need more space, they click **"⛶ Expand"**
3. Overlay opens with current text
4. User edits in the large text area
5. User clicks **"Save & Close"** or presses `Cmd+S`
6. Text is copied back to main UI
7. Overlay closes

## Use Cases

### Short Context (Main UI)
```
Focus on blockers and action items
```

### Long Context (Overlay)
```
This is a sprint planning meeting for Q1 2026. Please focus on:

1. Action items for the frontend team, especially React component refactoring
2. Backend API changes that need coordination
3. Any blockers related to the database migration
4. Timeline commitments for the mobile app release

Also pay attention to any decisions about the tech stack and architecture changes.
Do not include routine status updates unless they relate to blockers.
```

## Benefits

1. **Compact Main UI** - Keeps the main interface clean and uncluttered
2. **Comfortable Editing** - Large overlay for writing detailed context
3. **No Loss of Space** - Only opens when needed
4. **Better UX** - Users can focus on writing without UI distractions
5. **Character Counter** - Helps users gauge context length
6. **Keyboard-friendly** - Power users can use shortcuts

## Technical Details

### Implementation
- Uses `ctk.CTkToplevel` for overlay window
- `transient()` makes it a child of main window
- `grab_set()` makes it modal (blocks main window)
- Dynamic character counting with key release binding
- Content synchronization between main and overlay text areas

### Window Management
- Centered using screen dimensions
- Modal prevents multi-window confusion
- Close button in multiple locations (header, footer, keyboard)
- Automatic cleanup on close

## Future Enhancements

Possible additions:
- [ ] Templates/snippets for common contexts
- [ ] Save favorite contexts for reuse
- [ ] AI-powered context suggestions
- [ ] Format toolbar (bold, lists, etc.)
- [ ] Preview mode showing how context affects summary
- [ ] History of previous contexts
- [ ] Import context from file
- [ ] Markdown support with preview

## Testing

Test the feature:

1. **Open overlay**:
   - Launch app: `python -m src.ui.app`
   - Type some text in Context field
   - Click "⛶ Expand" button
   - Verify overlay opens centered

2. **Edit text**:
   - Type/edit in overlay
   - Check character count updates
   - Try keyboard shortcuts

3. **Save changes**:
   - Click "Save & Close"
   - Verify text appears in main UI

4. **Cancel changes**:
   - Open overlay
   - Edit text
   - Click "Cancel" or press ESC
   - Verify changes are not saved

5. **Clear button**:
   - Open overlay with text
   - Click "Clear"
   - Verify text is removed
   - Cancel to restore

## Accessibility

- Large font (14pt) for readability
- Clear visual hierarchy with header/footer
- Multiple ways to perform actions (mouse, keyboard)
- Character counter helps users stay aware of content length
- Word wrap prevents horizontal scrolling

## Code Location

**File**: `src/ui/app.py`

**Methods**:
- `_create_settings_section()` - Adds expand button
- `_open_context_overlay()` - Creates and manages overlay window

## Screenshots

```
Main UI (Compact):
┌─────────────────────────────────┐
│ Context:  [___________________] │
│           [___________________] │  <- 80px height
│           [___________________] │
│           [ ⛶ Expand ]          │
└─────────────────────────────────┘

Overlay (Full View):
┌──────────────────────────────────────────────────────┐
│ Meeting Context                               [✕]    │
│ Add context to guide the AI...                       │
├──────────────────────────────────────────────────────┤
│                                                      │
│  [                                                   │
│                                                      │
│   Large text area with plenty of space              │
│   for detailed context...                           │
│                                                      │
│                                                   ]  │
│                                                      │
├──────────────────────────────────────────────────────┤
│ Characters: 125      [Clear] [Cancel] [Save & Close]│
└──────────────────────────────────────────────────────┘
```

## User Feedback

This feature addresses:
- ✅ "Context box is too small for detailed instructions"
- ✅ "I need more space to write meeting context"
- ✅ "Can't see all my context at once"
- ✅ "UI feels cramped when writing long context"

## Backward Compatibility

✅ Fully backward compatible:
- Existing functionality unchanged
- Small text area still works as before
- Overlay is optional (only opens on click)
- No breaking changes to data format


