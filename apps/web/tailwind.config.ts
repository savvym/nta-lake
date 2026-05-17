import type { Config } from "tailwindcss";

// design.md §11.7 第 6 坑：content 必须含所有用到 className 的目录。
const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: { extend: {} },
  plugins: [],
};

export default config;
