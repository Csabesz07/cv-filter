import { type RouteConfig, index, route } from "@react-router/dev/routes";

export default [
  index("routes/index.tsx"),
  route("login", "routes/login.tsx"),
  route("register", "routes/register.tsx"),
  route("home", "routes/home.tsx"),
  route("user", "routes/user.tsx"),
] satisfies RouteConfig;
