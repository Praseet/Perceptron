import type { ChangeEvent } from "react";
import { cn } from "./cn";

// H.2.1: single-handle range only.
interface SliderProps {
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  step?: number;
  disabled?: boolean;
  className?: string;
  id?: string;
}

export function Slider({
  value,
  onChange,
  min = 0,
  max = 100,
  step = 1,
  disabled,
  className,
  id,
}: SliderProps) {
  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    onChange(Number(e.target.value));
  };
  // H.2.4: no box-shadow, no transform, no gradient. Single-handle
  // native <input type="range"> styled with token colors only.
  return (
    <input
      id={id}
      type="range"
      min={min}
      max={max}
      step={step}
      value={value}
      onChange={handleChange}
      disabled={disabled}
      className={cn(
        "w-full h-2 appearance-none cursor-pointer",
        "bg-[var(--bg-elevated)]",
        "rounded-full",
        "disabled:opacity-50 disabled:cursor-not-allowed",
        "[&::-webkit-slider-thumb]:appearance-none",
        "[&::-webkit-slider-thumb]:w-4",
        "[&::-webkit-slider-thumb]:h-4",
        "[&::-webkit-slider-thumb]:rounded-full",
        "[&::-webkit-slider-thumb]:bg-[var(--accent-cyan)]",
        "[&::-moz-range-thumb]:w-4",
        "[&::-moz-range-thumb]:h-4",
        "[&::-moz-range-thumb]:rounded-full",
        "[&::-moz-range-thumb]:bg-[var(--accent-cyan)]",
        "[&::-moz-range-thumb]:border-0",
        className,
      )}
    />
  );
}