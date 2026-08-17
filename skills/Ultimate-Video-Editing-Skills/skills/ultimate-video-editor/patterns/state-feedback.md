# State Feedback Animation Patterns

*Source: [LottieFiles/motion-design-skill](https://github.com/LottieFiles/motion-design-skill)*

## Success State
1. **Primary**: Scale pop to 1.1 → settle to 1.0 (ease-out-back, 300ms)
2. **Secondary**: Checkmark icon draws in (200ms, 100ms delay)
3. **Ambient**: Subtle particle burst or glow
4. **Color**: Green fill transition (150ms)
5. **Total**: 300-400ms

## Error State
1. **Primary**: Horizontal shake 2-3 oscillations, ±10-15px (ease-in-out, 300-400ms)
2. **Color**: Red tint (150ms)
3. **Secondary**: Error icon appears (scale in, 200ms)
4. **No overshoot**: Errors feel firm, not bouncy
5. **Total**: 300-400ms

## Loading State
1. **Spinner**: Continuous rotation (linear easing — one of the few valid uses)
2. **Skeleton**: Shimmer gradient sweep (2-3s, sine ease-in-out loop)
3. **Progress bar**: Linear fill + subtle pulse at edges
4. **Dots**: Sequential scale pulse (100ms stagger, 1.5s cycle)

## Hover State
1. **Scale**: 1.0 → 1.02-1.05 (80-120ms, ease-out)
2. **Shadow**: Deepen/expand (120ms, ease-out)
3. **Color**: Subtle shift or lighten (80ms)
4. **Cursor**: Change on interactive elements
5. **Response**: <100ms — must feel instant

## Press/Active State
1. **Scale**: 1.0 → 0.95-0.98 (100ms, ease-out)
2. **Shadow**: Flatten/shrink (100ms)
3. **Color**: Darken (80ms)
4. **Ripple**: Expand from press point (Material Design, 300ms)
5. **Release**: Spring back with slight overshoot (200ms)

## Toggle/Switch
1. **Thumb**: Slide to new position (150ms, ease-out)
2. **Track**: Color transition (200ms)
3. **Spring**: Slight overshoot on arrival (3-5% for corporate, 10% for playful)
