import type { Route } from "./+types/index";
import Login, { meta as loginMeta } from "./login";

export const meta = (args: Route.MetaArgs) => loginMeta(args);

export default function Index() {
  return <Login />;
}
