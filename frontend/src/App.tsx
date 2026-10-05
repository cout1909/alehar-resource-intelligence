import { BrowserRouter, Link, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Lenders from "./pages/Lenders";
import LenderDetail from "./pages/LenderDetail";
import Reviews from "./pages/Reviews";
import History from "./pages/History";
import System from "./pages/System";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="lenders" element={<Lenders />} />
          <Route path="lenders/:id" element={<LenderDetail />} />
          <Route path="reviews" element={<Reviews />} />
          <Route path="history" element={<History />} />
          <Route path="system" element={<System />} />
          <Route
            path="*"
            element={
              <div className="state">
                <h1>Page not found</h1>
                <Link to="/">Return to dashboard</Link>
              </div>
            }
          />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
