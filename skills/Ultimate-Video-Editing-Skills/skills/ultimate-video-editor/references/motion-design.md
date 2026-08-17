# Motion Design Complete Reference

*Source: [LottieFiles/motion-design-skill](https://github.com/LottieFiles/motion-design-skill) + [iart-ai/motion-skills](https://github.com/iart-ai/motion-skills)*

## Disney's 12 Principles — Full Reference

### 1. Squash and Stretch
- Squash: scale ~[1.2, 0.8]; Stretch: ~[0.85, 1.15]
- Impact: 2-4 frames (30-65ms); Recovery: 4-8 frames (65-130ms)
- Preserve volume: width +20% → height decreases proportionally
- Skip for premium/luxury brands

### 2. Anticipation
- Small motion opposite to main direction before action
- Duration: 100-200ms, magnitude: 10-20% of main action
- Button: scale down 3% before expanding; Card: shift 5-10px away first
- Skip for micro-feedback (<150ms)

### 3. Staging
- Dim non-hero elements to 40-60% opacity; optional 2-4px blur
- Hero enters 100-200ms after supporting elements
- One primary action per timing beat

### 4. Straight Ahead vs. Pose to Pose
| Approach | Feel | Best For |
|----------|------|----------|
| Straight Ahead | Fluid, spontaneous | Particles, ambient, generative art |
| Pose to Pose | Planned, controlled | UI transitions, state changes |

### 5. Follow Through and Overlapping Action
- Child delay: 50-150ms behind parent
- Trailing elements: offset stop times by 100-200ms
- Use spring easing for trailing parts (lower stiffness = more trailing)

### 6. Slow In and Slow Out
| Context | Easing | Why |
|---------|--------|-----|
| Entrance | ease-out | Arrives smoothly |
| Exit | ease-in | Departs quickly |
| On-screen | ease-in-out | Smooth journey |
| Ambient loop | sine ease-in-out | Seamless |

**NEVER** linear for spatial movement. Linear only for: rotation, progress bars, timers.

### 7. Arcs
- Add 10-20px perpendicular offset at path midpoint
- Subtle (5px) for corporate, pronounced (20px+) for playful
- Mechanical UIs can use straight paths intentionally

### 8. Secondary Action
- Amplitude: 30-50% of primary; timing: 50-100ms after primary
- Different easing than primary
- Examples: card enters → shadow grows; button presses → ripple expands

### 9. Timing
| Weight/Mood | Duration |
|-------------|----------|
| Heavy (modals, pages) | 400-800ms |
| Light (tooltips, toggles) | 100-250ms |
| Sad/serious | 600ms+ |
| Happy/light | 200-400ms |
| Urgent | 100-200ms |

Enter-exit asymmetry: entrances 30-50% longer than exits.

### 10. Exaggeration
| Personality | Exaggeration |
|-------------|-------------|
| Playful | 15-25% |
| Energetic | 20-30% |
| Corporate | 0-5% |
| Premium | 0% |

Scale overshoot: 10-30% beyond target; rotation: ±5-15°

### 11. Solid Drawing
Consistent visual weight and perspective. In UI: consistent shadow direction, depth relationships, and visual hierarchy across all animated elements.

### 12. Appeal
Clean, readable, satisfying movement. No janky frames, no confusing motion paths. The viewer should enjoy watching the animation, even subconsciously.

---

## Choreography Deep Dive

### Coordinated Entry Rules
1. **Lead with the Hero** — largest displacement, most attention-grabbing easing
2. **Spatial Origin Consistency** — all elements enter from same direction. Mixed = chaos.
3. **Counter-Motion** — hero moves right → background shifts left at 20-30% speed

### Sequence Structure
| Phase | Share | What Happens |
|-------|-------|-------------|
| Setup | 20-30% | Elements enter, scene establishes |
| Action | 30-40% | Primary motion, hero moment |
| Resolution | 30-40% | Settle, secondary reactions, breathing |

Leave 100-200ms stillness after resolution before new motion.

### Stagger Patterns
| Pattern | Description | Best For |
|---------|------------|----------|
| Sequential | Reading order | Lists, grids, navigation |
| Center-out | Radiating from center | Hero content, ripples |
| Random | Varied timing | Organic, particle-like |
| Wave | Sine-based | Data bars, continuous |
| Reverse | Bottom-to-top | Exits, backward navigation |

### Depth Through Speed (Parallax)
| Layer | Displacement | Speed |
|-------|-------------|-------|
| Foreground | 1.0x | Fastest |
| Midground | 0.5x | Medium |
| Background | 0.2x | Slowest |

---

## Material-Based Easing
| Material | Duration Scale | Overshoot | Character |
|----------|---------------|-----------|-----------|
| Rigid (metal, stone) | 1.2x | 0% | Hard stops, no flex |
| Elastic (rubber, gel) | 0.8x | 15-25% | Bouncy, stretchy |
| Fluid (water, paint) | 1.5x | 5% | Flowing, viscous |
| Paper (cards, sheets) | 1.0x | 3-5% | Light, crisp |
| Gas (smoke, fog) | 2.0x | 0% | Diffuse, slow |
| Glass (brittle) | 0.9x | 0% | Sharp, clean |

---

## Property Selection Guide
| Effect Goal | Primary Property | Secondary |
|-------------|------------------|-----------|
| Entrance/Exit | position | opacity, scale |
| Emphasis | scale | rotation (subtle), opacity pulse |
| State Change | opacity, color | scale (press feedback) |
| Direction/Flow | position | rotation (follow path) |
| Depth/3D | scale + shadow | position (parallax) |
| Loading | rotation (spinner) | scale, opacity pulse |
| Success | scale (pop) | color, rotation (checkmark) |
| Error | position (shake) | color, rotation (wobble) |

**Simplicity**: 1 property = direct. 2 = polished. 3+ = potentially overwhelming.

---

## Emotion-to-Motion Translation
| Emotion | Character | Path Shape | Easing | Duration | Color |
|---------|-----------|------------|--------|----------|-------|
| Joy | Bouncy, arcs | Curved upward | ease-out-back | 200-400ms | Warm, bright |
| Calm | Smooth, flowing | Gentle curves | sine ease-in-out | 500-1000ms | Cool, muted |
| Urgency | Sharp, fast | Straight lines | ease-out | 100-200ms | Red, high contrast |
| Sadness | Slow, heavy | Drooping curves | cubic ease-in-out | 600-1200ms | Blue, desaturated |
| Surprise | Sudden, expanding | Radial outward | ease-out-expo | 150-300ms | Bright, flash |
| Elegance | Slow, controlled | Long arcs | (0.4,0,0.2,1) | 400-700ms | Gold, black, white |
| Playfulness | Bouncy, irregular | Arcs, squiggly | ease-out-back | 200-350ms | Vivid, varied |

**Path as language**: Angular = tense. Curved = friendly. Spiral = whimsical. Diagonal = purposeful. Vertical = growth/weight. Horizontal = progress.
