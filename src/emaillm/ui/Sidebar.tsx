import React from "react";
import { Link } from "react-router-dom";

export default function Sidebar() {
  return (
    <nav style={{ width: 180, padding: 16, background: "#f5f5f5", height: "100vh" }}>
      <ul style={{ listStyle: "none", padding: 0 }}>
        <li><Link to="/admin/plans">Plans</Link></li>
      </ul>
    </nav>
  );
}
