"use client";

import { useEffect, useRef } from "react";

export default function AuroraWake() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Set canvas dimensions
    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resizeCanvas();

    // Debounced resize listener
    let resizeTimeout: NodeJS.Timeout;
    const handleResize = () => {
      clearTimeout(resizeTimeout);
      resizeTimeout = setTimeout(resizeCanvas, 150);
    };
    window.addEventListener("resize", handleResize);

    // Path tracking
    const path: { x: number; y: number }[] = [];
    const maxPoints = 32;

    const handleMouseMove = (e: MouseEvent) => {
      path.push({ x: e.clientX, y: e.clientY });
      if (path.length > maxPoints) {
        path.shift();
      }
    };
    window.addEventListener("mousemove", handleMouseMove, { passive: true });

    // RAF Loop
    let animationFrameId: number;

    const render = () => {
      // 1. Fade mechanic
      ctx.fillStyle = "rgba(10, 5, 20, 0.18)";
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // 2. Draw stroke if enough points
      if (path.length >= 2) {
        const first = path[0];
        const last = path[path.length - 1];

        // 3. Build gradient
        const gradient = ctx.createLinearGradient(first.x, first.y, last.x, last.y);
        gradient.addColorStop(0, "rgba(192, 132, 252, 0)");
        gradient.addColorStop(0.4, "rgba(192, 132, 252, 0.6)");
        gradient.addColorStop(1, "rgba(244, 114, 182, 0.9)");

        // 5. Glow pass (must be before stroke)
        ctx.shadowBlur = 12;
        ctx.shadowColor = "#C084FC";

        // 4. Draw stroke
        ctx.beginPath();
        ctx.moveTo(first.x, first.y);
        for (let i = 1; i < path.length; i++) {
          ctx.lineTo(path[i].x, path[i].y);
        }
        
        ctx.strokeStyle = gradient;
        ctx.lineWidth = 3;
        ctx.lineCap = "round";
        ctx.lineJoin = "round";
        ctx.stroke();

        // Reset shadow for next frame's fillRect
        ctx.shadowBlur = 0;
      }

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    // Cleanup
    return () => {
      window.removeEventListener("resize", handleResize);
      window.removeEventListener("mousemove", handleMouseMove);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 w-full h-full pointer-events-none z-10"
      // If the fillRect accumulates and hides the UI, mix-blend-mode screen prevents the dark color from accumulating opaquely over bright UI
      style={{ mixBlendMode: "screen" }} 
    />
  );
}
