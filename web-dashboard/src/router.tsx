import {
  createBrowserRouter,
  LoaderFunction,
  ActionFunction,
} from "react-router-dom";
import Layout from "./layout";

interface IRoute {
  path: string;
  Element: Element;
  loader?: LoaderFunction;
  action?: ActionFunction;
  ErrorBoundary?: Element;
}

const pages = import.meta.glob("/src/pages/**/[a-z[]*.tsx", { eager: true });

const routes: IRoute[] = [];
for (const path of Object.keys(pages)) {
  const fileName = path
    .replace(/\/src\/pages|index|\.tsx$/g, "")
    .replace(/\[\.{3}.+\]/, "*")
    .replace(/\[(.+)\]/, ":$1");

  routes.push({
    path: fileName === "index" ? "/" : `${fileName.toLowerCase()}`,
    // @ts-expect-error unknown type due to routing method
    Element: pages[path].default,

    // @ts-expect-error unknown type due to routing method
    loader: pages[path]?.loader as unknown as LoaderFunction | undefined,

    // @ts-expect-error unknown type due to routing method
    action: pages[path]?.action as unknown as ActionFunction | undefined,

    // @ts-expect-error unknown type due to routing method
    ErrorBoundary: pages[path]?.ErrorBoundary as unknown as JSX.Element,
  });
}

const router = createBrowserRouter(
  routes.map(({ Element, ErrorBoundary, ...rest }) => ({
    ...rest,

    // @ts-expect-error unknown type due to routing method
    element: (
      <Layout>
        <Element />
      </Layout>
    ),

    // @ts-expect-error unknown type due to routing method
    ...(ErrorBoundary && { errorElement: <ErrorBoundary /> }),
  }))
);

export default router;
