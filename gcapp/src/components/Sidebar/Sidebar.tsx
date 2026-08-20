import React, { useState } from "react";
import "./Sidebar.css";
import gc from "../../assets/gc.svg";
import SidebarItem from "./SidebarItem.tsx";

export interface SideBarItemInfo {
  target: string;
  class_str: string;
  title: string;
}

const Sidebar: React.FC = () => {
  const [isCollapsed, setIsCollapsed] = useState(false);

  const sb_items: SideBarItemInfo[] = [
    { target: "/", class_str: "bi bi-clouds fs-4 me-2", title: "Home" },
    { target: "/data", class_str: "bi bi-database fs-4 me-2", title: "Data" },
    {
      target: "/configuration",
      class_str: "bi bi-sliders2 fs-4 me-2",
      title: "Configuration",
    },
    {
      target: "/results",
      class_str: "bi bi-clipboard-data fs-4 me-2",
      title: "Results",
    },
  ];

  const toggleSidebar = () => {
    setIsCollapsed(!isCollapsed);
  };

  return (
    <div className="d-flex">
      <nav
        // Nav style
        className={`sidebar bg-dark shadow text-white ${isCollapsed ? "collapsed" : ""}`}
      >
        {/* hamburger */}
        <div className="d-flex justify-content-between align-items-center">
          <button
            className="btn btn-outline-light rounded-circle btn-sm border-0"
            onClick={toggleSidebar}
          >
            <i className="bi bi-list fs-3"></i>
          </button>
          <div className="logo-container flex-grow-1 text-start">
            <img src={gc} alt="Logo" className="logo" />
          </div>
        </div>

        <hr />

        {/* list */}
        <ul className="nav nav-pills flex-column mb-auto">
          {sb_items?.map((item) => (
            <SidebarItem
              target={item.target}
              class_str={item.class_str}
              title={item.title}
              key={item.title}
            />
          ))}
        </ul>
      </nav>
    </div>
  );
};

export default Sidebar;
