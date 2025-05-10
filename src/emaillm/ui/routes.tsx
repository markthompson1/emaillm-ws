import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Sidebar from "./Sidebar";
import PlansPanel from "./admin/PlansPanel";

export default function AppRoutes() {
  return (
    <Router>
      <div style={{ display: "flex" }}>
        <Sidebar />
        <div style={{ flex: 1, padding: 24 }}>
          <Routes>
            <Route path="/admin/plans" element={<PlansPanel />} />
            {/* Add more admin routes here */}
          </Routes>
        </div>
      </div>
    </Router>
  );
}
