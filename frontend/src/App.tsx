import { Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { Dashboard } from "./pages/Dashboard";
import { Demos } from "./pages/Demos";
import { LeadRoom } from "./pages/LeadRoom";
import { Leads } from "./pages/Leads";
import { Products } from "./pages/Products";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/leads" element={<Leads />} />
        <Route path="/leads/:id" element={<LeadRoom />} />
        <Route path="/demos" element={<Demos />} />
        <Route path="/products" element={<Products />} />
      </Routes>
    </Layout>
  );
}
