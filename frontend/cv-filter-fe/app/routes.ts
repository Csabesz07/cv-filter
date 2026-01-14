import { type RouteConfig, index, route } from "@react-router/dev/routes";

export default [
  index("routes/index.tsx"),
  route("login", "routes/login.tsx"),
  route("register", "routes/register.tsx"),
  route("home", "routes/home.tsx"),
  route("user", "routes/user.tsx"),
  route("organization", "routes/organization.tsx"),
  route("candidates", "routes/candidates.tsx"),
  route("files", "routes/files.tsx"),
  route("document-extraction", "routes/document-extraction.tsx"),
] satisfies RouteConfig;
