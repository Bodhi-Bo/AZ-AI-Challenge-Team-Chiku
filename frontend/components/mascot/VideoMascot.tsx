"use client";

import { useEffect, useRef } from "react";

interface VideoMascotProps {
  videoSrc: "normal" | "speak" | "think";
  className?: string;
  width?: number;
  height?: number;
  opacity?: number;
}

export default function VideoMascot({
  videoSrc,
  className = "",
  width = 120,
  height = 120,
  opacity = 1,
}: VideoMascotProps) {
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    // Ensure video plays seamlessly in loop
    video.play().catch((error) => {
      console.log("Auto-play prevented:", error);
    });

    // Handle end event to ensure seamless loop
    const handleEnded = () => {
      video.currentTime = 0;
      video.play();
    };

    video.addEventListener("ended", handleEnded);

    return () => {
      video.removeEventListener("ended", handleEnded);
    };
  }, [videoSrc]);

  return (
    <video
      ref={videoRef}
      className={`object-cover transition-opacity duration-500 ${className}`}
      style={{ opacity }}
      width={width}
      height={height}
      loop
      muted
      playsInline
      autoPlay
      preload="auto"
    >
      <source src={`/${videoSrc}.mp4`} type="video/mp4" />
      Your browser does not support the video tag.
    </video>
  );
}
