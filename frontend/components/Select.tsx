"use client";

import { useEffect, useRef, useState } from "react";

export interface SelectOption {
  value: string;
  label: string;
}

interface SelectProps {
  value: string;
  onChange: (value: string) => void;
  options: SelectOption[];
  placeholder?: string;
}


export default function Select({ value, onChange, options, placeholder = "Select..." }: SelectProps) {
  const [open, setOpen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const selected = options.find((o) => o.value === value);

  return (
    <div ref={wrapperRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        className="w-full flex items-center justify-between bg-transparent border rounded-sm px-3 py-2 text-[13px] mono outline-none transition-shadow"
        style={{
          borderColor: open ? "var(--accent)" : "var(--panel-line)",
          color: "var(--text)",
          boxShadow: open ? "0 0 0 1px var(--accent), 0 0 14px -4px rgba(0,232,255,0.6)" : "none",
        }}
      >
        <span>{selected ? selected.label : placeholder}</span>
        <svg
          width="12" height="12" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"
          style={{
            color: "var(--muted)",
            transform: open ? "rotate(180deg)" : "rotate(0deg)",
            transition: "transform 0.15s ease",
            flexShrink: 0,
          }}
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      {open && (
        <div
          className="absolute z-20 mt-1 w-full rounded-sm border overflow-hidden"
          style={{
            borderColor: "var(--panel-line)",
            background: "var(--panel-bg)",
            boxShadow: "0 8px 24px -8px rgba(0,0,0,0.6)",
          }}
        >
          {options.map((opt) => {
            const isSelected = opt.value === value;
            return (
              <div
                key={opt.value}
                onClick={() => {
                  onChange(opt.value);
                  setOpen(false);
                }}
                className="px-3 py-2 text-[13px] mono cursor-pointer transition-colors"
                style={{
                  color: isSelected ? "var(--accent)" : "var(--text)",
                  background: isSelected ? "rgba(0,232,255,0.08)" : "transparent",
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = "rgba(0,232,255,0.14)";
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = isSelected ? "rgba(0,232,255,0.08)" : "transparent";
                }}
              >
                {opt.label}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
