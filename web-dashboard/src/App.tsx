import { RouterProvider } from "react-router-dom";
import router from "./router";
import Layout from "./layout";

export default function App() {
  return (
    <Layout>
      <RouterProvider router={router} />
    </Layout>
  );
}
