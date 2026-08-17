# Entrance & Exit Animation Patterns

*Source: [LottieFiles/motion-design-skill](https://github.com/LottieFiles/motion-design-skill)*

## Entrance Strategies

### 1. Direct Entrance (Slide In)
Position + opacity; offset 20-40px + opacity 0 → final position + opacity 1.
Easing: ease-out; duration 200-350ms.

| Personality | Offset | Easing | Overshoot |
|------------|--------|--------|-----------|
| Playful | 30-50px | ease-out-back | 10-15% |
| Premium | 15-25px | (0.4, 0, 0.2, 1) | 0% |
| Corporate | 20-30px | (0.2, 0, 0, 1) | 0-3% |
| Energetic | 40-80px | ease-out-expo | 15-25% |

Direction meaning: below=arrival, right=forward, left=back, above=dropdown/authority.

### 2. Emergent Entrance (Scale In)
Scale + opacity; start 85-95% + opacity 0 → 100% + opacity 1.
Duration 250-400ms. Best for: modals, dialogs, notifications, popovers.

### 3. Reveal Entrance (Clip/Mask)
clip-path or mask + opacity; 300-500ms, ease-out.
Directions: top-to-bottom (dramatic), left-to-right (reading order), center-out (focus).

### 4. Assembled Entrance (Multi-Part)
Parts arrive from different positions; stagger 50-100ms; total 300-600ms.
Best for: icon assembly, logo builds, data visualization construction.

## Exit Strategies

**Rule**: Exits = 65-75% of entrance duration.

### 1. Direct Exit (Slide Out)
Offset 20-40px + opacity 0; ease-in; 150-250ms.

### 2. Dissolve Exit (Fade Out)
Opacity (+ optional scale to 98%); ease-in; 150-250ms.
Best for: gentle departures, crossfades.

### 3. Collapse Exit (Shrink Out)
Scale 85-95% + opacity 0; ease-in; 150-250ms.
Best for: deletion, closing modals, dismissal.

### 4. Transfer Exit (Move Away)
Position toward destination + scale shrink; ease-in-out; 250-400ms.
Best for: add-to-cart, save-to-collection, move-to-folder.

## Entrance-Exit Continuity
- Eye follows naturally from exit to entrance
- Exit point near entry point when possible
- 100-150ms timing overlap between exit and entrance
- Same easing family for paired entrance-exit

## Common Recipes

### Notification Slide-In
1. Slide from right + opacity (250ms, ease-out)
2. Overshoot 3-5% (corporate) or 10-15% (playful)
3. Icon appears (100ms, 50ms delay)

### Lower Third (Video)
1. Bar slides from left (250ms, ease-out)
2. Name text fades in (150ms, 80ms delay)
3. Title text fades in (150ms, 120ms delay)
4. Hold 3-5 seconds
5. All slide left + fade (180ms, ease-in)

### Title Card Reveal
1. Background fades in (300ms)
2. Main title scales from 95% + opacity (400ms, ease-out, 200ms delay)
3. Subtitle slides up + opacity (300ms, ease-out, 400ms delay)
4. Decorative elements stagger (50ms each, 500ms delay)

### Page Transition (Forward)
1. Current page slides left + fades (300ms, ease-in)
2. New page slides from right (350ms, ease-out, 100ms overlap)
3. Elements on new page stagger in (50ms each, after page settles)
