# Remotion — Programmatic Video with React

## What is Remotion?
Remotion lets you create videos using React components. Write JSX/CSS, render MP4. Perfect for:
- Data-driven videos (dashboards, reports)
- Batch personalized videos (1000s of variations)
- Animated explainers and motion graphics
- AI-generated video content

## Setup
```bash
npx create-video@latest my-video
cd my-video
npm start        # Preview in browser
npx remotion render src/index.ts MyComp out.mp4  # Render
```

## Core Concepts

### Composition = Video Definition
```tsx
import { Composition } from "remotion";

export const RemotionRoot = () => (
  <Composition
    id="MyVideo"
    component={MyVideo}
    durationInFrames={150}  // 5 seconds at 30fps
    fps={30}
    width={1080}
    height={1920}
  />
);
```

### useCurrentFrame = Animation Driver
```tsx
import { useCurrentFrame, interpolate, spring, useVideoConfig } from "remotion";

const MyVideo = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  
  // Linear interpolation (0 → 1 over frames 0-30)
  const opacity = interpolate(frame, [0, 30], [0, 1], {
    extrapolateRight: "clamp",
  });
  
  // Spring animation (bouncy entrance)
  const scale = spring({ frame, fps, config: { damping: 10, stiffness: 100 } });
  
  return (
    <div style={{ opacity, transform: `scale(${scale})` }}>
      <h1>Hello World</h1>
    </div>
  );
};
```

### Sequence = Timing Sections
```tsx
import { Sequence } from "remotion";

const MyVideo = () => (
  <>
    <Sequence from={0} durationInFrames={60}>
      <TitleCard text="Introduction" />
    </Sequence>
    <Sequence from={60} durationInFrames={90}>
      <MainContent />
    </Sequence>
    <Sequence from={150} durationInFrames={60}>
      <OutroCard />
    </Sequence>
  </>
);
```

### Audio & Video
```tsx
import { Audio, Video, OffthreadVideo, staticFile } from "remotion";

// Background music
<Audio src={staticFile("music.mp3")} volume={0.3} />

// Video clip
<OffthreadVideo src={staticFile("footage.mp4")} />

// Volume animation (fade in)
<Audio src={src} volume={(f) => interpolate(f, [0, 30], [0, 1], { extrapolateRight: "clamp" })} />
```

## Useful Patterns

### Animated Text (Word by Word)
```tsx
const AnimatedText = ({ text }: { text: string }) => {
  const frame = useCurrentFrame();
  const words = text.split(" ");
  
  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 12, justifyContent: "center" }}>
      {words.map((word, i) => {
        const delay = i * 5;
        const opacity = interpolate(frame - delay, [0, 10], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
        const y = interpolate(frame - delay, [0, 10], [20, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
        
        return (
          <span key={i} style={{ opacity, transform: `translateY(${y}px)`, fontSize: 48, color: "white", fontWeight: "bold" }}>
            {word}
          </span>
        );
      })}
    </div>
  );
};
```

### Karaoke Captions
```tsx
const KaraokeCaptions = ({ words }: { words: { text: string; start: number; end: number }[] }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTime = frame / fps;
  
  const currentGroup = words.filter(w => w.start <= currentTime && w.end >= currentTime);
  
  return (
    <div style={{ position: "absolute", bottom: 200, width: "100%", textAlign: "center" }}>
      {currentGroup.map((word, i) => (
        <span key={i} style={{
          fontSize: 48,
          fontWeight: "bold",
          color: currentTime >= word.start ? "#FFD700" : "white",
          textShadow: "2px 2px 4px rgba(0,0,0,0.8)",
          margin: "0 6px",
        }}>
          {word.text}
        </span>
      ))}
    </div>
  );
};
```

### Progress Bar
```tsx
const ProgressBar = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const progress = (frame / durationInFrames) * 100;
  
  return (
    <div style={{ position: "absolute", bottom: 0, left: 0, width: "100%", height: 4, backgroundColor: "rgba(255,255,255,0.3)" }}>
      <div style={{ width: `${progress}%`, height: "100%", backgroundColor: "#FF6B00" }} />
    </div>
  );
};
```

## Rendering

### CLI Render
```bash
# MP4 output
npx remotion render src/index.ts MyVideo output.mp4

# Custom resolution
npx remotion render src/index.ts MyVideo output.mp4 --width 1080 --height 1920

# GIF
npx remotion render src/index.ts MyVideo output.gif --image-format png

# Still frame (thumbnail)
npx remotion still src/index.ts MyVideo thumb.png --frame 30
```

### Lambda (Cloud Rendering)
```bash
# Deploy to AWS Lambda for fast parallel rendering
npx remotion lambda deploy
npx remotion lambda render --function-name my-func src/index.ts MyVideo
```

## When to Use Remotion vs FFmpeg

| Task | Best Tool | Why |
|------|-----------|-----|
| Color grade existing footage | FFmpeg | Filter chains, no React needed |
| Animated text/captions | Remotion | CSS animations, font control |
| Data-driven video | Remotion | React data binding |
| Batch grade 100 videos | FFmpeg | Simple loop, fast |
| Batch generate 100 personalized videos | Remotion | Props, templates |
| Trim/concat/speed | FFmpeg | Native, fast |
| Complex motion graphics | Remotion | React ecosystem |
| Quick social media export | FFmpeg | One command |
