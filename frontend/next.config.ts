/** @type {import('next').NextConfig} */
const nextConfig = {
  typedRoutes: true,
  turbopack: {
    root: __dirname, // fuerza /frontend como raíz
  },
};
export default nextConfig;