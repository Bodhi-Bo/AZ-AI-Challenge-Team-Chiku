# Chiku Mascot Image Mapping

This document shows how the mascot images are mapped to different emotions.

## Image to Emotion Mapping

| Emotion       | Image File                | Description                   |
| ------------- | ------------------------- | ----------------------------- |
| `idle`        | `Neutral peaceful,.jpg`   | Calm, neutral expression      |
| `happy`       | `Happy.jpg`               | Joyful, smiling               |
| `thinking`    | `Gentle.jpg`              | Thoughtful, gentle expression |
| `celebrating` | `Happy and surprised.jpg` | Excited, surprised happiness  |
| `tired`       | `Slightly uneasy.jpg`     | Uneasy, tired look            |
| `encouraging` | `Winking.jpg`             | Winking, encouraging          |
| `sleeping`    | `Gentle.jpg`              | Peaceful, resting             |

## Available Images (Not Currently Used)

These images are available but not currently mapped to emotions:

- `Mildly surprised.jpg`
- `Shocked.jpg`
- `Small smile.jpg`
- `Worried.jpg`

## Custom Emotion Mapping

You can easily customize the emotion mapping by editing the `emotionImageMap` in `components/ChikuMascot.tsx`:

```tsx
const emotionImageMap: Record<EmotionType, string> = {
  idle: "Neutral peaceful,.jpg",
  happy: "Happy.jpg",
  // Add your custom mappings here
};
```

## Adding New Emotions

To add new emotions:

1. Add the emotion type to `EmotionType` in both files:

   - `components/ChikuMascot.tsx`
   - `lib/mascotStore.ts`

2. Add the emotion message to `emotionMessages`

3. Add the image mapping to `emotionImageMap`

4. Add a glow color to `getEmotionGlow()`

5. (Optional) Add custom animations/effects for the emotion
