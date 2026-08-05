import React from "react";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary";
  children: React.ReactNode;
}

export default function Button({
  variant = "primary",
  children,
  disabled,
  ...props
}: ButtonProps) {
  const baseClasses = "px-4 py-2 rounded-md font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2";
  const variantClasses =
    variant === "primary"
      ? "bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500"
      : "bg-gray-200 text-gray-800 hover:bg-gray-300 focus:ring-gray-500";

  return (
    <button
      disabled={disabled}
      className={`${baseClasses} ${variantClasses} disabled:opacity-50`}
      {...props}
    >
      {children}
    </button>
  );
}
