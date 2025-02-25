import ReactDOM from "react-dom/client";
import App from "./App";
import ContextPackage from "./contextPackage";

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <ContextPackage>
    <App />
  </ContextPackage>
);
