"use client";

import { useEffect, useRef, useState } from "react";

interface SmoothVideoMascotProps {
  videoSrc: "normal" | "speak" | "think";
  className?: string;
  width?: number;
  height?: number;
}

export default function SmoothVideoMascot({
  videoSrc,
  className = "",
  width = 320,
  height = 320,
}: SmoothVideoMascotProps) {
  const [activeVideo, setActiveVideo] = useState<"normal" | "speak" | "think">(
    videoSrc
  );

  const normalRef = useRef<HTMLVideoElement>(null);
  const speakRef = useRef<HTMLVideoElement>(null);
  const thinkRef = useRef<HTMLVideoElement>(null);
  const transitionTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Preload and loop all videos
  useEffect(() => {
    const videos = [normalRef.current, speakRef.current, thinkRef.current];

    videos.forEach((video) => {
      if (!video) return;

      const handleEnded = () => {
        video.currentTime = 0;
        video.play().catch(console.error);
      };

      video.addEventListener("ended", handleEnded);
      video.play().catch(console.error);

      return () => {
        video.removeEventListener("ended", handleEnded);
      };
    });
  }, []);

  // Handle video changes with smooth transition
  useEffect(() => {
    if (videoSrc === activeVideo) return;

    // Clear any existing transition
    if (transitionTimerRef.current) {
      clearTimeout(transitionTimerRef.current);
    }

    // Delay the state change to create crossfade effect
    transitionTimerRef.current = setTimeout(() => {
      setActiveVideo(videoSrc);
    }, 100);

    return () => {
      if (transitionTimerRef.current) {
        clearTimeout(transitionTimerRef.current);
      }
    };
  }, [videoSrc, activeVideo]);

  return (
    <div className={`relative ${className}`} style={{ width, height }}>
      {/* All videos stacked, only one visible at a time with smooth transitions */}
      <video
        ref={normalRef}
        className="absolute inset-0 object-cover transition-opacity duration-700 ease-in-out"
        style={{ opacity: activeVideo === "normal" ? 1 : 0 }}
        width={width}
        height={height}
        loop
        muted
        playsInline
        autoPlay
        preload="auto"
      >
        <source src="/normal.mp4" type="video/mp4" />
      </video>

      <video
        ref={speakRef}
        className="absolute inset-0 object-cover transition-opacity duration-700 ease-in-out"
        style={{ opacity: activeVideo === "speak" ? 1 : 0 }}
        width={width}
        height={height}
        loop
        muted
        playsInline
        autoPlay
        preload="auto"
      >
        <source src="/speak.mp4" type="video/mp4" />
      </video>

      <video
        ref={thinkRef}
        className="absolute inset-0 object-cover transition-opacity duration-700 ease-in-out"
        style={{ opacity: activeVideo === "think" ? 1 : 0 }}
        width={width}
        height={height}
        loop
        muted
        playsInline
        autoPlay
        preload="auto"
      >
        <source src="/think.mp4" type="video/mp4" />
      </video>
    </div>
  );
}
