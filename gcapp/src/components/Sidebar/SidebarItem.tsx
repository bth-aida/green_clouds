import { NavLink } from "react-router-dom";
import type { SideBarItemInfo } from "./Sidebar";

const SidebarItem = ({ target, class_str, title }: SideBarItemInfo) => {
  return (
    <li className="nav-item mb-2">
      <NavLink
        to={target}
        className={({ isActive }) =>
          `nav-link text-white ${isActive ? "active" : ""}`
        }
      >
        <i className={class_str}></i>
        <span>{title}</span>
      </NavLink>
    </li>
  );
};

export default SidebarItem;
