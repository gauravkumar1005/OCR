const VARIANTS = {
  full: "w-full max-w-[1600px] mx-auto px-4 sm:px-5 md:px-6 xl:px-8 py-5 md:py-7",
  wide: "w-full max-w-[1400px] mx-auto px-4 sm:px-5 md:px-6 xl:px-8 py-5 md:py-7",
  narrow: "w-full max-w-[1100px] mx-auto px-4 sm:px-5 md:px-6 xl:px-8 py-5 md:py-7",
};

export default function PageContainer({ variant = "full", className = "", children }) {
  return <div className={`${VARIANTS[variant]} ${className}`.trim()}>{children}</div>;
}
